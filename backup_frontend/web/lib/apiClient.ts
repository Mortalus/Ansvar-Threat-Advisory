/**
 * Unified API Client - Single Source of Truth for Backend Communication
 * 
 * Solves: API routing mismatch, contract drift, hardcoded endpoints
 * Pattern: All frontend API calls go through this centralized client
 */

// Phase 2: Gateway-based routing (same origin through reverse proxy)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '';

console.log('🔌 API Client configured with base URL:', API_BASE_URL || '[same-origin via gateway]');

// Request wrapper with consistent error handling
async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const requestId = crypto.randomUUID();
  
  console.log(`🚀 [${requestId}] API Request: ${options.method || 'GET'} ${url}`);
  
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId,
        ...options.headers,
      },
      ...options,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`✅ [${requestId}] API Success:`, data);
    return data;
  } catch (error) {
    console.error(`❌ [${requestId}] API Error:`, error);
    throw error;
  }
}

// Centralized API endpoints (contracts defined in one place)
export const apiClient = {
  // System Health
  health: () => apiRequest('/health'),
  
  // Projects API (using working endpoints)
  projects: {
    list: () => apiRequest<Array<any>>('/api/projects-simple/'),
    health: () => apiRequest<{status: string, projects_count: number}>('/api/projects-simple/health'),
    createTest: () => apiRequest('/api/projects-simple/test', { method: 'POST' }),
  },
  
  // Pipeline Operations
  pipeline: {
    create: () => apiRequest('/api/pipeline/create', { method: 'POST' }),
    getStatus: (pipelineId: string) => apiRequest(`/api/pipeline/${pipelineId}/status`),
    executeStep: (pipelineId: string, step: string) => 
      apiRequest(`/api/pipeline/${pipelineId}/step/${step}`, { method: 'POST' }),
    cancel: (pipelineId: string) => 
      apiRequest(`/api/pipeline/${pipelineId}/cancel`, { method: 'POST' }),
    list: (params?: string) => apiRequest(`/api/pipeline/list${params || ''}`),
  },
  
  // Document Operations  
  documents: {
    upload: (formData: FormData) => apiRequest('/api/documents/upload', {
      method: 'POST',
      body: formData,
      headers: {} // Let browser set multipart headers
    }),
    extractData: (pipelineId: string) => 
      apiRequest(`/api/documents/extract-data`, {
        method: 'POST',
        body: JSON.stringify({ pipeline_id: pipelineId })
      }),
    extractDFD: (pipelineId: string) => 
      apiRequest(`/api/documents/extract-dfd`, {
        method: 'POST', 
        body: JSON.stringify({ pipeline_id: pipelineId })
      }),
    generateThreats: (pipelineId: string) => 
      apiRequest(`/api/documents/generate-threats`, {
        method: 'POST',
        body: JSON.stringify({ pipeline_id: pipelineId })
      }),
    refineThreats: (pipelineId: string) => 
      apiRequest(`/api/documents/refine-threats`, {
        method: 'POST',
        body: JSON.stringify({ pipeline_id: pipelineId })
      }),
  },
  
  // Debug/Development endpoints
  debug: {
    sampleDFD: () => apiRequest('/api/debug/sample-dfd'),
    sampleThreats: () => apiRequest('/api/debug/sample-threats'), 
    quickRefine: () => apiRequest('/api/debug/quick-refine', { method: 'POST' }),
  },
  
  // LLM Operations
  llm: {
    testProvider: (provider: string) => 
      apiRequest(`/api/llm/test/${provider}`, { method: 'POST' }),
    getProviders: () => apiRequest('/api/llm/providers'),
  },
  
  // Settings
  settings: {
    getLLMSteps: () => apiRequest('/api/settings/llm-steps'),
    getPrompts: () => apiRequest('/api/settings/prompts'),
    updatePrompts: (prompts: any) => 
      apiRequest('/api/settings/prompts', {
        method: 'PUT',
        body: JSON.stringify(prompts)
      }),
  }
};

// Export types for better development experience
export type ApiClient = typeof apiClient;
export type ProjectsResponse = Awaited<ReturnType<typeof apiClient.projects.list>>;
export type HealthResponse = Awaited<ReturnType<typeof apiClient.projects.health>>;

console.log('📋 API Client initialized with endpoints:', Object.keys(apiClient));