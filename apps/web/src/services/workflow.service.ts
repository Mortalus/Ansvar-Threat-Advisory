import { apiClient } from './api.client';
import { websocketService } from './websocket.service';
import { z } from 'zod';

// Validation schemas
const workflowStepSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.enum(['agent', 'condition', 'parallel', 'loop', 'transform']),
  agent_id: z.string().optional(),
  config: z.record(z.any()).optional(),
  inputs: z.array(z.string()).optional(),
  outputs: z.array(z.string()).optional(),
  conditions: z.array(z.object({
    field: z.string(),
    operator: z.enum(['equals', 'not_equals', 'contains', 'greater_than', 'less_than']),
    value: z.any(),
  })).optional(),
  next_steps: z.array(z.string()).optional(),
});

const workflowSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().optional(),
  steps: z.array(workflowStepSchema),
  is_template: z.boolean().default(false),
  is_active: z.boolean().default(true),
  created_by: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  metadata: z.record(z.any()).optional(),
});

const workflowExecutionSchema = z.object({
  id: z.string(),
  workflow_id: z.string(),
  status: z.enum(['pending', 'running', 'completed', 'failed', 'paused', 'cancelled']),
  started_at: z.string(),
  completed_at: z.string().optional(),
  total_steps: z.number(),
  completed_steps: z.number(),
  current_step: z.string().optional(),
  error_message: z.string().optional(),
  results: z.any().optional(),
  metadata: z.record(z.any()).optional(),
});

const executionStepSchema = z.object({
  id: z.string(),
  execution_id: z.string(),
  step_id: z.string(),
  agent_id: z.string().optional(),
  name: z.string(),
  status: z.enum(['pending', 'running', 'completed', 'failed', 'skipped']),
  started_at: z.string().optional(),
  completed_at: z.string().optional(),
  input_data: z.any().optional(),
  output_data: z.any().optional(),
  error_message: z.string().optional(),
  token_usage: z.object({
    prompt_tokens: z.number(),
    completion_tokens: z.number(),
    total_tokens: z.number(),
  }).optional(),
  confidence: z.number().min(0).max(1).optional(),
  step_order: z.number(),
});

export type WorkflowStep = z.infer<typeof workflowStepSchema>;
export type Workflow = z.infer<typeof workflowSchema>;
export type WorkflowExecution = z.infer<typeof workflowExecutionSchema>;
export type ExecutionStep = z.infer<typeof executionStepSchema>;

interface CreateWorkflowData {
  name: string;
  description?: string;
  steps: WorkflowStep[];
  is_template?: boolean;
}

interface ExecuteWorkflowData {
  workflow_id: string;
  input_data?: any;
  context_sources?: string[];
}

class WorkflowService {
  private executionCallbacks = new Map<string, (execution: WorkflowExecution) => void>();

  constructor() {
    this.setupWebSocketListeners();
  }

  /**
   * Setup WebSocket event listeners for workflow updates
   */
  private setupWebSocketListeners(): void {
    websocketService.on('workflow:progress', (data: any) => {
      try {
        const execution = workflowExecutionSchema.parse(data);
        const callback = this.executionCallbacks.get(execution.id);
        if (callback) {
          callback(execution);
        }
      } catch (error) {
        console.error('Invalid workflow progress update:', error);
      }
    });

    websocketService.on('workflow:complete', (data: any) => {
      try {
        const execution = workflowExecutionSchema.parse({
          ...data,
          status: 'completed',
        });
        const callback = this.executionCallbacks.get(execution.id);
        if (callback) {
          callback(execution);
          this.executionCallbacks.delete(execution.id);
        }
      } catch (error) {
        console.error('Invalid workflow complete event:', error);
      }
    });

    websocketService.on('workflow:error', (data: any) => {
      const executionId = data.execution_id;
      const callback = this.executionCallbacks.get(executionId);
      if (callback) {
        callback({
          ...data,
          status: 'failed',
          error_message: data.error || 'Workflow failed',
        });
        this.executionCallbacks.delete(executionId);
      }
    });
  }

