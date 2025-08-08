// Phase 2: Gateway-based routing - use same-origin through NGINX reverse proxy
const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || ''

// Log API URL for debugging
console.log('API_URL configured as:', API_URL || '[same-origin via gateway]')

export interface DFDComponents {
  project_name: string
  project_version: string
  industry_context: string
  external_entities: string[]
  assets: string[]
  processes: string[]
  trust_boundaries: string[]
  data_flows: DataFlow[]
}

export interface DataFlow {
  source: string
  destination: string
  data_description: string
  data_classification: string
  protocol: string
  authentication_mechanism: string
}

export interface UploadResponse {
  pipeline_id?: string
  files: FileInfo[]
  text_length: number
  dfd_components?: DFDComponents
  token_estimate?: {
    estimated_tokens: number
    model_basis: string
    discrete_summary: string
  }
  status: string
  error?: string
}

export interface FileInfo {
  filename: string
  size: number
  content_type: string
}

export interface PipelineStatus {
  id: string
  status: string
  current_step: string | null
  created_at: string
  updated_at: string
  steps: Record<string, StepStatus>
  metadata: Record<string, any>
}

export interface StepStatus {
  status: string
  started_at: string | null
  completed_at: string | null
  result: any | null
  error: string | null
}

export interface Threat {
  "Threat Category": string
  "Threat Name": string
  "Description": string
  "Potential Impact": string
  "Likelihood": string
  "Suggested Mitigation": string
  component_id: string
  component_name: string
  component_type: string
}

export interface ThreatGenerationResponse {
  pipeline_id: string
  threats: Threat[]
  total_count: number
  components_analyzed: number
  knowledge_sources_used: string[]
  generated_at: string
  status: string
}

export interface ThreatRefinementResponse {
  pipeline_id: string
  refined_threats: RefinedThreat[]
  total_count: number
  refinement_stats: {
    original_count: number
    deduplicated_count: number
    final_count: number
    risk_distribution: Record<string, number>
    refinement_timestamp: string
  }
  refined_at: string
  status: string
}

export interface RefinedThreat extends Threat {
  // Enhanced fields from refinement
  risk_score?: string
  business_risk_statement?: string
  financial_impact_range?: string
  regulatory_implications?: string
  stakeholder_impact?: string
  business_continuity_impact?: string
  primary_mitigation?: string
  secondary_mitigations?: string[]
  implementation_priority?: string
  estimated_effort?: string
  success_metrics?: string
  compliance_alignment?: string
  priority_score?: number
  priority_ranking?: string
  priority_rank?: number
  exploitability?: string
  assessment_reasoning?: string
  business_impact_description?: string
  mitigation_maturity?: string
  merged_from?: string[]
}

