export interface Agent {
  id: string;
  name: string;
  description: string;
  category: string;
  provider: string;
  systemPrompt: string;
  capabilities: string[];
  settings: {
    temperature: number;
    maxTokens: number;
    model: string;
  };
  isActive: boolean;
  createdAt: string;
}

export interface WorkflowStep {
  id: string;
  type: 'input' | 'agent' | 'condition' | 'output';
  agentId?: string;
  name: string;
  description: string;
  position: { x: number; y: number };
  connections: string[];
  contextSources?: string[];
  inputData?: any;
  outputData?: any;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  isTemplate: boolean;
  createdAt: string;
}

export interface WorkflowExecution {
  id: string;
  workflowId: string;
  workflowName: string;
  status: 'running' | 'completed' | 'failed' | 'paused';
  startedAt: string;
  completedAt?: string;
  steps: WorkflowExecutionStep[];
  totalSteps: number;
  completedSteps: number;
}

export interface WorkflowExecutionStep {
  id: string;
  stepId: string;
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  startedAt?: string;
  completedAt?: string;
  input?: any;
  output?: any;
  error?: string;
  agentId?: string;
  tokenUsage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
    cost?: number;
  };
  confidence?: number; // 0-1 scale
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar: string;
  role: string;
  permissions: string[];
  lastLogin?: string;
  createdAt: string;
}

export interface UserRole {
  id: string;
  name: 'admin' | 'user' | 'viewer';
  permissions: string[];
  description: string;
}

export interface AuditLog {
  id: string;
  userId: string;
  userName: string;
  action: string;
  resource: string;
  resourceId: string;
  details: any;
  timestamp: string;
  ipAddress?: string;
}

export interface Version {
  id: string;
  version: string;
  createdAt: string;
  createdBy: string;
  changes: string;
  data: any;
}

export interface LLMProvider {
  id: string;
  name: string;
  type: 'openai' | 'azure' | 'scaleway' | 'ollama' | 'custom';
  configuration: {
    apiKey?: string;
    endpoint?: string;
    region?: string;
    models?: string[];
    customHeaders?: Record<string, string>;
  };
  isActive: boolean;
  createdAt: string;
  versions?: Version[];
}

export interface ContextSource {
  id: string;
  name: string;
  type: 'rag_database' | 'document' | 'web_search' | 'api' | 'knowledge_base';
  description: string;
  configuration: {
    endpoint?: string;
    apiKey?: string;
    searchQuery?: string;
    documentPath?: string;
    parameters?: Record<string, any>;
  };
  isActive: boolean;
  createdAt: string;
  versions?: Version[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  tokenCount?: number;
}

export interface ChatSession {
  id: string;
  name: string;
  documents: UploadedDocument[];
  knowledgeSources: string[]; // Array of context source IDs
  messages: ChatMessage[];
  model: string;
  provider: string;
  totalTokens: number;
  createdAt: string;
  updatedAt: string;
}

export interface UploadedDocument {
  id: string;
  name: string;
  size: number;
  type: string;
  content?: string;
  tokenCount: number;
  uploadedAt: string;
}