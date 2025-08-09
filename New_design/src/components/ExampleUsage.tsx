import React, { useState } from 'react';
import { useErrorHandler } from '../hooks/useErrorHandler';
import { useOfflineStorage } from '../hooks/useOfflineStorage';
import { apiClient } from '../utils/apiClient';

interface TodoItem {
  id: string;
  title: string;
  completed: boolean;
}

export function ExampleUsage() {
  const { handleError, handleNetworkError, handleValidationError } = useErrorHandler();
  const [loading, setLoading] = useState(false);
  
  // Offline storage for todos
  const {
    items: todos,
    addItem: addTodo,
    updateItem: updateTodo,
    syncPendingItems,
    hasUnsyncedItems,
    getUnsyncedCount
  } = useOfflineStorage<TodoItem>({
    key: 'todos',
    syncOnReconnect: true,
    maxItems: 50
  });

  // Example: Network error handling
  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get<any[]>('/todos');
      
      if (!response.success) {
        // Error is automatically handled by apiClient
        return;
      }
      
      console.log('Data fetched:', response.data);
    } catch (error) {
      handleNetworkError(error, { action: 'fetch_todos' });
    } finally {
      setLoading(false);
    }
  };

  // Example: Validation error handling
  const validateAndSubmit = (title: string) => {
    if (!title.trim()) {
      handleValidationError('Title is required', 'title');
      return;
    }

    if (title.length < 3) {
      handleValidationError('Title must be at least 3 characters long', 'title');
      return;
    }

    // Add todo (works offline)
    addTodo({
      id: Date.now().toString(),
      title: title.trim(),
      completed: false
    });
  };

  // Example: API error handling with retry
  const submitWithRetry = async (data: any) => {
    const maxRetries = 3;
    let attempt = 0;

    while (attempt < maxRetries) {
      try {
        const response = await apiClient.post('/submit', data);
        
        if (response.success) {
          console.log('Submitted successfully');
          return;
        }
        
        // If it's a validation error, don't retry
        if (response.error?.type === 'validation') {
          break;
        }
        
        attempt++;
        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
        }
      } catch (error) {
        attempt++;
        if (attempt >= maxRetries) {
          handleError(error, { 
            action: 'submit_data', 
            attempts: attempt,
            data 
          });
        }
      }
    }
  };

  // Example: File upload with progress and error handling
  const uploadFile = async (file: File) => {
    try {
      const response = await apiClient.uploadFile(
        '/upload',
        file,
        (progress) => {
          console.log(`Upload progress: ${progress}%`);
        }
      );

      if (!response.success) {
        // Error automatically handled by apiClient
        return;
      }

      console.log('File uploaded successfully');
    } catch (error) {
      handleError(error, { 
        action: 'file_upload',
        fileName: file.name,
        fileSize: file.size
      });
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold">Error Handling Examples</h2>
      
      {/* Network Operations */}
      <div className="bg-white p-4 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4">Network Operations</h3>
        <div className="space-x-4">
          <button
            onClick={fetchData}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Fetch Data'}
          </button>
          
          <button
            onClick={() => submitWithRetry({ test: 'data' })}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          >
            Submit with Retry
          </button>
        </div>
      </div>

      {/* Validation Examples */}
      <div className="bg-white p-4 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4">Validation Examples</h3>
        <div className="space-x-4">
          <button
            onClick={() => validateAndSubmit('')}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Submit Empty (Error)
          </button>
          
          <button
            onClick={() => validateAndSubmit('Hi')}
            className="bg-yellow-600 text-white px-4 py-2 rounded hover:bg-yellow-700"
          >
            Submit Short (Error)
          </button>
          
          <button
            onClick={() => validateAndSubmit('Valid Todo Item')}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          >
            Submit Valid
          </button>
        </div>
      </div>

      {/* Offline Storage */}
      <div className="bg-white p-4 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4">Offline Storage</h3>
        <div className="space-y-2">
          <p>Todos: {todos.length}</p>
          <p>Unsynced: {getUnsyncedCount()}</p>
          {hasUnsyncedItems && (
            <button
              onClick={syncPendingItems}
              className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
            >
              Sync Pending Items
            </button>
          )}
        </div>
      </div>

      {/* File Upload */}
      <div className="bg-white p-4 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4">File Upload</h3>
        <input
          type="file"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) {
              uploadFile(file);
            }
          }}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100"
        />
      </div>
    </div>
  );
}