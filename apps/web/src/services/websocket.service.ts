import { io, Socket } from 'socket.io-client';
import { toast } from 'react-hot-toast';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

interface WebSocketOptions {
  reconnection?: boolean;
  reconnectionAttempts?: number;
  reconnectionDelay?: number;
  timeout?: number;
}

interface EventHandler {
  event: string;
  handler: (...args: any[]) => void;
}

class WebSocketService {
  private socket: Socket | null = null;
  private eventHandlers: Map<string, Set<(...args: any[]) => void>> = new Map();
  private isConnected: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private messageQueue: Array<{ event: string; data: any }> = [];

  /**
   * Connect to WebSocket server
   */
  connect(token?: string, options?: WebSocketOptions): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket?.connected) {
        resolve();
        return;
      }

      try {
        this.socket = io(WS_URL, {
          transports: ['websocket'],
          reconnection: options?.reconnection ?? true,
          reconnectionAttempts: options?.reconnectionAttempts ?? this.maxReconnectAttempts,
          reconnectionDelay: options?.reconnectionDelay ?? 1000,
          timeout: options?.timeout ?? 10000,
          auth: token ? { token } : undefined,
        });

        this.setupCoreEventHandlers();
        
        // Resolve on successful connection
        this.socket.once('connect', () => {
          this.onConnect();
          resolve();
        });

        // Reject on connection error
        this.socket.once('connect_error', (error) => {
          console.error('WebSocket connection error:', error);
          reject(error);
        });

      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.clearTimers();
    
    if (this.socket) {
      this.socket.removeAllListeners();
      this.socket.disconnect();
      this.socket = null;
    }

    this.isConnected = false;
    this.eventHandlers.clear();
    this.messageQueue = [];
  }

  /**
   * Setup core event handlers
   */
  private setupCoreEventHandlers(): void {
    if (!this.socket) return;

    // Connection events
    this.socket.on('connect', () => this.onConnect());
    this.socket.on('disconnect', (reason) => this.onDisconnect(reason));
    this.socket.on('connect_error', (error) => this.onConnectError(error));

    // Custom events
    this.socket.on('error', (error) => this.onError(error));
    this.socket.on('pong', () => this.onPong());

    // Pipeline events
    this.socket.on('pipeline:update', (data) => this.handlePipelineUpdate(data));
    this.socket.on('pipeline:complete', (data) => this.handlePipelineComplete(data));
    this.socket.on('pipeline:error', (data) => this.handlePipelineError(data));

    // Workflow events
    this.socket.on('workflow:progress', (data) => this.handleWorkflowProgress(data));
    this.socket.on('workflow:complete', (data) => this.handleWorkflowComplete(data));
    this.socket.on('workflow:error', (data) => this.handleWorkflowError(data));

    // Agent events
    this.socket.on('agent:status', (data) => this.handleAgentStatus(data));
    this.socket.on('agent:health', (data) => this.handleAgentHealth(data));
  }

  /**
   * Handle connection established
   */
  private onConnect(): void {
    this.isConnected = true;
    this.reconnectAttempts = 0;
    
    console.log('WebSocket connected');
    
    // Start heartbeat
    this.startHeartbeat();
    
    // Process queued messages
    this.processMessageQueue();

    // Notify user if this was a reconnection
    if (this.reconnectAttempts > 0) {
      toast.success('Connection restored');
    }
  }

  /**
   * Handle disconnection
   */
  private onDisconnect(reason: string): void {
    this.isConnected = false;
    this.clearTimers();
    
    console.log('WebSocket disconnected:', reason);

    // Handle different disconnect reasons
    switch (reason) {
      case 'io server disconnect':
        // Server initiated disconnect
        toast.error('Disconnected by server');
        this.attemptReconnect();
        break;
      case 'ping timeout':
        // Connection lost
        toast.error('Connection lost');
        this.attemptReconnect();
        break;
      case 'transport close':
        // Network issue
        toast.error('Network connection lost');
        this.attemptReconnect();
        break;
      default:
        // Client initiated or other reasons
        console.log('Disconnect reason:', reason);
    }
  }

  /**
   * Handle connection error
   */
  private onConnectError(error: Error): void {
    console.error('WebSocket connection error:', error);
    
    if (this.reconnectAttempts === 0) {
      toast.error('Failed to connect to server');
    }
  }

  /**
   * Handle general errors
   */
  private onError(error: any): void {
    console.error('WebSocket error:', error);
    toast.error(error.message || 'WebSocket error occurred');
  }

  /**
   * Attempt to reconnect
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      toast.error('Unable to reconnect. Please refresh the page.');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

    console.log(`Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);

    this.reconnectTimer = setTimeout(() => {
      if (this.socket && !this.isConnected) {
        this.socket.connect();
      }
    }, delay);
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.clearHeartbeatTimer();

    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected && this.socket) {
        this.socket.emit('ping');
      }
    }, 30000); // Every 30 seconds
  }

  /**
   * Handle heartbeat response
   */
  private onPong(): void {
    // Connection is alive
  }

  /**
   * Clear all timers
   */
  private clearTimers(): void {
    this.clearReconnectTimer();
    this.clearHeartbeatTimer();
  }

  /**
   * Clear reconnect timer
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Clear heartbeat timer
   */
  private clearHeartbeatTimer(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Process queued messages
   */
  private processMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.emit(message.event, message.data);
      }
    }
  }

  // Public methods for event handling

  /**
   * Subscribe to an event
   */
  on(event: string, handler: (...args: any[]) => void): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    
    this.eventHandlers.get(event)?.add(handler);

    // Also register with socket if connected
    if (this.socket && !this.socket.hasListeners(event)) {
      this.socket.on(event, (...args) => {
        this.eventHandlers.get(event)?.forEach(h => h(...args));
      });
    }
  }

  /**
   * Unsubscribe from an event
   */
  off(event: string, handler?: (...args: any[]) => void): void {
    if (!handler) {
      // Remove all handlers for this event
      this.eventHandlers.delete(event);
      this.socket?.removeAllListeners(event);
    } else {
      // Remove specific handler
      this.eventHandlers.get(event)?.delete(handler);
      
      // If no more handlers, remove socket listener
      if (this.eventHandlers.get(event)?.size === 0) {
        this.socket?.removeAllListeners(event);
      }
    }
  }

  /**
   * Emit an event
   */
  emit(event: string, data?: any): void {
    if (this.isConnected && this.socket) {
      this.socket.emit(event, data);
    } else {
      // Queue message for later
      this.messageQueue.push({ event, data });
      console.warn('WebSocket not connected. Message queued:', event);
    }
  }

  /**
   * Send a message and wait for response
   */
  request<T = any>(event: string, data?: any, timeout: number = 5000): Promise<T> {
    return new Promise((resolve, reject) => {
      if (!this.isConnected || !this.socket) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      const timer = setTimeout(() => {
        reject(new Error(`Request timeout: ${event}`));
      }, timeout);

      this.socket.emit(event, data, (response: any) => {
        clearTimeout(timer);
        
        if (response.error) {
          reject(response.error);
        } else {
          resolve(response);
        }
      });
    });
  }

  // Pipeline event handlers

  private handlePipelineUpdate(data: any): void {
    console.log('Pipeline update:', data);
    // Will be handled by pipeline store
  }

  private handlePipelineComplete(data: any): void {
    console.log('Pipeline complete:', data);
    toast.success('Pipeline completed successfully');
  }

  private handlePipelineError(data: any): void {
    console.error('Pipeline error:', data);
    toast.error(data.message || 'Pipeline error occurred');
  }

  // Workflow event handlers

  private handleWorkflowProgress(data: any): void {
    console.log('Workflow progress:', data);
    // Will be handled by workflow store
  }

  private handleWorkflowComplete(data: any): void {
    console.log('Workflow complete:', data);
    toast.success('Workflow completed successfully');
  }

  private handleWorkflowError(data: any): void {
    console.error('Workflow error:', data);
    toast.error(data.message || 'Workflow error occurred');
  }

  // Agent event handlers

  private handleAgentStatus(data: any): void {
    console.log('Agent status:', data);
    // Will be handled by agent store
  }

  private handleAgentHealth(data: any): void {
    console.log('Agent health:', data);
    // Will be handled by agent store
  }

  // Getters

  get connected(): boolean {
    return this.isConnected;
  }

  get socketId(): string | undefined {
    return this.socket?.id;
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();