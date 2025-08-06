const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Log API URL for debugging
console.log('API_URL configured as:', API_URL)

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
      throw new Error('Cannot connect to server. Please ensure the backend is running on port 8000.')
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

async function extractDFDComponents(pipelineId: string): Promise<{
  pipeline_id: string
  dfd_components: DFDComponents
  validation: any
  status: string
}> {
  const response = await fetch(`${API_URL}/api/documents/extract-dfd`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pipeline_id: pipelineId
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

async function generateThreats(pipelineId: string): Promise<ThreatGenerationResponse> {
  const response = await fetch(`${API_URL}/api/documents/generate-threats`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pipeline_id: pipelineId })
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Threat generation failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
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
  const response = await fetch(`${API_URL}/api/pipeline/${pipelineId}/step/${step}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data || {})
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Step execution failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
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
  const wsURL = API_URL.replace('http', 'ws')
  const ws = new WebSocket(`${wsURL}/ws/${pipelineId}`)

  ws.onopen = () => {
    console.log('WebSocket connected for pipeline:', pipelineId)
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

// Export API object with all methods
export const api = {
  // Document methods
  uploadDocuments,
  uploadDocument,  // Legacy support
  getSampleDFD,
  extractDFDComponents,
  reviewDFDComponents,
  generateThreats,
  
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
}