// Document endpoints
async function uploadDocuments(files: File[]): Promise<UploadResponse> {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })

  try {
    console.log('Uploading to:', `${API_URL}/api/documents/upload`)
    const response = await fetch(`${API_URL}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      console.error('Upload failed with status:', response.status, error)
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    
    return response.json()
  } catch (error) {
    console.error('Network error during upload:', error)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to server. Please ensure the gateway is running.')
    }
    throw error
  }
}

async function uploadDocument(file: File): Promise<any> {
  // Legacy single file upload - redirects to multi-file upload
  return uploadDocuments([file])
}

async function getSampleDFD(): Promise<DFDComponents> {
  const response = await fetch(`${API_URL}/api/documents/sample`)
  
  if (!response.ok) {
    throw new Error(`Failed to get sample DFD: ${response.status}`)
  }
  
  return response.json()
}

async function extractStrideData(pipelineId: string, options: {
  enable_quality_validation?: boolean
} = {}): Promise<{
  pipeline_id: string
  extracted_security_data: any
  extraction_metadata: any
  quality_score?: number
  completeness_indicators?: any
  status: string
}> {
  console.log('Extracting STRIDE data for pipeline:', pipelineId)
  
  const response = await fetch(`${API_URL}/api/documents/extract-data`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      pipeline_id: pipelineId,
      enable_quality_validation: options.enable_quality_validation ?? true
    }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`STRIDE data extraction failed: ${response.status} ${errorText}`)
  }

  const result = await response.json()
  console.log('STRIDE data extraction result:', result)
  return result
}

async function extractDFDComponents(pipelineId: string): Promise<{
  pipeline_id: string
  dfd_components: DFDComponents
  validation: any
  status: string
  quality_report?: {
    enhancement_enabled: boolean
    token_usage?: {
      total_tokens: number
      total_cost_usd: number
      model_name: string
    }
    quality_summary?: {
      overall_quality_score: number
      components_added: number
      improvement_percentage: string
    }
    extraction_time_seconds: number
    confidence_analysis?: any
    security_analysis?: any
  }
}> {
  const response = await fetch(`${API_URL}/api/documents/extract-dfd`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pipeline_id: pipelineId,
      background: false,
      use_enhanced_extraction: true,
      enable_stride_review: true,
      enable_confidence_scoring: true,
      enable_security_validation: true
    })
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'DFD extraction failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

async function reviewDFDComponents(pipelineId: string, dfdComponents: DFDComponents): Promise<{
  pipeline_id: string
  dfd_components: DFDComponents
  status: string
  reviewed_at: string
}> {
  const response = await fetch(`${API_URL}/api/documents/review-dfd`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pipeline_id: pipelineId,
      dfd_components: dfdComponents
    })
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'DFD review failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

async function generateThreats(
  pipelineId: string, 
  selectedAgents?: string[]
): Promise<ThreatGenerationResponse> {
  const response = await fetch(`${API_URL}/api/documents/generate-threats`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      pipeline_id: pipelineId,
      use_v2_generator: false,
      context_aware: true,
      use_v3_generator: true,
      multi_agent: true,
      selected_agents: selectedAgents || []
    })
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Threat generation failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

async function refineThreats(pipelineId: string): Promise<ThreatRefinementResponse> {
  const response = await fetch(`${API_URL}/api/documents/refine-threats`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pipeline_id: pipelineId })
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Threat refinement failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

// Debug mode functions
async function quickRefineThreats(): Promise<ThreatRefinementResponse> {
  const response = await fetch(`${API_URL}/api/debug/quick-refine`, {
    method: 'POST',
  })
  
  if (!response.ok) {
    throw new Error(`Debug refinement failed: ${response.status}`)
  }
  
  return response.json()
}

async function getDebugSampleDFD(): Promise<any> {
  const response = await fetch(`${API_URL}/api/debug/sample-dfd`)
  
  if (!response.ok) {
    throw new Error(`Failed to get sample DFD: ${response.status}`)
  }
  
  return response.json()
}

async function getSampleThreats(): Promise<any> {
  const response = await fetch(`${API_URL}/api/debug/sample-threats`)
  
  if (!response.ok) {
    throw new Error(`Failed to get sample threats: ${response.status}`)
  }
  
  return response.json()
}

// Pipeline endpoints
async function createPipeline(metadata?: any): Promise<any> {
  const response = await fetch(`${API_URL}/api/pipeline/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ metadata })
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to create pipeline' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

async function executeStep(pipelineId: string, step: string, data?: any): Promise<any> {
  // Format the request to match the new backend ExecuteStepRequest model
  const requestBody = {
    background: false,
    data: data || {},
    // Flatten any additional fields from data to the top level
    ...data
  }
  
  console.log('🔧 Executing pipeline step:', step, 'for pipeline:', pipelineId, 'with data:', requestBody)
  
  const response = await fetch(`${API_URL}/api/pipeline/${pipelineId}/step/${step}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody)
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Step execution failed' }))
    console.error('Pipeline step execution failed:', error)
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  const result = await response.json()
  console.log('✅ Pipeline step completed:', result)
  return result
}

async function getPipelineStatus(pipelineId: string): Promise<PipelineStatus> {
  const response = await fetch(`${API_URL}/api/pipeline/${pipelineId}/status`)
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get status' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

async function cancelPipeline(pipelineId: string): Promise<{ success: boolean }> {
  const response = await fetch(`${API_URL}/api/pipeline/${pipelineId}/cancel`, {
    method: 'POST',
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to cancel' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

async function listPipelines(status?: string): Promise<PipelineStatus[]> {
  const params = status ? `?status=${status}` : ''
  const response = await fetch(`${API_URL}/api/pipeline/list${params}`)
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to list pipelines' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

// WebSocket connection for real-time updates
function connectWebSocket(pipelineId: string, handlers: {
  onMessage?: (data: any) => void
  onError?: (error: Event) => void
  onClose?: () => void
}): WebSocket {
  // Phase 2: WebSocket through NGINX gateway  
  const wsBaseUrl = process.env.NEXT_PUBLIC_WS_BASE_URL || ''
  let wsURL = wsBaseUrl
  
  // Smart gateway routing: Always use port 80 for WebSocket (the main gateway port)
  if (!wsURL && typeof window !== 'undefined') {
    const hostname = window.location.hostname
    wsURL = `ws://${hostname}` // Always use port 80 (default) for WebSocket through gateway
  }
  
  // Fallback for server-side rendering
  if (!wsURL) {
    wsURL = 'ws://localhost'
  }
  
  const ws = new WebSocket(`${wsURL}/ws/${pipelineId}`)

  ws.onopen = () => {
    console.log('WebSocket connected for pipeline:', pipelineId, 'via', wsURL)
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handlers.onMessage?.(data)
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }

  ws.onerror = handlers.onError || ((error) => {
    console.error('WebSocket error:', error)
  })

  ws.onclose = handlers.onClose || (() => {
    console.log('WebSocket closed')
  })

  return ws
}

