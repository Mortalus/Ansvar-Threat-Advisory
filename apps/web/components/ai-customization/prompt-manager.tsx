'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ErrorBoundary } from '@/components/ui/error-boundary'
import { api } from '@/lib/api'
import { 
  Settings, 
  Edit3, 
  Save, 
  RefreshCw, 
  ChevronRight, 
  CheckCircle, 
  AlertCircle, 
  Eye,
  Wand2,
  Building2,
  Shield,
  FileText,
  Brain,
  Zap,
  ArrowLeft,
  Copy,
  Download
} from 'lucide-react'

interface LLMStep {
  step_name: string
  display_name: string
  description: string
  agents?: Array<{
    agent_type: string
    display_name: string
    description: string
    icon: string
  }>
  has_custom_prompt: boolean
  active_prompt_id?: string
}

interface PromptTemplate {
  id: string
  step_name: string
  agent_type?: string
  system_prompt: string
  description: string
  is_active: boolean
  created_at: string
  updated_at: string
}

interface IndustryTemplate {
  id: string
  name: string
  category: string
  description: string
  icon: string
  prompts: Array<{
    step_name: string
    agent_type?: string
    system_prompt: string
    description: string
  }>
}

export function PromptManager() {
  const [currentView, setCurrentView] = useState<'overview' | 'step' | 'editor'>('overview')
  const [selectedStep, setSelectedStep] = useState<LLMStep | null>(null)
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  
  const [llmSteps, setLlmSteps] = useState<LLMStep[]>([])
  const [promptTemplates, setPromptTemplates] = useState<PromptTemplate[]>([])
  const [industryTemplates, setIndustryTemplates] = useState<IndustryTemplate[]>([])
  
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPrompt, setCurrentPrompt] = useState('')
  const [currentDescription, setCurrentDescription] = useState('')

  // Load data from API
  useEffect(() => {
    loadLLMSteps()
    loadPromptTemplates()
  }, [])

  const loadLLMSteps = async () => {
    try {
      const steps = await api.getLLMSteps()
      // Ensure we have an array
      setLlmSteps(Array.isArray(steps) ? steps : mockLLMSteps)
    } catch (error) {
      console.error('Failed to load LLM steps:', error)
      // Fallback to mock data
      setLlmSteps(mockLLMSteps)
    }
  }

  const loadPromptTemplates = async () => {
    try {
      const templates = await api.getPromptTemplates()
      // Ensure we have an array
      setPromptTemplates(Array.isArray(templates) ? templates : [])
    } catch (error) {
      console.error('Failed to load prompt templates:', error)
      setPromptTemplates([])
    }
  }

  const loadActivePrompt = async (stepName: string, agentType?: string) => {
    try {
      const prompt = await api.getActivePrompt(stepName, agentType)
      setCurrentPrompt(prompt.system_prompt || '')
      setCurrentDescription(prompt.description || '')
    } catch (error) {
      console.error('Failed to load active prompt:', error)
      setCurrentPrompt('')
      setCurrentDescription('')
    }
  }

  const mockLLMSteps: LLMStep[] = [
    {
      step_name: 'dfd_extraction',
      display_name: 'DFD Extraction',
      description: 'Extract system components and data flows from documents',
      has_custom_prompt: false
    },
    {
      step_name: 'threat_generation',
      display_name: 'Threat Generation',
      description: 'Multi-agent threat analysis system',
      has_custom_prompt: true,
      agents: [
        {
          agent_type: 'architectural_risk',
          display_name: 'Architectural Risk Agent',
          description: 'Analyzes system architecture for structural vulnerabilities',
          icon: 'building'
        },
        {
          agent_type: 'business_financial',
          display_name: 'Business & Financial Agent', 
          description: 'Assesses business impact and financial risks',
          icon: 'dollar'
        },
        {
          agent_type: 'compliance_governance',
          display_name: 'Compliance & Governance Agent',
          description: 'Evaluates regulatory and compliance requirements',
          icon: 'shield'
        }
      ]
    },
    {
      step_name: 'threat_refinement',
      display_name: 'Threat Refinement',
      description: 'Risk assessment and threat prioritization',
      has_custom_prompt: false
    },
    {
      step_name: 'attack_path_analysis',
      display_name: 'Attack Path Analysis',
      description: 'Attack vector identification and analysis',
      has_custom_prompt: false
    }
  ]

  const mockIndustryTemplates: IndustryTemplate[] = [
    {
      id: 'fintech',
      name: 'Financial Services',
      category: 'Industry Vertical',
      description: 'PCI-DSS, SOX, and banking regulation focused analysis',
      icon: '🏦',
      prompts: [
        {
          step_name: 'threat_generation',
          agent_type: 'compliance_governance',
          system_prompt: 'You are a PCI-DSS Qualified Security Assessor (QSA) with expertise in banking regulations. Focus on cardholder data protection, PCI-DSS requirements, SOX controls for financial reporting, and regulatory requirements from OCC, FDIC, and Federal Reserve.',
          description: 'Financial services regulatory compliance focus'
        }
      ]
    },
    {
      id: 'healthcare',
      name: 'Healthcare & HIPAA',
      category: 'Industry Vertical',
      description: 'HIPAA, PHI protection, and healthcare compliance',
      icon: '🏥',
      prompts: [
        {
          step_name: 'threat_generation',
          agent_type: 'compliance_governance',
          system_prompt: 'You are a Senior Compliance Manager specializing in healthcare HIPAA requirements. Focus exclusively on PHI protection, BAA compliance, access controls for medical data, and healthcare-specific audit requirements.',
          description: 'Healthcare HIPAA-focused compliance analysis'
        }
      ]
    },
    {
      id: 'cloud_aws',
      name: 'AWS Cloud Architecture',
      category: 'Technology Focus',
      description: 'AWS security best practices and Well-Architected Framework',
      icon: '☁️',
      prompts: [
        {
          step_name: 'threat_generation',
          agent_type: 'architectural_risk',
          system_prompt: 'You are a Principal Solutions Architect at AWS with deep expertise in Well-Architected Framework security pillar. Focus on identifying architectural patterns that violate AWS security best practices, emphasizing IAM, network segmentation, and data protection patterns.',
          description: 'AWS-focused architectural risk analysis'
        }
      ]
    },
    {
      id: 'saas',
      name: 'Multi-Tenant SaaS',
      category: 'Technology Focus',
      description: 'SaaS-specific security patterns and tenant isolation',
      icon: '🔧',
      prompts: [
        {
          step_name: 'threat_generation',
          agent_type: 'architectural_risk', 
          system_prompt: 'You are a SaaS Security Architect specializing in multi-tenant applications. Focus on tenant isolation, API security, data segregation between customers, and SaaS-specific attack patterns like tenant enumeration and privilege escalation across organizations.',
          description: 'Multi-tenant SaaS security architecture focus'
        }
      ]
    }
  ]

  useEffect(() => {
    setLlmSteps(mockLLMSteps)
    setIndustryTemplates(mockIndustryTemplates)
  }, [])

  const getStepIcon = (stepName: string) => {
    const icons: Record<string, any> = {
      'dfd_extraction': FileText,
      'threat_generation': Shield,
      'threat_refinement': Brain,
      'attack_path_analysis': Zap
    }
    const IconComponent = icons[stepName] || Settings
    return <IconComponent className="w-5 h-5" />
  }

  const getAgentIcon = (iconType: string) => {
    const icons: Record<string, any> = {
      'building': Building2,
      'dollar': Brain,
      'shield': Shield
    }
    const IconComponent = icons[iconType] || Brain
    return <IconComponent className="w-5 h-5" />
  }

  const handleStepSelect = (step: LLMStep) => {
    setSelectedStep(step)
    setSelectedAgent(null)
    setCurrentView('step')
  }

  const handleAgentSelect = (agentType: string) => {
    setSelectedAgent(agentType)
    setCurrentView('editor')
    
    if (selectedStep) {
      loadActivePrompt(
        selectedStep.step_name, 
        agentType === 'main' ? undefined : agentType
      )
    }
  }

  const handleSavePrompt = async () => {
    if (!selectedStep || !currentPrompt.trim()) return
    
    setIsLoading(true)
    try {
      const data = {
        step_name: selectedStep.step_name,
        agent_type: selectedAgent === 'main' ? undefined : selectedAgent,
        system_prompt: currentPrompt,
        description: currentDescription,
        is_active: true
      }

      await api.createPromptTemplate(data)
      setError(null)
      
      // Reload data to reflect changes
      await loadLLMSteps()
      await loadPromptTemplates()
      
      setCurrentView('overview')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save prompt')
    } finally {
      setIsLoading(false)
    }
  }

  const handleApplyTemplate = async (template: IndustryTemplate) => {
    setIsLoading(true)
    try {
      for (const prompt of template.prompts) {
        await api.createPromptTemplate({
          ...prompt,
          is_active: true
        })
      }
      
      // Reload data
      await loadLLMSteps()
      await loadPromptTemplates()
      
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply template')
    } finally {
      setIsLoading(false)
    }
  }

  const handleResetToDefaults = async () => {
    setIsLoading(true)
    try {
      await api.initializeDefaultPrompts()
      
      // Reload data
      await loadLLMSteps()
      await loadPromptTemplates()
      
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset to defaults')
    } finally {
      setIsLoading(false)
    }
  }

  const renderOverview = () => (
    <div className="space-y-6">
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-4">
          <img src="/ansvar-logo.svg" alt="Ansvar" className="w-8 h-8" />
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Wand2 className="w-6 h-6 text-purple-500" />
              AI Customization
            </h2>
            <p className="text-sm text-purple-400">Powered by Ansvar Threat Advisory</p>
          </div>
        </div>
        <p className="text-gray-400">
          Customize how AI agents analyze your systems. Create industry-specific prompts to get more relevant threat analysis.
        </p>
      </div>

      {/* Status Overview */}
      <Card className="bg-[#1a1a2e] border-[#2a2a4a] p-6">
        <h3 className="text-lg font-semibold mb-4 text-white">Customization Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {llmSteps && llmSteps.length > 0 ? llmSteps.map((step) => (
            <div
              key={step.step_name}
              className="flex items-center justify-between p-4 rounded-lg bg-[#252541] hover:bg-[#2a2a4a] cursor-pointer transition-colors"
              onClick={() => handleStepSelect(step)}
            >
              <div className="flex items-center gap-3">
                {getStepIcon(step.step_name)}
                <div>
                  <p className="font-medium text-white">{step.display_name}</p>
                  <p className="text-sm text-gray-400">{step.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {step.has_custom_prompt ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : (
                  <div className="w-5 h-5 rounded-full border-2 border-gray-600" />
                )}
                <ChevronRight className="w-4 h-4 text-gray-500" />
              </div>
            </div>
          )) : (
            <div className="col-span-2 text-center py-8 text-gray-400">
              <p>Loading customization options...</p>
            </div>
          )}
        </div>
      </Card>

      {/* Industry Templates */}
      <Card className="bg-[#1a1a2e] border-[#2a2a4a] p-6">
        <h3 className="text-lg font-semibold mb-4 text-white">Industry Templates</h3>
        <p className="text-gray-400 mb-6">Get started quickly with pre-built prompts for your industry or technology stack.</p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {industryTemplates && industryTemplates.length > 0 ? industryTemplates.map((template) => (
            <div key={template.id} className="p-4 rounded-lg bg-[#252541] hover:bg-[#2a2a4a] cursor-pointer transition-colors">
              <div className="flex items-start gap-3 mb-3">
                <span className="text-2xl">{template.icon}</span>
                <div className="flex-1">
                  <h4 className="font-semibold text-white">{template.name}</h4>
                  <p className="text-xs text-purple-400 mb-2">{template.category}</p>
                  <p className="text-sm text-gray-400">{template.description}</p>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">
                  {template.prompts.length} prompts included
                </span>
                <Button 
                  size="sm" 
                  className="bg-purple-600 hover:bg-purple-700 text-white"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleApplyTemplate(template)
                  }}
                  disabled={isLoading}
                >
                  {isLoading ? 'Applying...' : 'Apply Template'}
                </Button>
              </div>
            </div>
          )) : (
            <div className="col-span-2 text-center py-8 text-gray-400">
              <p>Loading industry templates...</p>
            </div>
          )}
        </div>
      </Card>

      {/* Quick Actions */}
      <Card className="bg-[#1a1a2e] border-[#2a2a4a] p-6">
        <h3 className="text-lg font-semibold mb-4 text-white">Quick Actions</h3>
        <div className="flex flex-wrap gap-3">
          <Button 
            variant="outline" 
            className="border-purple-500/30 text-purple-400 hover:bg-purple-500/10"
            onClick={handleResetToDefaults}
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Reset to Defaults
          </Button>
          <Button 
            variant="outline" 
            className="border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
            onClick={() => {
              // TODO: Implement export functionality
              console.log('Export functionality coming soon')
            }}
          >
            <Download className="w-4 h-4 mr-2" />
            Export Settings
          </Button>
          <Button 
            variant="outline" 
            className="border-green-500/30 text-green-400 hover:bg-green-500/10"
            onClick={() => {
              // TODO: Implement preview mode
              console.log('Preview mode coming soon')
            }}
          >
            <Eye className="w-4 h-4 mr-2" />
            Preview Mode
          </Button>
        </div>
      </Card>
    </div>
  )

  const renderStepView = () => {
    if (!selectedStep) return null

    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4 mb-6">
          <Button
            variant="ghost"
            onClick={() => setCurrentView('overview')}
            className="text-gray-400 hover:text-white p-0"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-3">
              {getStepIcon(selectedStep.step_name)}
              {selectedStep.display_name}
            </h2>
            <p className="text-gray-400">{selectedStep.description}</p>
          </div>
        </div>

        {selectedStep.agents ? (
          <Card className="bg-[#1a1a2e] border-[#2a2a4a] p-6">
            <h3 className="text-lg font-semibold mb-4 text-white">Select AI Agent to Customize</h3>
            <div className="space-y-3">
              {selectedStep.agents && selectedStep.agents.length > 0 ? selectedStep.agents.map((agent) => (
                <div
                  key={agent.agent_type}
                  className="flex items-center justify-between p-4 rounded-lg bg-[#252541] hover:bg-[#2a2a4a] cursor-pointer transition-colors"
                  onClick={() => handleAgentSelect(agent.agent_type)}
                >
                  <div className="flex items-center gap-3">
                    {getAgentIcon(agent.icon)}
                    <div>
                      <p className="font-medium text-white">{agent.display_name}</p>
                      <p className="text-sm text-gray-400">{agent.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 rounded-full border-2 border-gray-600" />
                    <ChevronRight className="w-4 h-4 text-gray-500" />
                  </div>
                </div>
              )) : (
                <div className="text-center py-8 text-gray-400">
                  <p>No agents available for customization</p>
                </div>
              )}
            </div>
          </Card>
        ) : (
          <Card className="bg-[#1a1a2e] border-[#2a2a4a] p-6">
            <div className="text-center py-8">
              <Edit3 className="w-16 h-16 text-purple-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Customize This Step</h3>
              <p className="text-gray-400 mb-6">
                Create a custom prompt to improve how the AI analyzes your {selectedStep.display_name.toLowerCase()}.
              </p>
              <Button 
                className="bg-purple-600 hover:bg-purple-700 text-white"
                onClick={() => handleAgentSelect('main')}
              >
                <Edit3 className="w-4 h-4 mr-2" />
                Customize Prompt
              </Button>
            </div>
          </Card>
        )}
      </div>
    )
  }

  const renderEditor = () => (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <Button
          variant="ghost" 
          onClick={() => setCurrentView('step')}
          className="text-gray-400 hover:text-white p-0"
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h2 className="text-2xl font-bold">Prompt Editor</h2>
          <p className="text-gray-400">
            {selectedStep?.display_name} 
            {selectedAgent && selectedAgent !== 'main' && ` → ${selectedAgent}`}
          </p>
        </div>
      </div>

      <Card className="bg-[#1a1a2e] border-[#2a2a4a] p-6">
        <h3 className="text-lg font-semibold mb-4 text-white">System Prompt</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Description
            </label>
            <input
              type="text"
              value={currentDescription}
              onChange={(e) => setCurrentDescription(e.target.value)}
              className="w-full px-3 py-2 bg-[#252541] border border-[#2a2a4a] rounded-lg text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none"
              placeholder="Brief description of this custom prompt..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Prompt Content
            </label>
            <textarea
              value={currentPrompt}
              onChange={(e) => setCurrentPrompt(e.target.value)}
              rows={12}
              className="w-full px-3 py-2 bg-[#252541] border border-[#2a2a4a] rounded-lg text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none font-mono text-sm"
              placeholder="You are an expert security analyst specializing in..."
            />
          </div>
        </div>

        <div className="flex items-center justify-between mt-6 pt-4 border-t border-[#2a2a4a]">
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Eye className="w-4 h-4 mr-2" />
              Preview
            </Button>
            <Button variant="outline" size="sm">
              <Copy className="w-4 h-4 mr-2" />
              Copy from Template
            </Button>
          </div>
          
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              onClick={() => setCurrentView('step')}
            >
              Cancel
            </Button>
            <Button 
              className="bg-purple-600 hover:bg-purple-700 text-white"
              onClick={handleSavePrompt}
              disabled={isLoading || !currentPrompt.trim()}
            >
              <Save className="w-4 h-4 mr-2" />
              {isLoading ? 'Saving...' : 'Save & Activate'}
            </Button>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-400">{error}</span>
          </div>
        )}
      </Card>
    </div>
  )

  const renderCurrentView = () => {
    switch (currentView) {
      case 'overview':
        return renderOverview()
      case 'step':
        return renderStepView()
      case 'editor':
        return renderEditor()
      default:
        return renderOverview()
    }
  }

  return (
    <ErrorBoundary>
      <div className="h-full flex flex-col">
        {renderCurrentView()}
      </div>
    </ErrorBoundary>
  )
}