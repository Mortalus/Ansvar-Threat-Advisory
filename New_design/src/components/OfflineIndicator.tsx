import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff, Cloud, CloudOff } from 'lucide-react';

export function OfflineIndicator() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [showNotification, setShowNotification] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setShowNotification(true);
      setTimeout(() => setShowNotification(false), 3000);
    };

    const handleOffline = () => {
      setIsOnline(false);
      setShowNotification(true);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (isOnline && !showNotification) return null;

  return (
    <div className={`
      fixed bottom-4 left-4 z-50 transform transition-all duration-300 ease-in-out
      ${showNotification ? 'translate-y-0 opacity-100' : 'translate-y-2 opacity-90'}
    `}>
      <div className={`
        flex items-center space-x-3 px-4 py-3 rounded-lg shadow-lg backdrop-blur-sm border
        ${isOnline 
          ? 'bg-green-50 border-green-200 text-green-800' 
          : 'bg-red-50 border-red-200 text-red-800'
        }
      `}>
        <div className={`
          flex-shrink-0 p-2 rounded-full
          ${isOnline ? 'bg-green-100' : 'bg-red-100'}
        `}>
          {isOnline ? (
            <Wifi className={`w-4 h-4 ${isOnline ? 'text-green-600' : 'text-red-600'}`} />
          ) : (
            <WifiOff className="w-4 h-4 text-red-600" />
          )}
        </div>
        
        <div className="flex-1">
          <p className="text-sm font-medium">
            {isOnline ? 'Back Online' : 'You\'re Offline'}
          </p>
          <p className="text-xs opacity-75">
            {isOnline 
              ? 'All features are now available' 
              : 'Some features may be limited'
            }
          </p>
        </div>

        {!isOnline && (
          <div className="flex-shrink-0">
            <CloudOff className="w-4 h-4 text-red-500" />
          </div>
        )}
      </div>
    </div>
  );
}