// LLM provider endpoints
async function testLLMProvider(provider: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_URL}/api/llm/test/${provider}`, {
    method: 'POST',
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Test failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

async function getLLMProviders(): Promise<string[]> {
  const response = await fetch(`${API_URL}/api/llm/providers`)
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get providers' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

// Health check
async function healthCheck(): Promise<{ status: string; timestamp: string }> {
  const response = await fetch(`${API_URL}/health`)
  
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`)
  }
  
  return response.json()
}

// Prompt Management API
async function getLLMSteps() {
  try {
    const response = await fetch(`${API_URL}/api/settings/llm-steps`)
    if (!response.ok) {
      console.warn(`LLM steps endpoint returned ${response.status}`)
      return []
    }
    const data = await response.json()
    return Array.isArray(data) ? data : []
  } catch (error) {
    console.warn('LLM steps endpoint not available:', error)
    return []
  }
}

async function getPromptTemplates() {
  try {
    const response = await fetch(`${API_URL}/api/settings/prompts`)
    if (!response.ok) {
      console.warn(`Prompt templates endpoint returned ${response.status}`)
      return []
    }
    const data = await response.json()
    return Array.isArray(data) ? data : []
  } catch (error) {
    console.warn('Prompt templates endpoint not available:', error)
    return []
  }
}

async function getActivePrompt(stepName: string, agentType?: string) {
  try {
    const url = agentType 
      ? `${API_URL}/api/settings/prompts/active/${stepName}?agent_type=${agentType}`
      : `${API_URL}/api/settings/prompts/active/${stepName}`
    const response = await fetch(url)
    if (!response.ok) {
      console.warn(`Active prompt endpoint returned ${response.status}`)
      return { system_prompt: '', description: '' }
    }
    return response.json()
  } catch (error) {
    console.warn('Active prompt endpoint not available:', error)
    return { system_prompt: '', description: '' }
  }
}

