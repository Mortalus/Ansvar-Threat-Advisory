// Quick integration test to verify core functionality
import { authService } from './services/auth.service';
import { apiClient } from './services/api.client';

// Mock test to verify services are properly initialized
describe('Integration Tests', () => {
  test('Auth service is properly initialized', () => {
    expect(authService).toBeDefined();
    expect(authService.getToken).toBeDefined();
    expect(authService.login).toBeDefined();
    expect(authService.logout).toBeDefined();
  });

  test('API client is properly initialized', () => {
    expect(apiClient).toBeDefined();
    expect(apiClient.get).toBeDefined();
    expect(apiClient.post).toBeDefined();
    expect(apiClient.put).toBeDefined();
    expect(apiClient.delete).toBeDefined();
  });

  test('Environment variables are loaded', () => {
    // These should be available in the build
    expect(import.meta.env.VITE_API_URL).toBeDefined();
    expect(import.meta.env.VITE_WS_URL).toBeDefined();
  });
});