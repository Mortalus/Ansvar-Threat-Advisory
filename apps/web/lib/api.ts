import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const api = {
  // Pipeline management
  createPipeline: async () => {
    const response = await client.post('/api/pipeline/create')
    return response.data
  },

  getPipelineStatus: async (pipelineId: string) => {
    const response = await client.get(`/api/pipeline/${pipelineId}/status`)
    return response.data
  },

  executeStep: async (pipelineId: string, step: string, data?: any) => {
    const response = await client.post(
      `/api/pipeline/${pipelineId}/step/${step}`,
      { input_data: data }
    )
    return response.data
  },

  validateStep: async (pipelineId: string, step: string) => {
    const response = await client.post(`/api/pipeline/${pipelineId}/validate/${step}`)
    return response.data
  },

  // Document management
  uploadDocument: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await client.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  getSupportedFormats: async () => {
    const response = await client.get('/api/documents/supported-formats')
    return response.data
  },
}