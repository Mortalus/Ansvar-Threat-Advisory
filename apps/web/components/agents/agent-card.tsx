'use client'

import { useState } from 'react'
import { AgentInfo, api } from '@/lib/api'
import { Card } from '@/components/ui/card'

interface AgentCardProps {
  agent: AgentInfo
  onConfigure: () => void
}

export default function AgentCard({ agent, onConfigure }: AgentCardProps) {
  const [isTestingAgent, setIsTestingAgent] = useState(false)
  const [testResult, setTestResult] = useState<string | null>(null)

  const handleTestAgent = async () => {
    try {
      setIsTestingAgent(true)
      setTestResult(null)
      
      const result = await api.testAgent(agent.name, {
        use_mock_llm: true,
        sample_document: "This is a sample document for testing the agent."
      })

      if (result.success) {
        setTestResult(`✅ Test passed! Generated ${result.threats_generated} threats in ${result.execution_time.toFixed(2)}s`)
      } else {
        setTestResult(`❌ Test failed: ${result.error_message || 'Unknown error'}`)
      }
    } catch (error) {
      setTestResult(`❌ Test failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsTestingAgent(false)
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'architectural': return 'bg-blue-100 text-blue-800'
      case 'business': return 'bg-green-100 text-green-800'
      case 'compliance': return 'bg-purple-100 text-purple-800'
      case 'security': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getPriorityColor = (priority: number) => {
    if (priority <= 50) return 'text-red-600' // High priority (lower numbers = higher priority)
    if (priority <= 100) return 'text-yellow-600' // Medium priority
    return 'text-green-600' // Low priority
  }

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
          <p className="text-sm text-gray-500">v{agent.version}</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(agent.category)}`}>
            {agent.category}
          </span>
          {agent.enabled_by_default && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Enabled
            </span>
          )}
        </div>
      </div>

      <p className="text-gray-600 text-sm mb-4 line-clamp-3">
        {agent.description}
      </p>

      {/* Agent Details */}
      <div className="space-y-2 text-xs text-gray-500 mb-4">
        <div className="flex justify-between">
          <span>Priority:</span>
          <span className={`font-medium ${getPriorityColor(agent.priority)}`}>
            {agent.priority}
          </span>
        </div>
        <div className="flex justify-between">
          <span>Est. Tokens:</span>
          <span className="font-medium">{agent.estimated_tokens.toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span>Requirements:</span>
          <span className="font-medium">
            {agent.requires_document && '📄'}
            {agent.requires_components && '🔧'}
            {!agent.requires_document && !agent.requires_components && 'None'}
          </span>
        </div>
        {agent.legacy_equivalent && (
          <div className="flex justify-between">
            <span>Legacy Name:</span>
            <span className="font-medium text-blue-600">{agent.legacy_equivalent}</span>
          </div>
        )}
      </div>

      {/* Test Result */}
      {testResult && (
        <div className="mb-4 p-2 bg-gray-50 rounded text-xs">
          {testResult}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex space-x-2">
        <button
          onClick={onConfigure}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-sm font-medium transition-colors"
        >
          Configure
        </button>
        <button
          onClick={handleTestAgent}
          disabled={isTestingAgent}
          className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded text-sm font-medium transition-colors disabled:opacity-50"
        >
          {isTestingAgent ? 'Testing...' : 'Test'}
        </button>
      </div>

      {/* Agent Class Info */}
      <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-400">
        Class: {agent.class_name}
      </div>
    </Card>
  )
}