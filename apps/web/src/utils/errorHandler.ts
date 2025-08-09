// Error types and interfaces
export interface AppError {
  id: string;
  type: 'network' | 'api' | 'validation' | 'auth' | 'system' | 'offline';
  message: string;
  userMessage: string;
  code?: string | number;
  details?: any;
  timestamp: string;
  stack?: string;
  context?: Record<string, any>;
}

export interface ErrorLogEntry extends AppError {
  userId?: string;
  sessionId: string;
  userAgent: string;
  url: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

// Error classes
export class NetworkError extends Error {
  constructor(
    message: string,
    public code?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'NetworkError';
  }
}

export class APIError extends Error {
  constructor(
    message: string,
    public code?: string | number,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export class ValidationError extends Error {
  constructor(
    message: string,
    public field?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

export class AuthError extends Error {
  constructor(
    message: string,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'AuthError';
  }
}

// Error handler class
export class ErrorHandler {
  private static instance: ErrorHandler;
  private errorQueue: ErrorLogEntry[] = [];
  private isOnline = navigator.onLine;
  private sessionId = this.generateSessionId();

  private constructor() {
    this.setupGlobalErrorHandlers();
    this.setupOnlineStatusHandlers();
  }

  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupGlobalErrorHandlers(): void {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      console.error('Unhandled promise rejection:', event.reason);
      this.handleError(event.reason, {
        type: 'unhandled_promise',
        source: 'global'
      });
    });

    // Handle JavaScript errors
    window.addEventListener('error', (event) => {
      console.error('Global error:', event.error);
      this.handleError(event.error, {
        type: 'javascript_error',
        source: 'global',
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      });
    });
  }

  private setupOnlineStatusHandlers(): void {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.flushErrorQueue();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }

  handleError(error: any, context?: Record<string, any>): AppError {
    const appError = this.createAppError(error, context);
    this.logError(appError);
    return appError;
  }

  private createAppError(error: any, context?: Record<string, any>): AppError {
    const timestamp = new Date().toISOString();
    const id = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Handle different error types
    if (error instanceof NetworkError) {
      return {
        id,
        type: 'network',
        message: error.message,
        userMessage: this.getNetworkErrorMessage(error.code),
        code: error.code,
        details: error.details,
        timestamp,
        stack: error.stack,
        context
      };
    }

    if (error instanceof APIError) {
      return {
        id,
        type: 'api',
        message: error.message,
        userMessage: this.getAPIErrorMessage(error.code),
        code: error.code,
        details: error.details,
        timestamp,
        stack: error.stack,
        context
      };
    }

    if (error instanceof ValidationError) {
      return {
        id,
        type: 'validation',
        message: error.message,
        userMessage: this.getValidationErrorMessage(error.field),
        details: error.details,
        timestamp,
        stack: error.stack,
        context
      };
    }

    if (error instanceof AuthError) {
      return {
        id,
        type: 'auth',
        message: error.message,
        userMessage: this.getAuthErrorMessage(error.code),
        code: error.code,
        details: error.details,
        timestamp,
        stack: error.stack,
        context
      };
    }

    // Handle offline errors
    if (!this.isOnline) {
      return {
        id,
        type: 'offline',
        message: 'Application is offline',
        userMessage: 'You appear to be offline. Some features may not be available.',
        timestamp,
        context
      };
    }

    // Generic error handling
    return {
      id,
      type: 'system',
      message: error?.message || 'Unknown error occurred',
      userMessage: 'Something went wrong. Please try again.',
      timestamp,
      stack: error?.stack,
      context
    };
  }

  private getNetworkErrorMessage(code?: number): string {
    switch (code) {
      case 0:
        return 'Unable to connect. Please check your internet connection.';
      case 408:
        return 'Request timed out. Please try again.';
      case 429:
        return 'Too many requests. Please wait a moment and try again.';
      case 500:
        return 'Server error. Please try again later.';
      case 502:
      case 503:
      case 504:
        return 'Service temporarily unavailable. Please try again later.';
      default:
        return 'Network error occurred. Please check your connection and try again.';
    }
  }

  private getAPIErrorMessage(code?: string | number): string {
    switch (code) {
      case 400:
        return 'Invalid request. Please check your input and try again.';
      case 401:
        return 'Authentication required. Please log in again.';
      case 403:
        return 'Access denied. You don\'t have permission for this action.';
      case 404:
        return 'The requested resource was not found.';
      case 409:
        return 'Conflict detected. The resource may have been modified.';
      case 422:
        return 'Invalid data provided. Please check your input.';
      default:
        return 'An error occurred while processing your request.';
    }
  }

  private getValidationErrorMessage(field?: string): string {
    if (field) {
      return `Please check the ${field} field and try again.`;
    }
    return 'Please check your input and try again.';
  }

  private getAuthErrorMessage(code?: string): string {
    switch (code) {
      case 'token_expired':
        return 'Your session has expired. Please log in again.';
      case 'invalid_credentials':
        return 'Invalid username or password.';
      case 'account_locked':
        return 'Your account has been temporarily locked.';
      default:
        return 'Authentication error. Please try logging in again.';
    }
  }

  private logError(error: AppError): void {
    const logEntry: ErrorLogEntry = {
      ...error,
      sessionId: this.sessionId,
      userAgent: navigator.userAgent,
      url: window.location.href,
      severity: this.getSeverity(error)
    };

    // Store locally first
    this.storeErrorLocally(logEntry);

    // Try to send to server if online
    if (this.isOnline) {
      this.sendErrorToServer(logEntry);
    } else {
      this.errorQueue.push(logEntry);
    }
  }

  private getSeverity(error: AppError): 'low' | 'medium' | 'high' | 'critical' {
    switch (error.type) {
      case 'validation':
        return 'low';
      case 'network':
      case 'api':
        return 'medium';
      case 'auth':
        return 'high';
      case 'system':
        return 'critical';
      default:
        return 'medium';
    }
  }

  private storeErrorLocally(error: ErrorLogEntry): void {
    try {
      const errors = this.getStoredErrors();
      errors.push(error);
      
      // Keep only last 100 errors
      const recentErrors = errors.slice(-100);
      localStorage.setItem('app_errors', JSON.stringify(recentErrors));
    } catch (e) {
      console.warn('Failed to store error locally:', e);
    }
  }

  private getStoredErrors(): ErrorLogEntry[] {
    try {
      const stored = localStorage.getItem('app_errors');
      return stored ? JSON.parse(stored) : [];
    } catch (e) {
      return [];
    }
  }

  private async sendErrorToServer(error: ErrorLogEntry): Promise<void> {
    try {
      // Skip server logging when backend is unavailable to prevent error cascade
      if (error.message?.includes('Backend service unavailable') || 
          error.message?.includes('ECONNREFUSED') ||
          error.code === 'NETWORK_ERROR') {
        console.log('Skipping error logging - backend unavailable');
        return;
      }
      
      const response = await fetch('/api/errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(error),
      });
      
      if (!response.ok) {
        throw new Error(`Error logging failed: ${response.status}`);
      }
    } catch (e) {
      // If sending fails, silently fail to prevent error cascade
      console.log('Error logging to server failed, continuing without logging:', e);
    }
  }

  private async flushErrorQueue(): Promise<void> {
    if (this.errorQueue.length === 0) return;

    const errors = [...this.errorQueue];
    this.errorQueue = [];

    for (const error of errors) {
      await this.sendErrorToServer(error);
    }
  }

  // Public methods for specific error types
  handleNetworkError(error: any, context?: Record<string, any>): AppError {
    const networkError = new NetworkError(
      error.message || 'Network request failed',
      error.status || error.code,
      error
    );
    return this.handleError(networkError, context);
  }

  handleAPIError(response: Response, data?: any): AppError {
    const apiError = new APIError(
      data?.message || `API request failed with status ${response.status}`,
      response.status,
      { response, data }
    );
    return this.handleError(apiError, { url: response.url });
  }

  handleValidationError(message: string, field?: string, details?: any): AppError {
    const validationError = new ValidationError(message, field, details);
    return this.handleError(validationError);
  }

  handleAuthError(message: string, code?: string): AppError {
    const authError = new AuthError(message, code);
    return this.handleError(authError);
  }
}

// Export singleton instance
export const errorHandler = ErrorHandler.getInstance();