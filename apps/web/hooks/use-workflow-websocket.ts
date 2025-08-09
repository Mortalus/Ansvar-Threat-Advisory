import { useEffect, useRef, useCallback } from 'react';

export interface WorkflowEvent {
  type: 'run_status' | 'step_status' | 'artifact_created' | 'error';
  run_id: string;
  data: any;
  timestamp: string;
}

interface UseWorkflowWebSocketOptions {
  runId?: string;
  onMessage?: (event: WorkflowEvent) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

export function useWorkflowWebSocket({
  runId,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  autoReconnect = true,
  reconnectInterval = 5000,
}: UseWorkflowWebSocketOptions) {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const isIntentionalClose = useRef(false);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      // Construct WebSocket URL based on environment
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = runId 
        ? `${protocol}//${host}/api/ws/workflow/${runId}`
        : `${protocol}//${host}/api/ws/workflow`;

      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('WebSocket connected for workflow updates');
        onConnect?.();
        
        // Clear any pending reconnect timeout
        if (reconnectTimeout.current) {
          clearTimeout(reconnectTimeout.current);
          reconnectTimeout.current = null;
        }

        // Subscribe to specific run if provided
        if (runId && ws.current?.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({
            type: 'subscribe',
            run_id: runId
          }));
        }
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WorkflowEvent;
          onMessage?.(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        onDisconnect?.();
        
        // Attempt to reconnect if not intentionally closed
        if (autoReconnect && !isIntentionalClose.current) {
          reconnectTimeout.current = setTimeout(() => {
            console.log('Attempting to reconnect WebSocket...');
            connect();
          }, reconnectInterval);
        }
      };
    } catch (error) {
      console.error('Failed to establish WebSocket connection:', error);
      
      // Retry connection if auto-reconnect is enabled
      if (autoReconnect) {
        reconnectTimeout.current = setTimeout(connect, reconnectInterval);
      }
    }
  }, [runId, onMessage, onConnect, onDisconnect, onError, autoReconnect, reconnectInterval]);

  const disconnect = useCallback(() => {
    isIntentionalClose.current = true;
    
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
    
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }, []);

  // Connect on mount and disconnect on unmount
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Reconnect if runId changes
  useEffect(() => {
    if (runId && ws.current?.readyState === WebSocket.OPEN) {
      sendMessage({
        type: 'subscribe',
        run_id: runId
      });
    }
  }, [runId, sendMessage]);

  return {
    isConnected: ws.current?.readyState === WebSocket.OPEN,
    sendMessage,
    disconnect,
    reconnect: connect,
  };
}

// Hook for workflow list updates
export function useWorkflowListWebSocket(onUpdate: (event: WorkflowEvent) => void) {
  return useWorkflowWebSocket({
    onMessage: (event) => {
      if (event.type === 'run_status') {
        onUpdate(event);
      }
    }
  });
}

// Hook for specific workflow run updates
export function useWorkflowRunWebSocket(
  runId: string,
  onUpdate: (event: WorkflowEvent) => void
) {
  return useWorkflowWebSocket({
    runId,
    onMessage: onUpdate
  });
}