  /**
   * Get all workflows
   */
  async getWorkflows(includeTemplates: boolean = true): Promise<Workflow[]> {
    try {
      const response = await apiClient.get<Workflow[]>('/api/workflows', {
        params: { include_templates: includeTemplates },
      });
      
      return response.map(workflow => workflowSchema.parse(workflow));
    } catch (error: any) {
      console.error('Failed to fetch workflows:', error);
      
      // Return empty array on error to prevent UI crash
      if (error.code === 'OFFLINE') {
        const cached = localStorage.getItem('cached_workflows');
        if (cached) {
          try {
            return JSON.parse(cached);
          } catch {
            return [];
          }
        }
      }
      
      throw error;
    }
  }

  /**
   * Get workflow by ID
   */
  async getWorkflow(id: string): Promise<Workflow> {
    try {
      const response = await apiClient.get<Workflow>(`/api/workflows/${id}`);
      return workflowSchema.parse(response);
    } catch (error: any) {
      console.error(`Failed to fetch workflow ${id}:`, error);
      throw error;
    }
  }

  /**
   * Create new workflow
   */
  async createWorkflow(data: CreateWorkflowData): Promise<Workflow> {
    try {
      // Validate input
      const validated = z.object({
        name: z.string().min(1).max(255),
        description: z.string().max(1000).optional(),
        steps: z.array(workflowStepSchema).min(1),
        is_template: z.boolean().optional(),
      }).parse(data);

      const response = await apiClient.post<Workflow>('/api/workflows', validated);
      const workflow = workflowSchema.parse(response);

      // Update cache
      this.updateWorkflowCache(workflow);

      return workflow;
    } catch (error: any) {
      console.error('Failed to create workflow:', error);
      
      if (error instanceof z.ZodError) {
        throw new Error(error.errors[0].message);
      }
      
      throw error;
    }
  }

  /**
   * Update workflow
   */
  async updateWorkflow(id: string, data: Partial<CreateWorkflowData>): Promise<Workflow> {
    try {
      const response = await apiClient.put<Workflow>(`/api/workflows/${id}`, data);
      const workflow = workflowSchema.parse(response);

      // Update cache
      this.updateWorkflowCache(workflow);

      return workflow;
    } catch (error: any) {
      console.error(`Failed to update workflow ${id}:`, error);
      throw error;
    }
  }

  /**
   * Delete workflow
   */
  async deleteWorkflow(id: string): Promise<void> {
    try {
      await apiClient.delete(`/api/workflows/${id}`);
      
      // Remove from cache
      this.removeFromWorkflowCache(id);
    } catch (error: any) {
      console.error(`Failed to delete workflow ${id}:`, error);
      throw error;
    }
  }

  /**
   * Execute workflow
   */
  async executeWorkflow(data: ExecuteWorkflowData): Promise<WorkflowExecution> {
    try {
      // Ensure WebSocket is connected
      if (!websocketService.connected) {
        await websocketService.connect();
      }

      const response = await apiClient.post<WorkflowExecution>(
        `/api/workflows/${data.workflow_id}/execute`,
        {
          input_data: data.input_data,
          context_sources: data.context_sources,
        }
      );

      const execution = workflowExecutionSchema.parse(response);

      // Register for updates
      if (execution.id) {
        this.registerExecutionCallback(execution.id, (update) => {
          console.log('Workflow execution update:', update);
        });
      }

      return execution;
    } catch (error: any) {
      console.error('Failed to execute workflow:', error);
      throw error;
    }
  }

  /**
   * Get workflow executions
   */
  async getWorkflowExecutions(workflowId?: string): Promise<WorkflowExecution[]> {
    try {
      const url = workflowId 
        ? `/api/workflows/${workflowId}/executions`
        : '/api/workflow-executions';
      
      const response = await apiClient.get<WorkflowExecution[]>(url);
      return response.map(execution => workflowExecutionSchema.parse(execution));
    } catch (error: any) {
      console.error('Failed to fetch workflow executions:', error);
      throw error;
    }
  }

