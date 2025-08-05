// apps/web/lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = {
  // Pipeline management
  createPipeline: async (name: string) => {
    const response = await fetch(`${API_URL}/api/pipelines`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name }),
    })
    
    if (!response.ok) {
      throw new Error('Failed to create pipeline')
    }
    
    return response.json()
  },

  getPipeline: async (pipelineId: string) => {
    const response = await fetch(`${API_URL}/api/pipelines/${pipelineId}`)
    
    if (!response.ok) {
      throw new Error('Failed to get pipeline')
    }
    
    return response.json()
  },

  // Step execution
  executeStep: async (pipelineId: string, step: string, inputData: any) => {
    const response = await fetch(`${API_URL}/api/pipelines/${pipelineId}/steps/${step}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ step, input_data: inputData }),
    })
    
    if (!response.ok) {
      const error = await response.text()
      throw new Error(error || 'Failed to execute step')
    }
    
    return response.json()
  },

  // Document upload (if using separate endpoint)
  uploadDocument: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await fetch(`${API_URL}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    })
    
    if (!response.ok) {
      throw new Error('Failed to upload document')
    }
    
    return response.json()
  },

  // Run full pipeline
  runPipeline: async (pipelineId: string, documentData: any) => {
    const response = await fetch(`${API_URL}/api/pipelines/${pipelineId}/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(documentData),
    })
    
    if (!response.ok) {
      throw new Error('Failed to run pipeline')
    }
    
    return response.json()
  },

  // WebSocket connection for real-time updates
  connectWebSocket: (pipelineId: string) => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${pipelineId}`)
    
    ws.onopen = () => {
      console.log('WebSocket connected')
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    return ws
  },

  // LLM Provider validation
  validateProvider: async (provider: string, config: any) => {
    const response = await fetch(`${API_URL}/api/llm/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ provider, config }),
    })
    
    if (!response.ok) {
      throw new Error('Provider validation failed')
    }
    
    return response.json()
  },
}