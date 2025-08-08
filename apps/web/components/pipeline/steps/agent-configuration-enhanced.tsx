'use client'

import { useState, useEffect } from 'react'
import { useStore } from '@/lib/store'
import { api, AgentInfo } from '@/lib/api'
import { Card } from '@/components/ui/card'
import { 
  Settings, 
  Zap, 
  CheckCircle, 
  ArrowRight, 
  Shield,
  Building,
  Scale,
  AlertTriangle,
  Activity,
  Info,
  XCircle,
  RefreshCw,
  Loader2,
  ChevronDown,
  ChevronUp,
  Star,
  TrendingUp,
  Clock,
  FileText,
  Layers
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface AgentHealthStatus {
  is_healthy: boolean
  reliability_score: number
  success_rate: number
  average_response_time: number
  circuit_breaker_state: string
  last_error?: string
}

interface EnhancedAgentInfo extends AgentInfo {
  health?: AgentHealthStatus
  isExpanded?: boolean
}

// Agent category icons and colors
const categoryConfig = {
  architecture: {
    icon: Layers,
    color: 'text-blue-400',
    bgColor: 'bg-blue-400/10',
    borderColor: 'border-blue-400/20',
    description: 'Analyzes system architecture and design vulnerabilities'
  },
  business: {
    icon: Building,
    color: 'text-green-400',
    bgColor: 'bg-green-400/10',
    borderColor: 'border-green-400/20',
    description: 'Evaluates business and financial risks'
  },
  compliance: {
    icon: Scale,
    color: 'text-purple-400',
    bgColor: 'bg-purple-400/10',
    borderColor: 'border-purple-400/20',
    description: 'Ensures regulatory and compliance requirements'
  }
}

export function AgentConfigurationEnhanced() {
  const {
    currentPipelineId,
    dfdComponents,
    setStepStatus,
    setCurrentStep,
    stepStates,
  } = useStore()

  const [agents, setAgents] = useState<EnhancedAgentInfo[]>([])
  const [enabledAgents, setEnabledAgents] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [healthLoading, setHealthLoading] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set())
  const [autoSelectRecommended, setAutoSelectRecommended] = useState(true)

  useEffect(() => {
    loadAgents()
  }, [])

  useEffect(() => {
    // Load health status after agents are loaded
    if (agents.length > 0 && !healthLoading) {
      loadHealthStatus()
    }
  }, [agents])

  const loadAgents = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const agentList = await api.getAvailableAgents()
      
      if (!agentList || !Array.isArray(agentList)) {
        throw new Error('Invalid agent data received from server')
      }
      
      // Enhance agent info with UI state
      const enhancedAgents: EnhancedAgentInfo[] = agentList.map(agent => ({
        ...agent,
        isExpanded: false
      }))
      
      setAgents(enhancedAgents)
      
      // Auto-select recommended agents if enabled
      if (autoSelectRecommended) {
        const recommended = enhancedAgents
          .filter(agent => agent.enabled_by_default || agent.priority <= 10)
          .map(agent => agent.name)
        
        setEnabledAgents(recommended)
      }
      
    } catch (err) {
      console.error('Failed to load agents:', err)
      setError('Unable to load agents. Please check backend services.')
      setAgents([])
    } finally {
      setLoading(false)
    }
  }

  const loadHealthStatus = async () => {
    try {
      setHealthLoading(true)
      
      // Load health status for each agent
      const healthPromises = agents.map(async (agent) => {
        try {
          const response = await fetch(`/api/agents/${agent.name}/health`)
          if (response.ok) {
            return { name: agent.name, health: await response.json() }
          }
          return null
        } catch {
          return null
        }
      })
      
      const healthResults = await Promise.allSettled(healthPromises)
      
      // Update agents with health data
      const updatedAgents = agents.map(agent => {
        const healthResult = healthResults.find(
          r => r.status === 'fulfilled' && r.value?.name === agent.name
        )
        
        if (healthResult?.status === 'fulfilled' && healthResult.value) {
          return { ...agent, health: healthResult.value.health }
        }
        
        // Default health status if not available
        return {
          ...agent,
          health: {
            is_healthy: true,
            reliability_score: 95,
            success_rate: 98,
            average_response_time: 2.5,
            circuit_breaker_state: 'closed'
          }
        }
      })
      
      setAgents(updatedAgents)
      
    } catch (err) {
      console.warn('Could not load health status:', err)
    } finally {
      setHealthLoading(false)
    }
  }

  const toggleAgent = (agentName: string) => {
    setEnabledAgents(prev => 
      prev.includes(agentName)
        ? prev.filter(name => name !== agentName)
        : [...prev, agentName]
    )
  }

  const toggleAgentExpansion = (agentName: string) => {
    setExpandedAgents(prev => {
      const newSet = new Set(prev)
      if (newSet.has(agentName)) {
        newSet.delete(agentName)
      } else {
        newSet.add(agentName)
      }
      return newSet
    })
  }

  const selectAllInCategory = (category: string) => {
    const categoryAgents = agents
      .filter(a => a.category === category)
      .map(a => a.name)
    
    setEnabledAgents(prev => {
      const newSet = new Set(prev)
      categoryAgents.forEach(name => newSet.add(name))
      return Array.from(newSet)
    })
  }

  const deselectAllInCategory = (category: string) => {
    const categoryAgents = agents
      .filter(a => a.category === category)
      .map(a => a.name)
    
    setEnabledAgents(prev => 
      prev.filter(name => !categoryAgents.includes(name))
    )
  }

  const handleContinue = () => {
    if (!enabledAgents || enabledAgents.length === 0) {
      setError('Please select at least one agent to continue')
      return
    }
    
    // Store selected agents
    useStore.setState({ selectedAgents: enabledAgents })
    
    // Mark step as complete and continue
    setStepStatus('agent_config', 'complete')
    setCurrentStep('threat_generation')
  }

  const getHealthIcon = (health?: AgentHealthStatus) => {
    if (!health) return null
    
    if (health.circuit_breaker_state === 'open') {
      return <XCircle className="w-4 h-4 text-red-400" />
    }
    
    if (health.reliability_score >= 90) {
      return <CheckCircle className="w-4 h-4 text-green-400" />
    } else if (health.reliability_score >= 70) {
      return <AlertTriangle className="w-4 h-4 text-yellow-400" />
    } else {
      return <XCircle className="w-4 h-4 text-red-400" />
    }
  }

  const getHealthColor = (score: number) => {
    if (score >= 90) return 'text-green-400'
    if (score >= 70) return 'text-yellow-400'
    return 'text-red-400'
  }

  // Group agents by category
  const agentsByCategory = agents.reduce((acc, agent) => {
    if (!acc[agent.category]) {
      acc[agent.category] = []
    }
    acc[agent.category].push(agent)
    return acc
  }, {} as Record<string, EnhancedAgentInfo[]>)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
        <span className="ml-3 text-gray-400">Loading available agents...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Settings className="w-6 h-6 text-purple-400" />
            Configure Threat Analysis Agents
          </h2>
          <p className="text-gray-400 mt-2">
            Select specialized agents to analyze your system from different perspectives
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={loadAgents}
            className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors"
            title="Refresh agents"
          >
            <RefreshCw className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Error Display */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-red-500/10 border border-red-500/20 rounded-lg p-4"
          >
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5" />
              <div className="flex-1">
                <p className="text-red-400">{error}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Quick Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-gray-800/50 border-gray-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Available</p>
              <p className="text-2xl font-bold text-white">{agents.length}</p>
            </div>
            <Layers className="w-8 h-8 text-purple-400 opacity-50" />
          </div>
        </Card>
        
        <Card className="bg-gray-800/50 border-gray-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Selected</p>
              <p className="text-2xl font-bold text-white">{enabledAgents.length}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-400 opacity-50" />
          </div>
        </Card>
        
        <Card className="bg-gray-800/50 border-gray-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Est. Time</p>
              <p className="text-2xl font-bold text-white">
                {Math.ceil(enabledAgents.length * 15)}s
              </p>
            </div>
            <Clock className="w-8 h-8 text-blue-400 opacity-50" />
          </div>
        </Card>
        
        <Card className="bg-gray-800/50 border-gray-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Est. Tokens</p>
              <p className="text-2xl font-bold text-white">
                {agents
                  .filter(a => enabledAgents.includes(a.name))
                  .reduce((sum, a) => sum + (a.estimated_tokens || 5000), 0)
                  .toLocaleString()}
              </p>
            </div>
            <Zap className="w-8 h-8 text-yellow-400 opacity-50" />
          </div>
        </Card>
      </div>

      {/* Agent Categories */}
      <div className="space-y-4">
        {Object.entries(agentsByCategory).map(([category, categoryAgents]) => {
          const config = categoryConfig[category as keyof typeof categoryConfig]
          const Icon = config?.icon || Shield
          const enabledInCategory = categoryAgents.filter(a => 
            enabledAgents.includes(a.name)
          ).length
          
          return (
            <motion.div
              key={category}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-3"
            >
              {/* Category Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${config?.bgColor}`}>
                    <Icon className={`w-5 h-5 ${config?.color}`} />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white capitalize">
                      {category} Agents
                    </h3>
                    <p className="text-sm text-gray-400">
                      {config?.description}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-400">
                    {enabledInCategory}/{categoryAgents.length} selected
                  </span>
                  <button
                    onClick={() => selectAllInCategory(category)}
                    className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-gray-600 text-gray-300"
                  >
                    Select All
                  </button>
                  <button
                    onClick={() => deselectAllInCategory(category)}
                    className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-gray-600 text-gray-300"
                  >
                    Clear
                  </button>
                </div>
              </div>

              {/* Agents in Category */}
              <div className="grid gap-3">
                {categoryAgents.map((agent) => {
                  const isEnabled = enabledAgents.includes(agent.name)
                  const isExpanded = expandedAgents.has(agent.name)
                  
                  return (
                    <motion.div
                      key={agent.name}
                      layout
                      className={`
                        border rounded-lg transition-all cursor-pointer
                        ${isEnabled 
                          ? `${config?.borderColor} ${config?.bgColor} border-2` 
                          : 'border-gray-700 bg-gray-800/30 hover:bg-gray-800/50'
                        }
                      `}
                    >
                      {/* Agent Main Info */}
                      <div
                        className="p-4"
                        onClick={() => toggleAgent(agent.name)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3 flex-1">
                            <div className={`
                              w-10 h-10 rounded-lg flex items-center justify-center
                              ${isEnabled ? config?.bgColor : 'bg-gray-700'}
                            `}>
                              <Icon className={`w-5 h-5 ${isEnabled ? config?.color : 'text-gray-400'}`} />
                            </div>
                            
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <h4 className="font-semibold text-white">
                                  {agent.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </h4>
                                {agent.version && (
                                  <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-400">
                                    v{agent.version}
                                  </span>
                                )}
                                {agent.enabled_by_default && (
                                  <span className="text-xs px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-400 flex items-center gap-1">
                                    <Star className="w-3 h-3" />
                                    Recommended
                                  </span>
                                )}
                                {getHealthIcon(agent.health)}
                              </div>
                              
                              <p className="text-sm text-gray-400 mt-1">
                                {agent.description}
                              </p>
                              
                              {/* Quick Stats */}
                              <div className="flex items-center gap-4 mt-2">
                                <div className="flex items-center gap-1">
                                  <Activity className="w-3 h-3 text-gray-500" />
                                  <span className={`text-xs ${getHealthColor(agent.health?.reliability_score || 95)}`}>
                                    {agent.health?.reliability_score?.toFixed(0) || 95}% reliable
                                  </span>
                                </div>
                                <div className="flex items-center gap-1">
                                  <Clock className="w-3 h-3 text-gray-500" />
                                  <span className="text-xs text-gray-400">
                                    ~{agent.health?.average_response_time?.toFixed(1) || '2.5'}s
                                  </span>
                                </div>
                                <div className="flex items-center gap-1">
                                  <Zap className="w-3 h-3 text-gray-500" />
                                  <span className="text-xs text-gray-400">
                                    ~{(agent.estimated_tokens || 5000).toLocaleString()} tokens
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                toggleAgentExpansion(agent.name)
                              }}
                              className="p-1 rounded hover:bg-gray-700 transition-colors"
                            >
                              {isExpanded ? (
                                <ChevronUp className="w-4 h-4 text-gray-400" />
                              ) : (
                                <ChevronDown className="w-4 h-4 text-gray-400" />
                              )}
                            </button>
                            
                            <div className={`
                              w-6 h-6 rounded-full border-2 flex items-center justify-center
                              ${isEnabled 
                                ? 'bg-purple-500 border-purple-400' 
                                : 'border-gray-600 hover:border-gray-500'
                              }
                            `}>
                              {isEnabled && (
                                <CheckCircle className="w-4 h-4 text-white" />
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Expanded Details */}
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="border-t border-gray-700 overflow-hidden"
                          >
                            <div className="p-4 space-y-3">
                              {/* Requirements */}
                              <div>
                                <h5 className="text-sm font-medium text-gray-300 mb-2">Requirements</h5>
                                <div className="flex gap-2">
                                  {agent.requires_document && (
                                    <span className="text-xs px-2 py-1 rounded bg-gray-700 text-gray-400 flex items-center gap-1">
                                      <FileText className="w-3 h-3" />
                                      Document
                                    </span>
                                  )}
                                  {agent.requires_components && (
                                    <span className="text-xs px-2 py-1 rounded bg-gray-700 text-gray-400 flex items-center gap-1">
                                      <Layers className="w-3 h-3" />
                                      DFD Components
                                    </span>
                                  )}
                                </div>
                              </div>
                              
                              {/* Health Details */}
                              {agent.health && (
                                <div>
                                  <h5 className="text-sm font-medium text-gray-300 mb-2">Performance Metrics</h5>
                                  <div className="grid grid-cols-2 gap-2">
                                    <div className="bg-gray-800 rounded p-2">
                                      <p className="text-xs text-gray-500">Success Rate</p>
                                      <p className={`text-sm font-medium ${getHealthColor(agent.health.success_rate)}`}>
                                        {agent.health.success_rate.toFixed(1)}%
                                      </p>
                                    </div>
                                    <div className="bg-gray-800 rounded p-2">
                                      <p className="text-xs text-gray-500">Avg Response</p>
                                      <p className="text-sm font-medium text-white">
                                        {agent.health.average_response_time.toFixed(2)}s
                                      </p>
                                    </div>
                                  </div>
                                  
                                  {agent.health.last_error && (
                                    <div className="mt-2 p-2 bg-red-500/10 rounded">
                                      <p className="text-xs text-red-400">
                                        Last Error: {agent.health.last_error}
                                      </p>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  )
                })}
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Continue Button */}
      <div className="flex justify-end gap-3 pt-4">
        <button
          onClick={() => setCurrentStep('dfd_review')}
          className="px-6 py-3 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition-colors"
        >
          Back
        </button>
        
        <button
          onClick={handleContinue}
          disabled={enabledAgents.length === 0}
          className={`
            px-6 py-3 rounded-lg font-medium transition-all flex items-center gap-2
            ${enabledAgents.length > 0
              ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600'
              : 'bg-gray-700 text-gray-500 cursor-not-allowed'
            }
          `}
        >
          Continue to Threat Generation
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}