  /**
   * Get execution details
   */
  async getExecutionDetails(executionId: string): Promise<{
    execution: WorkflowExecution;
    steps: ExecutionStep[];
  }> {
    try {
      const response = await apiClient.get<{
        execution: WorkflowExecution;
        steps: ExecutionStep[];
      }>(`/api/workflow-executions/${executionId}`);

      return {
        execution: workflowExecutionSchema.parse(response.execution),
        steps: response.steps.map(step => executionStepSchema.parse(step)),
      };
    } catch (error: any) {
      console.error(`Failed to fetch execution details ${executionId}:`, error);
      throw error;
    }
  }

  /**
   * Pause workflow execution
   */
  async pauseExecution(executionId: string): Promise<void> {
    try {
      await apiClient.post(`/api/workflow-executions/${executionId}/pause`);
    } catch (error: any) {
      console.error(`Failed to pause execution ${executionId}:`, error);
      throw error;
    }
  }

  /**
   * Resume workflow execution
   */
  async resumeExecution(executionId: string): Promise<void> {
    try {
      await apiClient.post(`/api/workflow-executions/${executionId}/resume`);
    } catch (error: any) {
      console.error(`Failed to resume execution ${executionId}:`, error);
      throw error;
    }
  }

  /**
   * Cancel workflow execution
   */
  async cancelExecution(executionId: string): Promise<void> {
    try {
      await apiClient.post(`/api/workflow-executions/${executionId}/cancel`);
      
      // Clean up callback
      this.executionCallbacks.delete(executionId);
    } catch (error: any) {
      console.error(`Failed to cancel execution ${executionId}:`, error);
      throw error;
    }
  }

  /**
   * Clone workflow as template
   */
  async cloneAsTemplate(workflowId: string, name: string): Promise<Workflow> {
    try {
      const response = await apiClient.post<Workflow>(
        `/api/workflows/${workflowId}/clone`,
        { name, is_template: true }
      );
      
      return workflowSchema.parse(response);
    } catch (error: any) {
      console.error(`Failed to clone workflow ${workflowId}:`, error);
      throw error;
    }
  }

  /**
   * Validate workflow configuration
   */
  async validateWorkflow(data: CreateWorkflowData): Promise<{
    valid: boolean;
    errors?: string[];
  }> {
    try {
      const response = await apiClient.post<{
        valid: boolean;
        errors?: string[];
      }>('/api/workflows/validate', data);
      
      return response;
    } catch (error: any) {
      console.error('Failed to validate workflow:', error);
      throw error;
    }
  }

  /**
   * Register callback for execution updates
   */
  registerExecutionCallback(executionId: string, callback: (execution: WorkflowExecution) => void): void {
    this.executionCallbacks.set(executionId, callback);
  }

  /**
   * Unregister callback for execution updates
   */
  unregisterExecutionCallback(executionId: string): void {
    this.executionCallbacks.delete(executionId);
  }

  // Cache management

  private updateWorkflowCache(workflow: Workflow): void {
    try {
      const cached = localStorage.getItem('cached_workflows');
      let workflows: Workflow[] = cached ? JSON.parse(cached) : [];
      
      const index = workflows.findIndex(w => w.id === workflow.id);
      if (index >= 0) {
        workflows[index] = workflow;
      } else {
        workflows.push(workflow);
      }
      
      localStorage.setItem('cached_workflows', JSON.stringify(workflows));
    } catch (error) {
      console.error('Failed to update workflow cache:', error);
    }
  }

  private removeFromWorkflowCache(id: string): void {
    try {
      const cached = localStorage.getItem('cached_workflows');
      if (cached) {
        let workflows: Workflow[] = JSON.parse(cached);
        workflows = workflows.filter(w => w.id !== id);
        localStorage.setItem('cached_workflows', JSON.stringify(workflows));
      }
    } catch (error) {
      console.error('Failed to remove from workflow cache:', error);
    }
  }
}

export const workflowService = new WorkflowService();