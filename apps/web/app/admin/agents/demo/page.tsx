'use client'

import { useState } from 'react'
import { api } from '@/lib/api'
import { Card } from '@/components/ui/card'
import AsyncThreatGenerator from '@/components/agents/async-threat-generator'

export default function AgentDemoPage() {
  const [pipelineId, setPipelineId] = useState<string>('')
  const [isCreatingPipeline, setIsCreatingPipeline] = useState(false)

  const createTestPipeline = async () => {
    try {
      setIsCreatingPipeline(true)
      const pipeline = await api.createPipeline({
        name: 'Agent Demo Pipeline',
        description: 'Demo pipeline for testing async agent operations'
      })
      setPipelineId(pipeline.pipeline_id || pipeline.id)
    } catch (error) {
      console.error('Failed to create pipeline:', error)
      alert('Failed to create test pipeline')
    } finally {
      setIsCreatingPipeline(false)
    }
  }

  const handleThreatGenerationComplete = (result: any) => {
    console.log('Threat generation completed:', result)
    alert(`Generated ${result?.threats?.length || 0} threats successfully!`)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900">Agent Demo</h1>
        <p className="mt-1 text-gray-600">
          Test async operations and real-time WebSocket integration
        </p>
      </div>

      {/* Pipeline Setup */}
      <Card className="p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Pipeline Setup</h2>
        
        {!pipelineId ? (
          <div className="space-y-4">
            <p className="text-gray-600">
              Create a test pipeline to demonstrate async agent operations.
            </p>
            <button
              onClick={createTestPipeline}
              disabled={isCreatingPipeline}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-50"
            >
              {isCreatingPipeline ? 'Creating Pipeline...' : 'Create Test Pipeline'}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-md p-3">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-green-800">Pipeline Ready</h3>
                  <p className="text-sm text-green-700 mt-1">Pipeline ID: {pipelineId}</p>
                </div>
              </div>
            </div>
            
            <div className="flex space-x-2">
              <button
                onClick={() => setPipelineId('')}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded text-sm font-medium"
              >
                Create New Pipeline
              </button>
            </div>
          </div>
        )}
      </Card>

      {/* Async Operations Demo */}
      {pipelineId && (
        <>
          <AsyncThreatGenerator
            pipelineId={pipelineId}
            onComplete={handleThreatGenerationComplete}
          />

          {/* Additional Demo Components */}
          <Card className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Features Demonstrated
            </h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                Background task execution via REST API
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                Real-time WebSocket progress updates
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                Automatic reconnection handling
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                Fallback polling mechanism
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                Multi-agent threat analysis (V3 generator)
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                Progress visualization and status updates
              </li>
            </ul>
          </Card>

          {/* Technical Information */}
          <Card className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Technical Implementation
            </h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Backend Integration</h4>
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>• <code>/api/tasks/execute-step</code> endpoint</li>
                  <li>• <code>/api/tasks/status/{'{task_id}'}</code> polling</li>
                  <li>• WebSocket at <code>/ws/{'{pipeline_id}'}</code></li>
                  <li>• Celery background processing</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Frontend Features</h4>
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>• React hooks for WebSocket management</li>
                  <li>• Automatic reconnection logic</li>
                  <li>• Progress bar visualization</li>
                  <li>• Error handling and fallback polling</li>
                </ul>
              </div>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}