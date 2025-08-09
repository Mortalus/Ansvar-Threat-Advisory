import { useState, useEffect, useCallback } from 'react';

export interface OfflineStorageOptions {
  key: string;
  syncOnReconnect?: boolean;
  maxItems?: number;
  ttl?: number; // Time to live in milliseconds
}

export interface StoredItem<T> {
  data: T;
  timestamp: number;
  synced: boolean;
  id: string;
}

export function useOfflineStorage<T>(options: OfflineStorageOptions) {
  const { key, syncOnReconnect = true, maxItems = 100, ttl } = options;
  const [items, setItems] = useState<StoredItem<T>[]>([]);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [syncQueue, setSyncQueue] = useState<StoredItem<T>[]>([]);

  // Load items from localStorage on mount
  useEffect(() => {
    loadFromStorage();
  }, [key]);

  // Handle online/offline status
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      if (syncOnReconnect) {
        syncPendingItems();
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [syncOnReconnect]);

  const loadFromStorage = useCallback(() => {
    try {
      const stored = localStorage.getItem(key);
      if (stored) {
        const parsedItems: StoredItem<T>[] = JSON.parse(stored);
        
        // Filter out expired items if TTL is set
        const validItems = ttl 
          ? parsedItems.filter(item => Date.now() - item.timestamp < ttl)
          : parsedItems;

        setItems(validItems);
        setSyncQueue(validItems.filter(item => !item.synced));
      }
    } catch (error) {
      console.warn('Failed to load from offline storage:', error);
    }
  }, [key, ttl]);

  const saveToStorage = useCallback((newItems: StoredItem<T>[]) => {
    try {
      // Keep only the most recent items if maxItems is set
      const itemsToStore = maxItems 
        ? newItems.slice(-maxItems)
        : newItems;

      localStorage.setItem(key, JSON.stringify(itemsToStore));
      setItems(itemsToStore);
    } catch (error) {
      console.warn('Failed to save to offline storage:', error);
    }
  }, [key, maxItems]);

  const addItem = useCallback((data: T, forceOffline = false) => {
    const newItem: StoredItem<T> = {
      data,
      timestamp: Date.now(),
      synced: isOnline && !forceOffline,
      id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };

    const updatedItems = [...items, newItem];
    saveToStorage(updatedItems);

    // Add to sync queue if not synced
    if (!newItem.synced) {
      setSyncQueue(prev => [...prev, newItem]);
    }

    return newItem.id;
  }, [items, isOnline, saveToStorage]);

  const updateItem = useCallback((id: string, data: Partial<T>) => {
    const updatedItems = items.map(item => 
      item.id === id 
        ? { 
            ...item, 
            data: { ...item.data, ...data },
            synced: false,
            timestamp: Date.now()
          }
        : item
    );

    saveToStorage(updatedItems);

    // Add updated item to sync queue
    const updatedItem = updatedItems.find(item => item.id === id);
    if (updatedItem && !updatedItem.synced) {
      setSyncQueue(prev => {
        const filtered = prev.filter(item => item.id !== id);
        return [...filtered, updatedItem];
      });
    }
  }, [items, saveToStorage]);

  const removeItem = useCallback((id: string) => {
    const updatedItems = items.filter(item => item.id !== id);
    saveToStorage(updatedItems);
    setSyncQueue(prev => prev.filter(item => item.id !== id));
  }, [items, saveToStorage]);

  const markAsSynced = useCallback((id: string) => {
    const updatedItems = items.map(item => 
      item.id === id ? { ...item, synced: true } : item
    );
    saveToStorage(updatedItems);
    setSyncQueue(prev => prev.filter(item => item.id !== id));
  }, [items, saveToStorage]);

  const syncPendingItems = useCallback(async () => {
    if (!isOnline || syncQueue.length === 0) return;

    const itemsToSync = [...syncQueue];
    
    for (const item of itemsToSync) {
      try {
        // This would be replaced with actual API call
        await syncItemToServer(item);
        markAsSynced(item.id);
      } catch (error) {
        console.warn('Failed to sync item:', error);
        // Keep item in sync queue for retry
      }
    }
  }, [isOnline, syncQueue, markAsSynced]);

  const clearStorage = useCallback(() => {
    localStorage.removeItem(key);
    setItems([]);
    setSyncQueue([]);
  }, [key]);

  const getUnsyncedCount = useCallback(() => {
    return items.filter(item => !item.synced).length;
  }, [items]);

  // Mock sync function - replace with actual API call
  const syncItemToServer = async (item: StoredItem<T>) => {
    // Simulate API call
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (Math.random() > 0.1) { // 90% success rate
          resolve(item);
        } else {
          reject(new Error('Sync failed'));
        }
      }, 1000);
    });
  };

  return {
    items,
    isOnline,
    syncQueue,
    addItem,
    updateItem,
    removeItem,
    markAsSynced,
    syncPendingItems,
    clearStorage,
    getUnsyncedCount,
    hasUnsyncedItems: syncQueue.length > 0
  };
}