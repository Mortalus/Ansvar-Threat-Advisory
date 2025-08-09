import { useState, useCallback } from 'react';
import { errorHandler, AppError } from '../utils/errorHandler';

export interface UseErrorHandlerReturn {
  error: AppError | null;
  isError: boolean;
  clearError: () => void;
  handleError: (error: any, context?: Record<string, any>) => AppError;
  handleNetworkError: (error: any, context?: Record<string, any>) => AppError;
  handleAPIError: (response: Response, data?: any) => AppError;
  handleValidationError: (message: string, field?: string, details?: any) => AppError;
  handleAuthError: (message: string, code?: string) => AppError;
}

export function useErrorHandler(): UseErrorHandlerReturn {
  const [error, setError] = useState<AppError | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const handleError = useCallback((error: any, context?: Record<string, any>) => {
    const appError = errorHandler.handleError(error, context);
    setError(appError);
    return appError;
  }, []);

  const handleNetworkError = useCallback((error: any, context?: Record<string, any>) => {
    const appError = errorHandler.handleNetworkError(error, context);
    setError(appError);
    return appError;
  }, []);

  const handleAPIError = useCallback((response: Response, data?: any) => {
    const appError = errorHandler.handleAPIError(response, data);
    setError(appError);
    return appError;
  }, []);

  const handleValidationError = useCallback((message: string, field?: string, details?: any) => {
    const appError = errorHandler.handleValidationError(message, field, details);
    setError(appError);
    return appError;
  }, []);

  const handleAuthError = useCallback((message: string, code?: string) => {
    const appError = errorHandler.handleAuthError(message, code);
    setError(appError);
    return appError;
  }, []);

  return {
    error,
    isError: !!error,
    clearError,
    handleError,
    handleNetworkError,
    handleAPIError,
    handleValidationError,
    handleAuthError,
  };
}