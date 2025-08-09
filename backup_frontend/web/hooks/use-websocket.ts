'use client'

import { useEffect, useRef, useState } from 'react'
import { api } from '@/lib/api'

interface WebSocketMessage {
  type: string
  pipeline_id?: string
  step?: string
  status?: string
  progress?: number
  data?: any
  error?: string
  timestamp?: string
}

interface UseWebSocketOptions {
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onMessage?: (message: WebSocketMessage) => void
  onError?: (error: Event) => void
  onConnect?: () => void
  onDisconnect?: () => void
}

export function useWebSocket(pipelineId: string | null, options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [connectionAttempts, setConnectionAttempts] = useState(0)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()

  const {
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onMessage,
    onError,
    onConnect,
    onDisconnect
  } = options

  const connect = () => {
    if (!pipelineId || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      wsRef.current = api.connectWebSocket(pipelineId, {
        onMessage: (data: WebSocketMessage) => {
          setLastMessage(data)
          onMessage?.(data)
        },
        onError: (error: Event) => {
          console.error('WebSocket error:', error)
          setIsConnected(false)
          onError?.(error)
          scheduleReconnect()
        },
        onClose: () => {
          setIsConnected(false)
          onDisconnect?.()
          scheduleReconnect()
        }
      })

      wsRef.current.onopen = () => {
        setIsConnected(true)
        setConnectionAttempts(0)
        onConnect?.()
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      scheduleReconnect()
    }
  }

  const scheduleReconnect = () => {
    if (connectionAttempts >= maxReconnectAttempts) {
      console.warn(`Max reconnection attempts (${maxReconnectAttempts}) reached`)
      return
    }

    reconnectTimeoutRef.current = setTimeout(() => {
      setConnectionAttempts(prev => prev + 1)
      connect()
    }, reconnectInterval)
  }

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    setIsConnected(false)
    setConnectionAttempts(0)
  }

  const sendMessage = (message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }

  useEffect(() => {
    if (pipelineId) {
      connect()
    } else {
      disconnect()
    }

    return () => {
      disconnect()
    }
  }, [pipelineId])

  return {
    isConnected,
    lastMessage,
    connectionAttempts,
    connect,
    disconnect,
    sendMessage
  }
}