async function createPromptTemplate(data: {
  step_name: string
  agent_type?: string
  system_prompt: string
  description: string
  is_active?: boolean
}) {
  const response = await fetch(`${API_URL}/api/settings/prompts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  if (!response.ok) throw new Error('Failed to create prompt template')
  return response.json()
}

async function updatePromptTemplate(id: string, data: {
  system_prompt?: string
  description?: string
  is_active?: boolean
}) {
  const response = await fetch(`${API_URL}/api/settings/prompts/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  if (!response.ok) throw new Error('Failed to update prompt template')
  return response.json()
}

async function deletePromptTemplate(id: string) {
  const response = await fetch(`${API_URL}/api/settings/prompts/${id}`, {
    method: 'DELETE'
  })
  if (!response.ok) throw new Error('Failed to delete prompt template')
  return response.json()
}

async function initializeDefaultPrompts() {
  const response = await fetch(`${API_URL}/api/settings/prompts/initialize-defaults`, {
    method: 'POST'
  })
  if (!response.ok) throw new Error('Failed to initialize default prompts')
  return response.json()
}

// Admin Management API Functions
async function getSystemPrompts() {
  const response = await fetch(`${API_URL}/api/settings/prompts`)
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get system prompts' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

async function updateSystemPrompt(id: string, data: {
  prompt_text: string
  step_name: string
  agent_type?: string | null
}) {
  const response = await fetch(`${API_URL}/api/settings/prompts/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to update system prompt' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

// Agent Management API Types
export interface AgentInfo {
  name: string
  version: string
  description: string
  category: string
  priority: number
  requires_document: boolean
  requires_components: boolean
  estimated_tokens: number
  enabled: boolean  // Backend uses 'enabled', not 'enabled_by_default'
  enabled_by_default?: boolean  // Computed field for compatibility
  legacy_equivalent?: string
  current_config?: any
  class_name?: string  // Optional since backend doesn't always provide it
  metrics?: {
    total_executions: number
    success_rate: number
    avg_threats: number
    avg_execution_time: number
    total_tokens_used: number
    last_executed: string | null
  }
}

export interface AgentConfiguration {
  agent_name: string
  enabled: boolean
  priority: number
  custom_prompt?: string
  max_tokens: number
  temperature: number
  rate_limit_per_hour?: number
  concurrent_limit?: number
  total_executions?: number
  successful_executions?: number
  total_threats_found?: number
  total_tokens_used?: number
  average_execution_time?: number
  average_confidence_score?: number
  last_executed?: string
  last_modified?: string
}

export interface AgentExecutionLog {
  agent_name: string
  execution_id: string
  executed_at: string
  execution_time: number
  success: boolean
  error_message?: string
  threats_found?: number
  tokens_used?: number
  average_confidence?: number
}

export interface AgentTestResult {
  status: string  // Backend returns 'status', not boolean success
  success?: boolean  // Computed field for compatibility
  agent: string   // Backend uses 'agent', not 'agent_name'
  agent_name?: string  // Computed field for compatibility
  execution_time: number
  threats_found: number  // Backend uses 'threats_found', not 'threats_generated' 
  threats_generated?: number  // Computed field for compatibility
  average_confidence: number
  estimated_tokens: number
  threats_sample: any[]
  context_info?: {
    document_length: number
    components_count: number
  }
  error_message?: string
}

// Agent Management API Functions
async function getAvailableAgents(): Promise<AgentInfo[]> {
  try {
    // Defensive: Add timeout to prevent hanging requests
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout
    
    const response = await fetch(`${API_URL}/api/agents/list`, {
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      }
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      let errorDetail = 'Failed to get available agents'
      try {
        const error = await response.json()
        errorDetail = error.detail || error.message || `HTTP ${response.status}: ${response.statusText}`
      } catch (parseError) {
        console.warn('Failed to parse error response:', parseError)
        errorDetail = `HTTP ${response.status}: ${response.statusText}`
      }
      throw new Error(errorDetail)
    }
    
    const data = await response.json()
    
    // Defensive: Validate response structure
    if (!data || typeof data !== 'object') {
      throw new Error('Invalid response format from agents API')
    }
    
    const agents = data.agents || []
    
    // Defensive: Validate agents array
    if (!Array.isArray(agents)) {
      console.warn('Invalid agents array in response:', agents)
      return []
    }
    
    // Defensive: Filter out invalid agents
    const validAgents = agents.filter(agent => 
      agent && 
      typeof agent === 'object' &&
      agent.name && 
      typeof agent.name === 'string' &&
      agent.description &&
      agent.category
    )
    
    if (validAgents.length !== agents.length) {
      console.warn(`Filtered out ${agents.length - validAgents.length} invalid agents`)
    }
    
    // Map backend fields to frontend expectations
    const mappedAgents = validAgents.map(agent => ({
      ...agent,
      enabled_by_default: agent.enabled, // Map 'enabled' to 'enabled_by_default'
      class_name: agent.class_name || `${agent.name.charAt(0).toUpperCase()}${agent.name.slice(1).replace('_', '')}Agent` // Generate class_name if missing
    }))
    
    console.log(`✅ Loaded ${mappedAgents.length} valid agents`)
    return mappedAgents
    
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('Request timed out. Please check your connection and try again.')
    }
    
    console.error('Failed to fetch available agents:', error)
    
    // Rethrow with more context
    const message = error instanceof Error ? error.message : 'Unknown error occurred'
    throw new Error(`Unable to load agents: ${message}`)
  }
}

async function getAgentConfiguration(agentName: string): Promise<AgentConfiguration> {
  try {
    const response = await fetch(`${API_URL}/api/agents/${agentName}/config`)
    if (!response.ok) {
      // If endpoint doesn't exist, return default configuration
      if (response.status === 404) {
        console.warn(`Agent configuration endpoint not found for ${agentName}, returning default config`)
        return {
          agent_name: agentName,
          enabled: true,
          priority: 100,
          max_tokens: 4000,
          temperature: 0.7
        }
      }
      const error = await response.json().catch(() => ({ detail: 'Failed to get agent configuration' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    return response.json()
  } catch (error) {
    console.warn(`Failed to get agent configuration for ${agentName}, returning default:`, error)
    return {
      agent_name: agentName,
      enabled: true,
      priority: 100,
      max_tokens: 4000,
      temperature: 0.7
    }
  }
}

async function updateAgentConfiguration(
  agentName: string, 
  config: Partial<AgentConfiguration>
): Promise<AgentConfiguration> {
  try {
    const response = await fetch(`${API_URL}/api/agents/${agentName}/config`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    })
    if (!response.ok) {
      if (response.status === 404) {
        console.warn(`Agent configuration update endpoint not implemented for ${agentName}`)
        // Return the config as-is since we can't actually update it
        return { agent_name: agentName, ...config } as AgentConfiguration
      }
      const error = await response.json().catch(() => ({ detail: 'Failed to update agent configuration' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    return response.json()
  } catch (error) {
    console.warn(`Agent configuration update failed for ${agentName}, returning mock response:`, error)
    return { agent_name: agentName, ...config } as AgentConfiguration
  }
}

async function testAgent(
  agentName: string, 
  testData: {
    sample_document?: string
    sample_components?: any
    use_mock_llm?: boolean
    custom_prompt?: string
  } = {}
): Promise<AgentTestResult> {
  const response = await fetch(`${API_URL}/api/agents/${agentName}/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(testData)
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Agent test failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  const result = await response.json()
  
  // Map backend response to frontend expectations
  return {
    ...result,
    success: result.status === 'success',
    agent_name: result.agent,
    threats_generated: result.threats_found
  }
}

async function getAgentExecutionHistory(
  agentName: string, 
  limit: number = 50
): Promise<AgentExecutionLog[]> {
  const response = await fetch(`${API_URL}/api/agents/${agentName}/history?limit=${limit}`)
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get execution history' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

async function getAgentPerformanceStats(agentName: string): Promise<{
  total_executions: number
  successful_executions: number
  success_rate: number
  average_execution_time: number
  average_threats_per_execution: number
  average_confidence_score: number
  total_tokens_used: number
  last_30_days: {
    executions: number
    success_rate: number
  }
}> {
  const response = await fetch(`${API_URL}/api/agents/${agentName}/performance`)
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get performance stats' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

async function reloadAgentConfiguration(agentName: string): Promise<{ success: boolean; message: string }> {
  try {
    const response = await fetch(`${API_URL}/api/agents/${agentName}/reload`, {
      method: 'POST'
    })
    if (!response.ok) {
      if (response.status === 404) {
        console.warn(`Agent reload endpoint not implemented for ${agentName}`)
        return { success: true, message: `Agent ${agentName} reload not supported (endpoint not implemented)` }
      }
      const error = await response.json().catch(() => ({ detail: 'Failed to reload agent' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    return response.json()
  } catch (error) {
    console.warn(`Agent reload failed for ${agentName}:`, error)
    return { success: true, message: `Mock reload for ${agentName} (backend not implemented)` }
  }
}

// Task Management API Functions for Async Operations
async function executeStepInBackground(
  pipelineId: string, 
  stepName: string, 
  data: any = {}
): Promise<{ task_id: string; status: string }> {
  const response = await fetch(`${API_URL}/api/tasks/execute-step`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pipeline_id: pipelineId,
      step_name: stepName,
      ...data
    })
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to start background task' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

async function getTaskStatus(taskId: string): Promise<{
  task_id: string
  status: string
  result?: any
  error?: string
  progress?: number
}> {
  const response = await fetch(`${API_URL}/api/tasks/status/${taskId}`)
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get task status' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

async function listActiveTasks(): Promise<Array<{
  task_id: string
  name: string
  status: string
  started_at: string
  pipeline_id?: string
}>> {
  const response = await fetch(`${API_URL}/api/tasks/list`)
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to list tasks' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

// Export API object with all methods
export const api = {
  // Document methods
  uploadDocuments,
  uploadDocument,  // Legacy support
  getSampleDFD,
  extractStrideData,
  extractDFDComponents,
  reviewDFDComponents,
  generateThreats,
  refineThreats,
  
  // Pipeline methods
  createPipeline,
  executeStep,
  getPipelineStatus,
  cancelPipeline,
  listPipelines,
  
  // WebSocket
  connectWebSocket,
  
  // LLM methods
  testLLMProvider,
  getLLMProviders,
  
  // Health
  healthCheck,
  
  // Prompt Management
  getLLMSteps,
  getPromptTemplates,
  getActivePrompt,
  createPromptTemplate,
  updatePromptTemplate,
  deletePromptTemplate,
  initializeDefaultPrompts,
  
  // Agent Management
  listAgents: getAvailableAgents,  // Alias for consistency
  getAvailableAgents,
  getAgentConfiguration,
  updateAgentConfiguration,
  testAgent,
  getAgentExecutionHistory,
  getAgentPerformanceStats,
  reloadAgentConfiguration,
  
  // Admin Management
  getSystemPrompts,
  updateSystemPrompt,
  
  // Async Task Management
  executeStepInBackground,
  getTaskStatus,
  listActiveTasks,
  
  // Debug functions
  quickRefineThreats,
  getDebugSampleDFD,
  getSampleThreats,
}