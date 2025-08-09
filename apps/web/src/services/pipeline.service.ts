import { apiClient } from './api.client';
import { websocketService } from './websocket.service';
import { z } from 'zod';

// Validation schemas
const pipelineConfigSchema = z.object({
  step1_enabled: z.boolean().default(true),
  step2_enabled: z.boolean().default(true),
  step3_enabled: z.boolean().default(true),
  step4_enabled: z.boolean().default(true),
  step5_enabled: z.boolean().default(true),
  temperature: z.number().min(0).max(2).default(0.7),
  max_tokens: z.number().min(100).max(4000).default(2000),
  provider: z.enum(['azure', 'scaleway', 'ollama']).default('scaleway'),
});

const pipelineStatusSchema = z.object({
  pipeline_id: z.string(),
  status: z.enum(['pending', 'running', 'completed', 'failed', 'cancelled']),
  current_step: z.number().optional(),
  total_steps: z.number().optional(),
  progress: z.number().min(0).max(100).optional(),
  message: z.string().optional(),
  error: z.string().optional(),
  results: z.any().optional(),
  started_at: z.string().optional(),
  completed_at: z.string().optional(),
});

const dfdDataSchema = z.object({
  elements: z.array(z.object({
    id: z.string(),
    type: z.enum(['process', 'external_entity', 'data_store', 'data_flow']),
    name: z.string(),
    description: z.string().optional(),
    properties: z.record(z.any()).optional(),
  })),
  trust_boundaries: z.array(z.object({
    id: z.string(),
    name: z.string(),
    elements: z.array(z.string()),
  })).optional(),
  metadata: z.record(z.any()).optional(),
});

const threatSchema = z.object({
  id: z.string(),
  category: z.enum(['Spoofing', 'Tampering', 'Repudiation', 'Information Disclosure', 'Denial of Service', 'Elevation of Privilege']),
  threat: z.string(),
  description: z.string(),
  impact: z.enum(['Low', 'Medium', 'High', 'Critical']),
  likelihood: z.enum(['Low', 'Medium', 'High']),
  risk_score: z.number().min(1).max(10),
  affected_elements: z.array(z.string()),
  mitigations: z.array(z.string()),
  cwe_id: z.string().optional(),
  owasp_category: z.string().optional(),
});

export type PipelineConfig = z.infer<typeof pipelineConfigSchema>;
export type PipelineStatus = z.infer<typeof pipelineStatusSchema>;
export type DFDData = z.infer<typeof dfdDataSchema>;
export type Threat = z.infer<typeof threatSchema>;

interface StartPipelineData {
  project_id: string;
  session_id: string;
  document_id?: string;
  config?: Partial<PipelineConfig>;
}

interface PipelineResults {
  dfd_data?: DFDData;
  threats?: Threat[];
  report?: string;
  metadata?: Record<string, any>;
}

class PipelineService {
  private statusCallbacks = new Map<string, (status: PipelineStatus) => void>();

  constructor() {
    this.setupWebSocketListeners();
  }

  /**
   * Setup WebSocket event listeners for pipeline updates
   */
  private setupWebSocketListeners(): void {
    websocketService.on('pipeline:update', (data: any) => {
      try {
        const status = pipelineStatusSchema.parse(data);
        const callback = this.statusCallbacks.get(status.pipeline_id);
        if (callback) {
          callback(status);
        }
      } catch (error) {
        console.error('Invalid pipeline status update:', error);
      }
    });

    websocketService.on('pipeline:complete', (data: any) => {
      try {
        const status = pipelineStatusSchema.parse({
          ...data,
          status: 'completed',
          progress: 100,
        });
        const callback = this.statusCallbacks.get(status.pipeline_id);
        if (callback) {
          callback(status);
          this.statusCallbacks.delete(status.pipeline_id);
        }
      } catch (error) {
        console.error('Invalid pipeline complete event:', error);
      }
    });

    websocketService.on('pipeline:error', (data: any) => {
      const pipelineId = data.pipeline_id;
      const callback = this.statusCallbacks.get(pipelineId);
      if (callback) {
        callback({
          pipeline_id: pipelineId,
          status: 'failed',
          error: data.error || 'Pipeline failed',
          progress: 0,
        });
        this.statusCallbacks.delete(pipelineId);
      }
    });
  }

  /**
   * Start a new pipeline execution
   */
  async startPipeline(data: StartPipelineData): Promise<PipelineStatus> {
    try {
      // Validate input
      const validated = z.object({
        project_id: z.string().uuid(),
        session_id: z.string().uuid(),
        document_id: z.string().uuid().optional(),
        config: pipelineConfigSchema.partial().optional(),
      }).parse(data);

      // Ensure WebSocket is connected
      if (!websocketService.connected) {
        await websocketService.connect();
      }

      const response = await apiClient.post<PipelineStatus>('/api/pipeline/start', validated);
      const status = pipelineStatusSchema.parse(response);

      // Register for updates
      if (status.pipeline_id) {
        this.registerStatusCallback(status.pipeline_id, (update) => {
          console.log('Pipeline update:', update);
        });
      }

      return status;
    } catch (error: any) {
      console.error('Failed to start pipeline:', error);
      
      if (error instanceof z.ZodError) {
        throw new Error(error.errors[0].message);
      }
      
      throw error;
    }
  }

