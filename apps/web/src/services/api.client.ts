import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { toast } from 'react-hot-toast';

// Configuration
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000');
const RETRY_ATTEMPTS = parseInt(import.meta.env.VITE_RETRY_ATTEMPTS || '3');
const CACHE_TTL = parseInt(import.meta.env.VITE_CACHE_TTL || '300000');

// Error types
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Cache implementation
class CacheManager {
  private cache = new Map<string, { data: any; expiry: number }>();

  set(key: string, data: any, ttl: number = CACHE_TTL): void {
    this.cache.set(key, {
      data,
      expiry: Date.now() + ttl,
    });
  }

  get(key: string): any | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    if (Date.now() > entry.expiry) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  clear(): void {
    this.cache.clear();
  }

  delete(pattern: string): void {
    const keys = Array.from(this.cache.keys());
    keys.forEach(key => {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    });
  }
}

// Request queue for offline support
class RequestQueue {
  private queue: Array<{
    config: AxiosRequestConfig;
    resolve: (value: any) => void;
    reject: (error: any) => void;
  }> = [];

  add(config: AxiosRequestConfig): Promise<any> {
    return new Promise((resolve, reject) => {
      this.queue.push({ config, resolve, reject });
      this.saveToStorage();
    });
  }

  async processQueue(client: AxiosInstance): Promise<void> {
    while (this.queue.length > 0) {
      const request = this.queue.shift();
      if (request) {
        try {
          const response = await client.request(request.config);
          request.resolve(response.data);
        } catch (error) {
          request.reject(error);
        }
      }
    }
    this.saveToStorage();
  }

  private saveToStorage(): void {
    try {
      localStorage.setItem('request-queue', JSON.stringify(this.queue.map(r => r.config)));
    } catch (error) {
      console.error('Failed to save request queue:', error);
    }
  }

  loadFromStorage(): void {
    try {
      const stored = localStorage.getItem('request-queue');
      if (stored) {
        const configs = JSON.parse(stored);
        // Note: We can't restore promises, so these will need to be retried
        console.log(`Loaded ${configs.length} queued requests`);
      }
    } catch (error) {
      console.error('Failed to load request queue:', error);
    }
  }
}

class ApiClient {
  private client: AxiosInstance;
  private cache: CacheManager;
  private requestQueue: RequestQueue;
  private isOnline: boolean = navigator.onLine;

