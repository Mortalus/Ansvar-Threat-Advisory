import { apiClient } from './api.client';
import type { User } from '@types/index';
import { z } from 'zod';

// Validation schemas
const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

const userSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  name: z.string(),
  role: z.string(),
  permissions: z.array(z.string()),
  avatar_url: z.string().optional(),
  last_login: z.string().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});

interface LoginResponse {
  user: User;
  token: string;
  expires_at: string;
}

interface RefreshResponse {
  user: User;
  token: string;
  expires_at: string;
}

class AuthService {
  private token: string | null = null;
  private refreshTimer: NodeJS.Timeout | null = null;

  /**
   * Login with email and password
   * Implements defensive validation and error handling
   */
  async login(email: string, password: string): Promise<LoginResponse> {
    try {
      // Validate input
      const validated = loginSchema.parse({ email, password });

      // Make API request with timeout and retry
      const response = await apiClient.post<LoginResponse>('/auth/login', {
        email: validated.email,
        password: validated.password,
      });

      // Validate response
      const validatedUser = userSchema.parse(response.user);
      
      // Set up auto-refresh
      this.scheduleTokenRefresh(response.expires_at);

      return {
        ...response,
        user: validatedUser,
      };
    } catch (error: any) {
      if (error instanceof z.ZodError) {
        throw new Error(error.errors[0].message);
      }
      
      // Handle specific error cases
      if (error.response?.status === 401) {
        throw new Error('Invalid email or password');
      } else if (error.response?.status === 429) {
        throw new Error('Too many login attempts. Please try again later.');
      } else if (error.code === 'ECONNABORTED') {
        throw new Error('Login request timed out. Please check your connection.');
      } else if (!navigator.onLine) {
        throw new Error('No internet connection. Please check your network.');
      }
      
      throw new Error(error.message || 'Login failed. Please try again.');
    }
  }

  /**
   * Logout and clear authentication
   */
  logout(): void {
    this.clearToken();
    this.clearRefreshTimer();
    
    // Clear all auth-related storage
    localStorage.removeItem('auth-storage');
    sessionStorage.clear();
    
    // Clear API client headers
    apiClient.clearAuthHeader();
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(currentToken: string): Promise<RefreshResponse> {
    try {
      const response = await apiClient.post<RefreshResponse>('/auth/refresh', {
        refresh_token: currentToken,
      });

      // Validate response
      const validatedUser = userSchema.parse(response.user);
      
      // Reschedule refresh
      this.scheduleTokenRefresh(response.expires_at);

      return {
        ...response,
        user: validatedUser,
      };
    } catch (error: any) {
      console.error('Token refresh failed:', error);
      throw error;
    }
  }

  /**
   * Validate current token
   */
  async validateToken(token: string): Promise<User> {
    try {
      this.setToken(token);
      const response = await apiClient.get<{ user: User }>('/auth/me');
      
      // Validate response
      const validatedUser = userSchema.parse(response.user);
      return validatedUser;
    } catch (error) {
      this.clearToken();
      throw error;
    }
  }

  /**
   * Set authentication token
   */
  setToken(token: string): void {
    this.token = token;
    apiClient.setAuthToken(token);
  }

  /**
   * Clear authentication token
   */
  clearToken(): void {
    this.token = null;
    apiClient.clearAuthHeader();
  }

  /**
   * Get current token
   */
  getToken(): string | null {
    return this.token;
  }

  /**
   * Schedule automatic token refresh
   */
  private scheduleTokenRefresh(expiresAt: string): void {
    this.clearRefreshTimer();

    const expiryTime = new Date(expiresAt).getTime();
    const currentTime = Date.now();
    const timeUntilExpiry = expiryTime - currentTime;

    // Refresh 5 minutes before expiry
    const refreshTime = Math.max(0, timeUntilExpiry - 5 * 60 * 1000);

    if (refreshTime > 0) {
      this.refreshTimer = setTimeout(async () => {
        try {
          if (this.token) {
            await this.refreshToken(this.token);
          }
        } catch (error) {
          console.error('Auto refresh failed:', error);
          // Let the store handle logout
        }
      }, refreshTime);
    }
  }

  /**
   * Clear refresh timer
   */
  private clearRefreshTimer(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  /**
   * Check if user has specific permission
   */
  hasPermission(user: User | null, permission: string): boolean {
    if (!user) return false;
    if (user.role === 'admin') return true;
    return user.permissions?.includes(permission) ?? false;
  }

  /**
   * Check if user has specific role
   */
  hasRole(user: User | null, role: string): boolean {
    if (!user) return false;
    return user.role === role || user.role === 'admin';
  }
}

export const authService = new AuthService();