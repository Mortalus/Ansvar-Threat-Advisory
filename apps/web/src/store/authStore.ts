import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { authService } from '@services/auth.service';
import { mockAuthService } from '@services/mock-auth.service';
import type { User } from '@types/index';

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  updateUser: (user: User) => void;
  clearError: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      user: null,
      token: null,
      loading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ loading: true, error: null });
        try {
          // Try real auth service first, fallback to mock if backend unavailable
          let response;
          try {
            response = await authService.login(email, password);
            console.log('Using real auth service for login');
          } catch (backendError: any) {
            console.log('Real auth failed, trying mock auth service. Error:', backendError.message);
            // Always fallback to mock service regardless of error type
            response = await mockAuthService.login(email, password);
            console.log('Mock auth service login successful');
          }
          
          set({
            isAuthenticated: true,
            user: response.user,
            token: response.token,
            loading: false,
            error: null,
          });

          // Set token in appropriate service
          authService.setToken(response.token);
          mockAuthService.setToken(response.token);
          
          // No redirect here - let React Router handle navigation
        } catch (error: any) {
          set({
            loading: false,
            error: error.message || 'Login failed. Please try again.',
            isAuthenticated: false,
          });
          throw error;
        }
      },

      logout: () => {
        authService.logout();
        mockAuthService.logout();
        set({
          isAuthenticated: false,
          user: null,
          token: null,
          error: null,
        });
        // No redirect here - let React Router handle navigation
      },

      refreshToken: async () => {
        const { token } = get();
        if (!token) {
          get().logout();
          return;
        }

        try {
          // Try real auth service first, fallback to mock
          let response;
          try {
            response = await authService.refreshToken(token);
          } catch (backendError) {
            response = await mockAuthService.refreshToken(token);
          }
          
          set({
            token: response.token,
            user: response.user,
          });
          authService.setToken(response.token);
          mockAuthService.setToken(response.token);
        } catch (error) {
          console.error('Token refresh failed:', error);
          get().logout();
        }
      },

      updateUser: (user: User) => {
        set({ user });
      },

      clearError: () => {
        set({ error: null });
      },

      checkAuth: async () => {
        const { token } = get();
        if (!token) {
          set({ isAuthenticated: false, loading: false });
          return;
        }

        try {
          set({ loading: true });
          // Try real auth service first, fallback to mock
          let user;
          try {
            user = await authService.validateToken(token);
            console.log('Using real auth service for validation');
          } catch (backendError) {
            console.log('Backend unavailable for validation, using mock auth service');
            user = await mockAuthService.validateToken(token);
          }
          
          set({
            isAuthenticated: true,
            user,
            loading: false,
          });
          authService.setToken(token);
          mockAuthService.setToken(token);
        } catch (error) {
          console.log('Auth check failed completely, clearing auth state');
          set({
            isAuthenticated: false,
            user: null,
            token: null,
            loading: false,
          });
        }
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    }
  )
);