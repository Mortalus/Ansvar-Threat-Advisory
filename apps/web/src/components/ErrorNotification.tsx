import React, { useState, useEffect } from 'react';
import { X, AlertTriangle, AlertCircle, Info, CheckCircle, Wifi, WifiOff } from 'lucide-react';
import { AppError } from '../utils/errorHandler';

interface ErrorNotificationProps {
  error: AppError;
  onClose: () => void;
  autoClose?: boolean;
  duration?: number;
}

export function ErrorNotification({ 
  error, 
  onClose, 
  autoClose = true, 
  duration = 5000 
}: ErrorNotificationProps) {
  const [isVisible, setIsVisible] = useState(true);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    if (autoClose && error.type !== 'offline') {
      const timer = setTimeout(() => {
        handleClose();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [autoClose, duration, error.type]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(onClose, 300); // Wait for animation
  };

  const getErrorIcon = () => {
    switch (error.type) {
      case 'network':
        return <Wifi className="w-5 h-5" />;
      case 'offline':
        return <WifiOff className="w-5 h-5" />;
      case 'validation':
        return <Info className="w-5 h-5" />;
      case 'auth':
        return <AlertCircle className="w-5 h-5" />;
      case 'api':
        return <AlertTriangle className="w-5 h-5" />;
      default:
        return <AlertTriangle className="w-5 h-5" />;
    }
  };

  const getErrorStyles = () => {
    switch (error.type) {
      case 'validation':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      case 'network':
        return 'bg-orange-50 border-orange-200 text-orange-800';
      case 'offline':
        return 'bg-gray-50 border-gray-200 text-gray-800';
      case 'auth':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'api':
      case 'system':
      default:
        return 'bg-red-50 border-red-200 text-red-800';
    }
  };

  const getIconStyles = () => {
    switch (error.type) {
      case 'validation':
        return 'text-blue-600';
      case 'network':
        return 'text-orange-600';
      case 'offline':
        return 'text-gray-600';
      case 'auth':
        return 'text-yellow-600';
      case 'api':
      case 'system':
      default:
        return 'text-red-600';
    }
  };

  if (!isVisible) return null;

  return (
    <div className={`
      fixed top-4 right-4 z-50 max-w-sm w-full transform transition-all duration-300 ease-in-out
      ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
    `}>
      <div className={`
        rounded-lg border p-4 shadow-lg backdrop-blur-sm
        ${getErrorStyles()}
      `}>
        <div className="flex items-start space-x-3">
          <div className={`flex-shrink-0 ${getIconStyles()}`}>
            {getErrorIcon()}
          </div>
          
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-medium capitalize">
              {error.type.replace('_', ' ')} Error
            </h4>
            <p className="text-sm mt-1 opacity-90">
              {error.userMessage}
            </p>
            
            {error.type === 'offline' && !isOnline && (
              <div className="mt-2 text-xs opacity-75">
                <p>• Some features may be limited</p>
                <p>• Changes will sync when connection is restored</p>
              </div>
            )}
            
            {error.type === 'offline' && isOnline && (
              <div className="mt-2 flex items-center space-x-1 text-xs">
                <CheckCircle className="w-3 h-3 text-green-600" />
                <span className="text-green-600">Connection restored</span>
              </div>
            )}
          </div>
          
          <button
            onClick={handleClose}
            className="flex-shrink-0 p-1 rounded-md hover:bg-black/10 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        
        {/* Progress bar for auto-close */}
        {autoClose && error.type !== 'offline' && (
          <div className="mt-3 w-full bg-black/10 rounded-full h-1">
            <div 
              className="bg-current h-1 rounded-full transition-all ease-linear"
              style={{ 
                width: '100%',
                animation: `shrink ${duration}ms linear forwards`
              }}
            />
          </div>
        )}
      </div>
      
      <style jsx>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  );
}