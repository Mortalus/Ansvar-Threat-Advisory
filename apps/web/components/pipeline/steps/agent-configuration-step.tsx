'use client'

import { useState, useEffect } from 'react'
import { useStore } from '@/lib/store'
import { api, AgentInfo } from '@/lib/api'
import { Card } from '@/components/ui/card'
import { Settings, Zap, CheckCircle, ArrowRight } from 'lucide-react'

export function AgentConfigurationStep() {
  const {
    currentPipelineId,
    dfdComponents,
    setStepStatus,
    setCurrentStep,
    stepStates,
  } = useStore()

  const [agents, setAgents] = useState<AgentInfo[]>([])
  const [enabledAgents, setEnabledAgents] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Defensive: Check if API is available first
      if (!api || !api.getAvailableAgents) {
        throw new Error('Agent API is not available')
      }
      
      const agentList = await api.getAvailableAgents()
      
      // Defensive: Validate response structure
      if (!agentList || !Array.isArray(agentList)) {
        console.warn('Invalid agent list response:', agentList)
        throw new Error('Invalid agent data received from server')
      }
      
      setAgents(agentList)
      
      // Set default enabled agents (those marked enabled_by_default)
      const defaultEnabled = agentList
        .filter(agent => agent && agent.enabled_by_default)
        .map(agent => agent.name)
        .filter(Boolean) // Remove any undefined names
      
      setEnabledAgents(defaultEnabled)
      
      console.log(`✅ Loaded ${agentList.length} agents, ${defaultEnabled.length} enabled by default`)
    } catch (err) {
      console.error('❌ Failed to load agents:', err)
      const errorMessage = err instanceof Error ? err.message : 'Failed to load agents'
      setError(`${errorMessage}. Please check that the backend services are running.`)
      
      // Defensive: Set fallback agents to prevent UI from breaking
      setAgents([])
      setEnabledAgents([])
    } finally {
      setLoading(false)
    }
  }

  const toggleAgent = (agentName: string) => {
    setEnabledAgents(prev => 
      prev.includes(agentName)
        ? prev.filter(name => name !== agentName)
        : [...prev, agentName]
    )
  }

  const handleContinue = () => {
    try {
      // Defensive: Validate that we have enabled agents
      if (!enabledAgents || enabledAgents.length === 0) {
        setError('Please select at least one agent before continuing')
        return
      }
      
      // Defensive: Validate agent names
      const validAgentNames = enabledAgents.filter(name => 
        name && typeof name === 'string' && name.length > 0
      )
      
      if (validAgentNames.length !== enabledAgents.length) {
        console.warn('Some invalid agent names filtered out:', enabledAgents)
      }
      
      if (validAgentNames.length === 0) {
        setError('No valid agents selected')
        return
      }
      
      console.log(`✅ Continuing with ${validAgentNames.length} selected agents:`, validAgentNames)
      
      // Store agent configuration for the threat generation step
      useStore.setState({ selectedAgents: validAgentNames })
      setStepStatus('agent_config', 'complete')
      setCurrentStep('threat_generation')
      
    } catch (err) {
      console.error('❌ Error in handleContinue:', err)
      setError('Failed to save agent configuration. Please try again.')
    }
  }

  const getAgentDescription = (agent: AgentInfo) => {
    const descriptions = {
      'architectural_risk': 'Analyzes system design and architecture for structural vulnerabilities',
      'business_financial': 'Quantifies business impact and financial risks of threats',
      'compliance_governance': 'Ensures regulatory compliance and governance standards'
    }
    return descriptions[agent.name as keyof typeof descriptions] || agent.description
  }

  const isStepComplete = stepStates.agent_config?.status === 'complete'
  const estimatedTokens = agents
    .filter(agent => enabledAgents.includes(agent.name))
    .reduce((sum, agent) => sum + agent.estimated_tokens, 0)

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />
          <span>Loading threat analysis agents...</span>
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="p-6 border-red-200 bg-red-50">
        <div className="text-red-700">
          <h3 className="font-medium">Error Loading Agents</h3>
          <p className="text-sm mt-1">{error}</p>
          <button
            onClick={loadAgents}
            className="mt-2 text-sm text-red-600 hover:text-red-800"
          >
            Try Again
          </button>
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="p-6">
        <div className="flex items-center space-x-3">
          <Settings className="h-6 w-6 text-blue-600" />
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Configure Threat Analysis Agents
            </h2>
            <p className="text-gray-600">
              Select which AI agents will analyze your system for different types of threats
            </p>
          </div>
          {isStepComplete && (
            <CheckCircle className="h-6 w-6 text-green-500 ml-auto" />
          )}
        </div>
      </Card>

      {/* Agent Selection */}
      <div className="grid gap-4 md:grid-cols-1">
        {agents.map((agent) => {
          const isEnabled = enabledAgents.includes(agent.name)
          return (
            <Card
              key={agent.name}
              className={`p-4 cursor-pointer transition-all ${
                isEnabled 
                  ? 'border-blue-300 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => toggleAgent(agent.name)}
            >
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  <input
                    type="checkbox"
                    checked={isEnabled}
                    onChange={() => toggleAgent(agent.name)}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900 capitalize">
                    {agent.name.replace('_', ' ')} Agent
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {getAgentDescription(agent)}
                  </p>
                  <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                    <span>Category: {agent.category}</span>
                    <span>Est. tokens: {agent.estimated_tokens.toLocaleString()}</span>
                    <span>Priority: {agent.priority}</span>
                  </div>
                </div>
                <div className="flex-shrink-0">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    isEnabled 
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {isEnabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
              </div>
            </Card>
          )
        })}
      </div>

      {/* Summary and Continue */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Analysis Summary</h3>
            <p className="text-sm text-gray-600 mt-1">
              {enabledAgents.length} agents selected • ~{estimatedTokens.toLocaleString()} tokens estimated
            </p>
            {enabledAgents.length === 0 && (
              <p className="text-sm text-red-600 mt-1">
                Please select at least one agent to continue
              </p>
            )}
          </div>
          <div className="flex space-x-3">
            <button
              onClick={handleContinue}
              disabled={enabledAgents.length === 0}
              className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span>Continue to Threat Generation</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </Card>

      {/* Skip Option for Quick Testing */}
      <Card className="p-4 bg-gray-50">
        <div className="text-center">
          <p className="text-sm text-gray-600">
            Want to use all agents with default settings?
          </p>
          <button
            onClick={() => {
              setEnabledAgents(agents.filter(a => a.enabled_by_default).map(a => a.name))
              handleContinue()
            }}
            className="mt-2 text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Use Recommended Agents & Continue
          </button>
        </div>
      </Card>
    </div>
  )
}