  /**
   * Get pipeline status
   */
  async getPipelineStatus(pipelineId: string): Promise<PipelineStatus> {
    try {
      const response = await apiClient.get<PipelineStatus>(`/api/pipeline/${pipelineId}/status`);
      return pipelineStatusSchema.parse(response);
    } catch (error: any) {
      console.error(`Failed to get pipeline status ${pipelineId}:`, error);
      throw error;
    }
  }

  /**
   * Cancel running pipeline
   */
  async cancelPipeline(pipelineId: string): Promise<void> {
    try {
      await apiClient.post(`/api/pipeline/${pipelineId}/cancel`);
      
      // Clean up callback
      this.statusCallbacks.delete(pipelineId);
    } catch (error: any) {
      console.error(`Failed to cancel pipeline ${pipelineId}:`, error);
      throw error;
    }
  }

  /**
   * Get pipeline results
   */
  async getPipelineResults(pipelineId: string): Promise<PipelineResults> {
    try {
      const response = await apiClient.get<PipelineResults>(`/api/pipeline/${pipelineId}/results`);
      
      // Validate results
      const results: PipelineResults = {};
      
      if (response.dfd_data) {
        results.dfd_data = dfdDataSchema.parse(response.dfd_data);
      }
      
      if (response.threats) {
        results.threats = response.threats.map((threat: any) => threatSchema.parse(threat));
      }
      
      results.report = response.report;
      results.metadata = response.metadata;
      
      return results;
    } catch (error: any) {
      console.error(`Failed to get pipeline results ${pipelineId}:`, error);
      throw error;
    }
  }

  /**
   * Retry failed pipeline step
   */
  async retryPipelineStep(pipelineId: string, stepNumber: number): Promise<PipelineStatus> {
    try {
      const response = await apiClient.post<PipelineStatus>(
        `/api/pipeline/${pipelineId}/retry`,
        { step: stepNumber }
      );
      
      return pipelineStatusSchema.parse(response);
    } catch (error: any) {
      console.error(`Failed to retry pipeline step ${stepNumber}:`, error);
      throw error;
    }
  }

  /**
   * Export pipeline results
   */
  async exportPipelineResults(
    pipelineId: string,
    format: 'json' | 'pdf' | 'docx' = 'pdf'
  ): Promise<Blob> {
    try {
      const response = await apiClient.get<Blob>(
        `/api/pipeline/${pipelineId}/export`,
        {
          params: { format },
          responseType: 'blob',
        }
      );
      
      return response;
    } catch (error: any) {
      console.error(`Failed to export pipeline results ${pipelineId}:`, error);
      throw error;
    }
  }

  /**
   * Get pipeline history
   */
  async getPipelineHistory(projectId?: string, limit: number = 50): Promise<PipelineStatus[]> {
    try {
      const params: any = { limit };
      if (projectId) {
        params.project_id = projectId;
      }

      const response = await apiClient.get<PipelineStatus[]>('/api/pipeline/history', { params });
      return response.map(status => pipelineStatusSchema.parse(status));
    } catch (error: any) {
      console.error('Failed to get pipeline history:', error);
      throw error;
    }
  }

  /**
   * Validate pipeline configuration
   */
  validateConfig(config: any): PipelineConfig {
    try {
      return pipelineConfigSchema.parse(config);
    } catch (error) {
      if (error instanceof z.ZodError) {
        throw new Error(`Invalid configuration: ${error.errors[0].message}`);
      }
      throw error;
    }
  }

  /**
   * Register callback for pipeline status updates
   */
  registerStatusCallback(pipelineId: string, callback: (status: PipelineStatus) => void): void {
    this.statusCallbacks.set(pipelineId, callback);
  }

  /**
   * Unregister callback for pipeline status updates
   */
  unregisterStatusCallback(pipelineId: string): void {
    this.statusCallbacks.delete(pipelineId);
  }

  /**
   * Submit feedback for a threat
   */
  async submitThreatFeedback(
    threatId: string,
    feedback: {
      is_valid: boolean;
      severity_adjustment?: 'increase' | 'decrease' | 'none';
      comments?: string;
    }
  ): Promise<void> {
    try {
      await apiClient.post(`/api/threats/${threatId}/feedback`, feedback);
    } catch (error: any) {
      console.error(`Failed to submit threat feedback:`, error);
      throw error;
    }
  }
}

export const pipelineService = new PipelineService();