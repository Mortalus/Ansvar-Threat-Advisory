'use client'

import { useState, useEffect } from 'react'
import { useStore } from '@/lib/store'
import { api, AgentInfo } from '@/lib/api'
import { Shield, Target, AlertCircle, CheckCircle, ArrowRight, Settings, PlayCircle, Zap, Clock, TrendingUp } from 'lucide-react'
import { Card } from '@/components/ui/card'

export function ThreatGenerationStep() {
  const {
    currentPipelineId,
    dfdComponents,
    selectedAgents,
    agentExecutionStatus,
    setStepStatus,
    setStepResult,
    setCurrentStep,
    stepStates,
    setAgentExecutionStatus,
    threats,
    setThreats,
  } = useStore()

  const [agents, setAgents] = useState<AgentInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [executionPhase, setExecutionPhase] = useState<'pending' | 'preparing' | 'executing' | 'complete' | 'error'>('pending')
  const [overallProgress, setOverallProgress] = useState(0)

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    try {
      // Defensive: Check if API is available
      if (!api || !api.getAvailableAgents) {
        console.warn('⚠️ Agent API not available, using cached data')
        return
      }
      
      const agentList = await api.getAvailableAgents()
      
      // Defensive: Validate response
      if (!agentList || !Array.isArray(agentList)) {
        console.warn('Invalid agent list response:', agentList)
        return
      }
      
      setAgents(agentList)
      console.log(`✅ Loaded ${agentList.length} agents for threat generation`)
    } catch (err) {
      console.error('❌ Failed to load agents for threat generation:', err)
      // Don't set error state here as it's not critical for threat generation
      // if agents were already selected in previous step
    }
  }

  // WebSocket connection for real-time agent progress
  useEffect(() => {
    if (!currentPipelineId || executionPhase !== 'executing') return

    const ws = api.connectWebSocket(currentPipelineId, {
      onMessage: (data) => {
        if (data.type === 'agent_progress') {
          setAgentExecutionStatus(data.agent_name, {
            status: data.status,
            progress: data.progress,
            threatsFound: data.threats_found,
            error: data.error
          })
          
          // Update overall progress
          const completedAgents = selectedAgents.filter(name => 
            agentExecutionStatus[name]?.status === 'completed'
          ).length + (data.status === 'completed' ? 1 : 0)
          
          setOverallProgress((completedAgents / selectedAgents.length) * 100)
        }
        
        if (data.type === 'threat_generation_complete') {
          setExecutionPhase('complete')
          setThreats(data.threats || [])
          setStepStatus('threat_generation', 'complete')
          setStepResult('threat_generation', data)
        }
      },
      onError: (error) => {
        console.error('WebSocket error:', error)
        setError('Connection lost during threat generation')
      }
    })

    return () => ws.close()
  }, [currentPipelineId, executionPhase, selectedAgents])

  const handleStartThreatGeneration = async () => {
    try {
      // Defensive: Comprehensive validation
      if (!currentPipelineId) {
        setError('Pipeline ID is missing. Please start from document upload.')
        return
      }
      
      if (!selectedAgents || selectedAgents.length === 0) {
        setError('No agents selected. Please go back to agent configuration.')
        return
      }
      
      // Defensive: Validate selected agents
      const validAgents = selectedAgents.filter(name => 
        name && typeof name === 'string' && name.length > 0
      )
      
      if (validAgents.length === 0) {
        setError('No valid agents selected. Please reconfigure agents.')
        return
      }
      
      if (validAgents.length !== selectedAgents.length) {
        console.warn('Some invalid agents filtered out:', selectedAgents)
      }

      console.log(`🚀 Starting threat generation with ${validAgents.length} agents:`, validAgents)
      
      setLoading(true)
      setError(null)
      setExecutionPhase('preparing')
      setStepStatus('threat_generation', 'in_progress')

      // Initialize agent statuses
      validAgents.forEach(agentName => {
        setAgentExecutionStatus(agentName, {
          status: 'pending',
          progress: 0,
          threatsFound: 0
        })
      })

      // Defensive: Check API availability
      if (!api || !api.generateThreats) {
        throw new Error('Threat generation API is not available')
      }

      setExecutionPhase('executing')
      
      // Call the API with timeout handling
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Request timed out after 5 minutes')), 300000)
      })
      
      const result = await Promise.race([
        api.generateThreats(currentPipelineId, validAgents),
        timeoutPromise
      ])
      
      // Defensive: Validate result structure
      if (!result || typeof result !== 'object') {
        throw new Error('Invalid response from threat generation API')
      }
      
      const threats = result.threats || []
      if (!Array.isArray(threats)) {
        console.warn('Invalid threats array in response:', threats)
        throw new Error('Invalid threats data received')
      }
      
      setThreats(threats)
      setStepStatus('threat_generation', 'complete')
      setStepResult('threat_generation', result)
      setExecutionPhase('complete')
      
      console.log(`✅ Threat generation completed. Found ${threats.length} threats.`)
      
    } catch (err) {
      console.error('❌ Threat generation failed:', err)
      const errorMessage = err instanceof Error ? err.message : 'Threat generation failed'
      const detailedError = `${errorMessage}. Check that all services are running and try again.`
      
      setError(detailedError)
      setStepStatus('threat_generation', 'error', detailedError)
      setExecutionPhase('error')
    } finally {
      setLoading(false)
    }
  }

  const getSelectedAgentDetails = () => {
    return agents.filter(agent => selectedAgents.includes(agent.name))
  }

  const getTotalEstimatedTokens = () => {
    return getSelectedAgentDetails().reduce((sum, agent) => sum + agent.estimated_tokens, 0)
  }

  const getAgentCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'architecture': 'border-blue-500/30 bg-blue-500/10',
      'business': 'border-green-500/30 bg-green-500/10',
      'compliance': 'border-purple-500/30 bg-purple-500/10',
      'technical': 'border-orange-500/30 bg-orange-500/10',
    }
    return colors[category] || 'border-gray-500/30 bg-gray-500/10'
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Clock className="w-4 h-4 text-gray-400" />
      case 'running': return <div className="w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed': return <AlertCircle className="w-4 h-4 text-red-500" />
      default: return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  // Check prerequisites
  if (stepStates.dfd_review.status !== 'complete') {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center p-8 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
          <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <p className="text-lg font-semibold mb-2">Prerequisites Required</p>
          <p className="text-gray-400 mb-4">
            Please complete DFD review and agent configuration before generating threats.
          </p>
          <button
            onClick={() => setCurrentStep('dfd_review')}
            className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all"
          >
            Go to DFD Review
          </button>
        </div>
      </div>
    )
  }

  // Check if agents are selected
  if (selectedAgents.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center p-8 bg-yellow-500/10 border border-yellow-500/30 rounded-xl max-w-md">
          <Settings className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <p className="text-lg font-semibold mb-2">Agents Required</p>
          <p className="text-gray-400 mb-4">
            Please select threat analysis agents before generating threats.
          </p>
          <button
            onClick={() => setCurrentStep('agent_config')}
            className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all"
          >
            Configure Agents
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="p-6">
        <div className="flex items-center space-x-3 mb-4">
          <Shield className="h-6 w-6 text-purple-600" />
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              AI-Powered Threat Generation
            </h2>
            <p className="text-gray-600">
              Using {selectedAgents.length} specialized AI agents to analyze your system
            </p>
          </div>
          {stepStates.threat_generation.status === 'complete' && (
            <CheckCircle className="h-6 w-6 text-green-500 ml-auto" />
          )}
        </div>

        {/* Agent Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{selectedAgents.length}</div>
            <div className="text-sm text-blue-800">Active Agents</div>
          </div>
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {getTotalEstimatedTokens().toLocaleString()}
            </div>
            <div className="text-sm text-purple-800">Est. Tokens</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {threats.length || 0}
            </div>
            <div className="text-sm text-green-800">Threats Found</div>
          </div>
        </div>
      </Card>

      {/* Execution Status */}
      {executionPhase !== 'pending' && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Execution Progress</h3>
            <div className="text-sm text-gray-600">
              {Math.round(overallProgress)}% complete
            </div>
          </div>
          
          <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
            <div
              className="bg-gradient-to-r from-purple-600 to-blue-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${overallProgress}%` }}
            />
          </div>

          <div className="grid gap-3">
            {getSelectedAgentDetails().map(agent => {
              const status = agentExecutionStatus[agent.name] || { status: 'pending', progress: 0, threatsFound: 0 }
              
              return (
                <div
                  key={agent.name}
                  className={`p-4 rounded-lg border ${getAgentCategoryColor(agent.category)} transition-all`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(status.status)}
                      <span className="font-medium capitalize">
                        {agent.name.replace('_', ' ')} Agent
                      </span>
                      <span className="text-sm text-gray-500">({agent.category})</span>
                    </div>
                    <div className="text-sm text-gray-600">
                      {status.threatsFound || 0} threats found
                    </div>
                  </div>
                  
                  {status.status === 'running' && (
                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                      <div
                        className="bg-purple-600 h-1.5 rounded-full transition-all duration-300"
                        style={{ width: `${status.progress || 0}%` }}
                      />
                    </div>
                  )}
                  
                  {status.error && (
                    <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                      {status.error}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </Card>
      )}

      {/* Action Section */}
      {executionPhase === 'pending' && (
        <Card className="p-6">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full gradient-purple-blue flex items-center justify-center mx-auto mb-4">
              <Target className="w-8 h-8 text-white" />
            </div>
            
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Ready for Threat Analysis
            </h3>
            
            <p className="text-gray-600 mb-6">
              Your selected agents will analyze the DFD components to identify potential security threats.
            </p>

            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Selected Agents:</h4>
              <div className="flex flex-wrap gap-2 justify-center">
                {getSelectedAgentDetails().map(agent => (
                  <span
                    key={agent.name}
                    className={`px-3 py-1 rounded-full text-sm ${getAgentCategoryColor(agent.category)} border`}
                  >
                    {agent.name.replace('_', ' ')} ({agent.estimated_tokens.toLocaleString()} tokens)
                  </span>
                ))}
              </div>
            </div>

            <button
              onClick={handleStartThreatGeneration}
              disabled={loading}
              className="flex items-center space-x-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-8 py-3 rounded-lg text-base font-medium disabled:opacity-50 disabled:cursor-not-allowed mx-auto"
            >
              <PlayCircle className="h-5 w-5" />
              <span>{loading ? 'Starting Analysis...' : 'Start Threat Generation'}</span>
            </button>
          </div>
        </Card>
      )}

      {/* Results */}
      {executionPhase === 'complete' && threats.length > 0 && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <CheckCircle className="h-6 w-6 text-green-500" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Threat Analysis Complete
                </h3>
                <p className="text-sm text-gray-600">
                  Found {threats.length} potential threats across your system
                </p>
              </div>
            </div>
            <button
              onClick={() => setCurrentStep('threat_refinement')}
              className="flex items-center space-x-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700"
            >
              <ArrowRight className="h-4 w-4" />
              <span>Refine Threats</span>
            </button>
          </div>

          {/* Quick Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {threats.filter(t => t['Potential Impact'] === 'High').length}
              </div>
              <div className="text-sm text-red-800">High Impact</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">
                {threats.filter(t => t['Potential Impact'] === 'Medium').length}
              </div>
              <div className="text-sm text-yellow-800">Medium Impact</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {threats.filter(t => t['Potential Impact'] === 'Low').length}
              </div>
              <div className="text-sm text-green-800">Low Impact</div>
            </div>
          </div>

          {/* Agent Performance Summary */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Agent Performance:</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {getSelectedAgentDetails().map(agent => {
                const status = agentExecutionStatus[agent.name]
                const agentThreats = threats.filter(t => 
                  t.metadata?.agent_name === agent.name
                ).length

                return (
                  <div
                    key={agent.name}
                    className="p-3 bg-gray-50 rounded-lg flex items-center justify-between"
                  >
                    <div>
                      <div className="font-medium text-sm">
                        {agent.name.replace('_', ' ')}
                      </div>
                      <div className="text-xs text-gray-600">
                        {agentThreats} threats found
                      </div>
                    </div>
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  </div>
                )
              })}
            </div>
          </div>
        </Card>
      )}

      {/* Error State */}
      {error && (
        <Card className="p-6 border-red-200 bg-red-50">
          <div className="flex items-center space-x-3">
            <AlertCircle className="h-6 w-6 text-red-500" />
            <div>
              <h3 className="text-lg font-semibold text-red-900">
                Threat Generation Failed
              </h3>
              <p className="text-red-700 mt-1">{error}</p>
            </div>
            <button
              onClick={handleStartThreatGeneration}
              className="ml-auto px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </Card>
      )}
    </div>
  )
}