  constructor() {
    this.cache = new CacheManager();
    this.requestQueue = new RequestQueue();

    // Create axios instance
    this.client = axios.create({
      baseURL: API_URL,
      timeout: TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Setup interceptors
    this.setupInterceptors();

    // Setup online/offline listeners
    this.setupNetworkListeners();

    // Load queued requests
    this.requestQueue.loadFromStorage();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add timestamp for cache busting if needed
        if (config.method === 'get') {
          config.params = {
            ...config.params,
            _t: Date.now(),
          };
        }

        // Log request in development
        if (import.meta.env.VITE_ENABLE_DEBUG === 'true') {
          console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data);
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        // Log response in development
        if (import.meta.env.VITE_ENABLE_DEBUG === 'true') {
          console.log(`[API] Response:`, response.data);
        }

        return response;
      },
      async (error: AxiosError) => {
        const originalRequest: any = error.config;

        // Handle 401 - Unauthorized
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            // Try to refresh token
            const authStore = (await import('@store/authStore')).useAuthStore.getState();
            await authStore.refreshToken();
            
            // Retry original request
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed, logout user
            const authStore = (await import('@store/authStore')).useAuthStore.getState();
            authStore.logout();
            return Promise.reject(error);
          }
        }

        // Handle other errors
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private setupNetworkListeners(): void {
    window.addEventListener('online', () => {
      this.isOnline = true;
      toast.success('Connection restored');
      // Process queued requests
      this.requestQueue.processQueue(this.client);
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      toast.error('Connection lost. Working offline.');
    });
  }

  private handleError(error: AxiosError): ApiError {
    if (error.response) {
      // Server responded with error
      const status = error.response.status;
      const data: any = error.response.data;
      const message = data?.message || data?.detail || 'An error occurred';

      switch (status) {
        case 400:
          return new ApiError('Bad request. Please check your input.', status, 'BAD_REQUEST', data);
        case 403:
          return new ApiError('You do not have permission to perform this action.', status, 'FORBIDDEN', data);
        case 404:
          return new ApiError('The requested resource was not found.', status, 'NOT_FOUND', data);
        case 429:
          return new ApiError('Too many requests. Please try again later.', status, 'RATE_LIMIT', data);
        case 500:
          return new ApiError('Server error. Please try again later.', status, 'SERVER_ERROR', data);
        default:
          return new ApiError(message, status, 'UNKNOWN', data);
      }
    } else if (error.request) {
      // Request made but no response
      if (!this.isOnline) {
        return new ApiError('No internet connection', undefined, 'OFFLINE');
      }
      return new ApiError('Network error. Please check your connection.', undefined, 'NETWORK_ERROR');
    } else {
      // Something else happened
      return new ApiError(error.message || 'An unexpected error occurred', undefined, 'CLIENT_ERROR');
    }
  }

  private async retryRequest<T>(
    fn: () => Promise<AxiosResponse<T>>,
    retries: number = RETRY_ATTEMPTS
  ): Promise<AxiosResponse<T>> {
    try {
      return await fn();
    } catch (error) {
      if (retries > 0 && this.shouldRetry(error)) {
        // Exponential backoff
        const delay = Math.pow(2, RETRY_ATTEMPTS - retries) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
        
        return this.retryRequest(fn, retries - 1);
      }
      throw error;
    }
  }

  private shouldRetry(error: any): boolean {
    // Retry on network errors or 5xx server errors
    if (!error.response) return true;
    if (error.response.status >= 500) return true;
    if (error.response.status === 429) return true;
    return false;
  }

  // Public methods

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    // Check cache first
    const cacheKey = `GET:${url}:${JSON.stringify(config?.params || {})}`;
    const cached = this.cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    // Make request with retry
    const response = await this.retryRequest(() => 
      this.client.get<T>(url, config)
    );

    // Cache successful GET requests
    this.cache.set(cacheKey, response.data);

    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    // Clear relevant cache entries
    this.cache.delete(url);

    // Check if offline
    if (!this.isOnline && this.canQueueRequest(url)) {
      return this.requestQueue.add({ ...config, method: 'post', url, data });
    }

    const response = await this.retryRequest(() => 
      this.client.post<T>(url, data, config)
    );

    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    // Clear relevant cache entries
    this.cache.delete(url);

    // Check if offline
    if (!this.isOnline && this.canQueueRequest(url)) {
      return this.requestQueue.add({ ...config, method: 'put', url, data });
    }

    const response = await this.retryRequest(() => 
      this.client.put<T>(url, data, config)
    );

    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    // Clear relevant cache entries
    this.cache.delete(url);

    // Check if offline
    if (!this.isOnline && this.canQueueRequest(url)) {
      return this.requestQueue.add({ ...config, method: 'delete', url });
    }

    const response = await this.retryRequest(() => 
      this.client.delete<T>(url, config)
    );

    return response.data;
  }

  async upload(url: string, file: File, onProgress?: (progress: number) => void): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  }

  private canQueueRequest(url: string): boolean {
    // Define which endpoints can be queued for offline mode
    const queuablePatterns = [
      '/api/projects',
      '/api/workflows',
      '/api/agents',
    ];

    return queuablePatterns.some(pattern => url.includes(pattern));
  }

  setAuthToken(token: string): void {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  clearAuthHeader(): void {
    delete this.client.defaults.headers.common['Authorization'];
  }

  clearCache(): void {
    this.cache.clear();
  }
}

// Export singleton instance
export const apiClient = new ApiClient();