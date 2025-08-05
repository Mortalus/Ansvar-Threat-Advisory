const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = {
  createPipeline: async () => {
    const response = await fetch(`${API_URL}/api/pipeline/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    return response.json()
  },

  executeStep: async (pipelineId: string, step: string, data?: any) => {
    const response = await fetch(`${API_URL}/api/pipeline/${pipelineId}/step/${step}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input_data: data }),
    })
    return response.json()
  },

  uploadDocument: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await fetch(`${API_URL}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    })
    return response.json()
  },
}
