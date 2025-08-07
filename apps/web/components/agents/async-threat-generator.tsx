'use client'

import { useState } from 'react'
import { api } from '@/lib/api'
import { useWebSocket } from '@/hooks/use-websocket'
import { Card } from '@/components/ui/card'

interface AsyncThreatGeneratorProps {
  pipelineId: string
  onComplete?: (result: any) => void
}

export default function AsyncThreatGenerator({ pipelineId, onComplete }: AsyncThreatGeneratorProps) {
  const [isRunning, setIsRunning] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [progress, setProgress] = useState<number>(0)
  const [currentStep, setCurrentStep] = useState<string>('')
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const { isConnected, lastMessage } = useWebSocket(pipelineId, {
    onMessage: (message) => {
      console.log('WebSocket message:', message)
      
      // Handle progress updates
      if (message.type === 'step_progress' || message.type === 'task_progress') {
        setProgress(message.progress || 0)
        setCurrentStep(message.step || '')
      }
      
      // Handle step completion
      if (message.type === 'step_complete') {
        if (message.step === 'generate_threats') {
          setResult(message.data)
          setIsRunning(false)
          onComplete?.(message.data)
        }
      }
      
      // Handle errors
      if (message.type === 'error') {
        setError(message.error || 'Unknown error occurred')
        setIsRunning(false)
      }
    },
    onConnect: () => {
      console.log('WebSocket connected for async threat generation')
    },
    onDisconnect: () => {
      console.log('WebSocket disconnected')
    }
  })

  const startThreatGeneration = async () => {
    try {
      setIsRunning(true)
      setError(null)
      setResult(null)
      setProgress(0)
      setCurrentStep('Starting threat generation...')

      // Start background task
      const response = await api.executeStepInBackground(pipelineId, 'generate_threats', {
        use_v3_generator: true,
        multi_agent: true,
        context_aware: true
      })

      setTaskId(response.task_id)
      setCurrentStep('Task started, waiting for updates...')
      
      // Poll task status as backup if WebSocket fails
      pollTaskStatus(response.task_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start threat generation')
      setIsRunning(false)
    }
  }

  const pollTaskStatus = async (taskId: string) => {
    if (!isRunning) return

    try {
      const status = await api.getTaskStatus(taskId)
      
      if (status.status === 'completed' && status.result) {
        setResult(status.result)
        setProgress(100)
        setCurrentStep('Completed')
        setIsRunning(false)
        onComplete?.(status.result)
      } else if (status.status === 'failed') {
        setError(status.error || 'Task failed')
        setIsRunning(false)
      } else if (status.status === 'running') {
        setProgress(status.progress || progress)
        // Continue polling
        setTimeout(() => pollTaskStatus(taskId), 2000)
      }
    } catch (error) {
      console.error('Failed to poll task status:', error)
      // Continue polling despite errors
      if (isRunning) {
        setTimeout(() => pollTaskStatus(taskId), 2000)
      }
    }
  }

  const formatThreats = (threatData: any) => {
    if (!threatData?.threats) return null

    return (
      <div className="mt-4 space-y-3">
        <h4 className="font-medium text-gray-900">
          Generated {threatData.threats.length} threats
        </h4>
        <div className="max-h-64 overflow-y-auto space-y-2">
          {threatData.threats.slice(0, 5).map((threat: any, index: number) => (
            <div key={index} className="bg-gray-50 p-3 rounded-lg text-sm">
              <p className="font-medium text-gray-900">
                {threat['Threat Name'] || threat.threat_name}
              </p>
              <p className="text-gray-600 mt-1">
                {threat['Description'] || threat.description}
              </p>
              <div className="flex justify-between mt-2 text-xs text-gray-500">
                <span>Impact: {threat['Potential Impact'] || threat.impact}</span>
                <span>Likelihood: {threat['Likelihood'] || threat.likelihood}</span>
              </div>
            </div>
          ))}
          {threatData.threats.length > 5 && (
            <p className="text-sm text-gray-500 text-center">
              +{threatData.threats.length - 5} more threats
            </p>
          )}
        </div>
      </div>
    )
  }

  return (
    <Card className="p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-medium text-gray-900">
            Async Threat Generation
          </h3>
          <p className="text-sm text-gray-500">
            Generate threats using background tasks with real-time updates
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {isConnected ? (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              🟢 Connected
            </span>
          ) : (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
              🔴 Disconnected
            </span>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {isRunning && (
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600">{currentStep}</span>
            <span className="text-gray-600">{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="flex space-x-2 mb-4">
        <button
          onClick={startThreatGeneration}
          disabled={isRunning}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isRunning ? 'Generating...' : 'Start Async Generation'}
        </button>
        
        {taskId && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            Task: {taskId.slice(0, 8)}...
          </span>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && formatThreats(result)}

      {/* WebSocket Status */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          WebSocket: {isConnected ? 'Connected' : 'Disconnected'} | 
          Last message: {lastMessage ? new Date(lastMessage.timestamp || Date.now()).toLocaleTimeString() : 'None'}
        </p>
      </div>
    </Card>
  )
}