import { errorHandler } from './errorHandler';

export interface ApiResponse<T = any> {
  data?: T;
  error?: any;
  success: boolean;
}

export interface RequestConfig extends RequestInit {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

class ApiClient {
  private baseURL: string;
  private defaultTimeout = 10000;
  private defaultRetries = 3;
  private defaultRetryDelay = 1000;

  constructor(baseURL: string = '/api') {
    this.baseURL = baseURL;
  }

  private async makeRequest<T>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const {
      timeout = this.defaultTimeout,
      retries = this.defaultRetries,
      retryDelay = this.defaultRetryDelay,
      ...fetchConfig
    } = config;

    const url = `${this.baseURL}${endpoint}`;
    let lastError: any;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(url, {
          ...fetchConfig,
          signal: controller.signal,
          headers: {
            'Content-Type': 'application/json',
            ...fetchConfig.headers,
          },
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorData = await this.parseErrorResponse(response);
          const appError = errorHandler.handleAPIError(response, errorData);
          
          return {
            success: false,
            error: appError,
          };
        }

        const data = await response.json();
        return {
          success: true,
          data,
        };

      } catch (error: any) {
        lastError = error;

        // Don't retry on certain errors
        if (error.name === 'AbortError') {
          const appError = errorHandler.handleNetworkError(
            new Error('Request timeout'),
            { url, attempt: attempt + 1 }
          );
          return {
            success: false,
            error: appError,
          };
        }

        // Don't retry if offline
        if (!navigator.onLine) {
          const appError = errorHandler.handleError(
            new Error('Network unavailable'),
            { url, offline: true }
          );
          return {
            success: false,
            error: appError,
          };
        }

        // Wait before retry (except on last attempt)
        if (attempt < retries) {
          await this.delay(retryDelay * Math.pow(2, attempt)); // Exponential backoff
        }
      }
    }

    // All retries failed
    const appError = errorHandler.handleNetworkError(lastError, {
      url,
      attempts: retries + 1,
    });

    return {
      success: false,
      error: appError,
    };
  }

  private async parseErrorResponse(response: Response): Promise<any> {
    try {
      return await response.json();
    } catch {
      return {
        message: `HTTP ${response.status}: ${response.statusText}`,
        status: response.status,
      };
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // HTTP Methods
  async get<T>(endpoint: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, {
      method: 'GET',
      ...config,
    });
  }

  async post<T>(
    endpoint: string,
    data?: any,
    config?: RequestConfig
  ): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      ...config,
    });
  }

  async put<T>(
    endpoint: string,
    data?: any,
    config?: RequestConfig
  ): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
      ...config,
    });
  }

  async patch<T>(
    endpoint: string,
    data?: any,
    config?: RequestConfig
  ): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
      ...config,
    });
  }

  async delete<T>(endpoint: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, {
      method: 'DELETE',
      ...config,
    });
  }

  // File upload with progress
  async uploadFile<T>(
    endpoint: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<T>> {
    return new Promise((resolve) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();
      formData.append('file', file);

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = (event.loaded / event.total) * 100;
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', async () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            resolve({ success: true, data });
          } catch {
            resolve({ success: true, data: xhr.responseText });
          }
        } else {
          const appError = errorHandler.handleAPIError(
            { status: xhr.status, url: endpoint } as Response,
            { message: xhr.statusText }
          );
          resolve({ success: false, error: appError });
        }
      });

      xhr.addEventListener('error', () => {
        const appError = errorHandler.handleNetworkError(
          new Error('Upload failed'),
          { endpoint, fileName: file.name }
        );
        resolve({ success: false, error: appError });
      });

      xhr.addEventListener('timeout', () => {
        const appError = errorHandler.handleNetworkError(
          new Error('Upload timeout'),
          { endpoint, fileName: file.name }
        );
        resolve({ success: false, error: appError });
      });

      xhr.open('POST', `${this.baseURL}${endpoint}`);
      xhr.timeout = 30000; // 30 second timeout for uploads
      xhr.send(formData);
    });
  }
}

export const apiClient = new ApiClient();