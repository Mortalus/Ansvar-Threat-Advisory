import type { User } from '../types';

// Mock implementation that works without backend
export class MockAuthService {
  private token: string | null = null;

  async login(email: string, password: string): Promise<{ user: User; token: string; expires_at: string }> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Demo credentials
    const demoUsers: Record<string, User> = {
      'admin@company.com': {
        id: '1',
        email: 'admin@company.com',
        name: 'System Administrator',
        avatar: '',
        role: 'admin',
        permissions: ['read', 'write', 'delete', 'manage_users', 'view_logs', 'manage_settings'],
        lastLogin: new Date().toISOString(),
        createdAt: '2024-01-01T00:00:00Z'
      },
      'user@company.com': {
        id: '2',
        email: 'user@company.com',
        name: 'Regular User',
        avatar: '',
        role: 'user',
        permissions: ['read', 'write', 'execute_workflows', 'manage_own_content'],
        lastLogin: new Date().toISOString(),
        createdAt: '2024-01-01T00:00:00Z'
      },
      'viewer@company.com': {
        id: '3',
        email: 'viewer@company.com',
        name: 'Viewer User',
        avatar: '',
        role: 'viewer',
        permissions: ['read', 'view_workflows', 'view_executions'],
        lastLogin: new Date().toISOString(),
        createdAt: '2024-01-01T00:00:00Z'
      }
    };

    const demoPasswords: Record<string, string> = {
      'admin@company.com': 'admin123',
      'user@company.com': 'user1234', 
      'viewer@company.com': 'viewer123'
    };

    // Check credentials
    if (!demoUsers[email] || demoPasswords[email] !== password) {
      throw new Error('Invalid email or password');
    }

    const user = demoUsers[email];
    const token = `mock-token-${user.id}-${Date.now()}`;
    const expires_at = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();

    return { user, token, expires_at };
  }

  async refreshToken(currentToken: string): Promise<{ user: User; token: string; expires_at: string }> {
    // For demo, just return the same user
    const user: User = {
      id: '1',
      email: 'admin@company.com',
      name: 'System Administrator',
      avatar: '',
      role: 'admin',
      permissions: ['read', 'write', 'delete', 'manage_users', 'view_logs', 'manage_settings'],
      lastLogin: new Date().toISOString(),
      createdAt: '2024-01-01T00:00:00Z'
    };

    const token = `mock-token-refreshed-${Date.now()}`;
    const expires_at = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();

    return { user, token, expires_at };
  }

  async validateToken(token: string): Promise<User> {
    // For demo, always return admin user
    return {
      id: '1',
      email: 'admin@company.com',
      name: 'System Administrator',
      avatar: '',
      role: 'admin',
      permissions: ['read', 'write', 'delete', 'manage_users', 'view_logs', 'manage_settings'],
      lastLogin: new Date().toISOString(),
      createdAt: '2024-01-01T00:00:00Z'
    };
  }

  setToken(token: string): void {
    this.token = token;
    console.log('Mock: Token set:', token);
  }

  getToken(): string | null {
    return this.token;
  }

  logout(): void {
    this.token = null;
    console.log('Mock: Logged out');
  }

  hasPermission(user: User | null, permission: string): boolean {
    if (!user) return false;
    if (user.role === 'admin') return true;
    return user.permissions?.includes(permission) ?? false;
  }

  hasRole(user: User | null, role: string): boolean {
    if (!user) return false;
    return user.role === role || user.role === 'admin';
  }
}

export const mockAuthService = new MockAuthService();