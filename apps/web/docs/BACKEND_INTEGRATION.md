# Backend Integration Guide

## 🏗️ Architecture Overview

This guide outlines the backend integration strategy for the Ansvar Security Agents platform, focusing on data sovereignty, security, and scalable AI workflow management.

### Core Principles
- **Data Sovereignty**: Complete control over data location and processing
- **Security First**: End-to-end encryption and secure communication
- **Scalability**: Horizontal scaling for AI workloads
- **Reliability**: Fault-tolerant design with graceful degradation
- **Performance**: Optimized for real-time AI processing

---

## 🔧 Technology Stack

### Recommended Backend Technologies

#### **Primary Stack**
- **Runtime**: Node.js 18+ or Python 3.9+
- **Framework**: Express.js/Fastify (Node.js) or FastAPI (Python)
- **Database**: PostgreSQL 14+ with vector extensions
- **Cache**: Redis 7+ for session management and caching
- **Message Queue**: RabbitMQ or Apache Kafka for workflow orchestration
- **File Storage**: MinIO (S3-compatible) for document storage

#### **AI/ML Stack**
- **LLM Integration**: OpenAI API, Anthropic Claude, Azure OpenAI
- **Vector Database**: Pinecone, Weaviate, or pgvector
- **Document Processing**: Apache Tika, PyPDF2, python-docx
- **Workflow Engine**: Temporal.io or Apache Airflow

#### **Infrastructure**
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Kubernetes (production)
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)

---

## 📊 Database Schema

### Core Tables

#### Users & Authentication
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    permissions JSONB DEFAULT '[]',
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sessions table
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### AI Agents
```sql
-- AI Agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    system_prompt TEXT NOT NULL,
    capabilities JSONB DEFAULT '[]',
    settings JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent versions for tracking changes
CREATE TABLE agent_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    changes TEXT,
    data JSONB NOT NULL,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Workflows
```sql
-- Workflows table
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    steps JSONB NOT NULL,
    is_template BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow executions
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    total_steps INTEGER NOT NULL,
    completed_steps INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id)
);

-- Execution steps
CREATE TABLE execution_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES workflow_executions(id) ON DELETE CASCADE,
    step_id VARCHAR(255) NOT NULL,
    agent_id UUID REFERENCES agents(id),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    token_usage JSONB,
    confidence DECIMAL(3,2),
    step_order INTEGER NOT NULL
);
```

#### Knowledge Sources
```sql
-- Context sources (knowledge bases)
CREATE TABLE context_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    description TEXT,
    configuration JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    processed_content TEXT,
    metadata JSONB DEFAULT '{}',
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vector embeddings (if using pgvector)
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI embedding dimension
    metadata JSONB DEFAULT '{}'
);
```

#### Audit & Logging
```sql
-- Audit logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System logs
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 🔌 API Design

### RESTful API Structure

#### Base URL
```
https://api.ansvar.com/v1
```

#### Authentication
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Core Endpoints

#### Authentication
```typescript
// POST /auth/login
interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  user: User;
  token: string;
  expires_at: string;
}

// POST /auth/refresh
interface RefreshRequest {
  refresh_token: string;
}

// POST /auth/logout
// DELETE /auth/sessions/:sessionId
```

#### Users
```typescript
// GET /users/me
// PUT /users/me
// GET /users (admin only)
// POST /users (admin only)
// PUT /users/:id (admin only)
// DELETE /users/:id (admin only)

interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  role: string;
  permissions: string[];
  last_login?: string;
  created_at: string;
  updated_at: string;
}
```

#### Agents
```typescript
// GET /agents
// POST /agents
// GET /agents/:id
// PUT /agents/:id
// DELETE /agents/:id
// POST /agents/:id/test

interface Agent {
  id: string;
  name: string;
  description: string;
  category: string;
  provider: string;
  system_prompt: string;
  capabilities: string[];
  settings: {
    temperature: number;
    max_tokens: number;
    model: string;
  };
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

interface AgentTestRequest {
  input: any;
  context_sources?: string[];
}

interface AgentTestResponse {
  output: any;
  token_usage: TokenUsage;
  confidence?: number;
  execution_time: number;
}
```

#### Workflows
```typescript
// GET /workflows
// POST /workflows
// GET /workflows/:id
// PUT /workflows/:id
// DELETE /workflows/:id
// POST /workflows/:id/execute
// GET /workflows/:id/executions

interface Workflow {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  is_template: boolean;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

interface WorkflowExecuteRequest {
  input_data?: any;
  context_sources?: string[];
}

interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused';
  started_at: string;
  completed_at?: string;
  total_steps: number;
  completed_steps: number;
  steps: ExecutionStep[];
  error_message?: string;
  metadata: any;
}
```

#### Context Sources
```typescript
// GET /context-sources
// POST /context-sources
// GET /context-sources/:id
// PUT /context-sources/:id
// DELETE /context-sources/:id
// POST /context-sources/:id/test

interface ContextSource {
  id: string;
  name: string;
  type: 'rag_database' | 'document' | 'web_search' | 'api' | 'knowledge_base';
  description: string;
  configuration: any;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}
```

#### Documents
```typescript
// GET /documents
// POST /documents/upload
// GET /documents/:id
// DELETE /documents/:id
// GET /documents/:id/content
// POST /documents/:id/process

interface Document {
  id: string;
  name: string;
  file_size: number;
  mime_type: string;
  content_hash: string;
  metadata: any;
  uploaded_by: string;
  created_at: string;
}

interface DocumentUploadResponse {
  document: Document;
  processing_job_id: string;
}
```

---

## 🔄 Workflow Engine

### Workflow Execution Architecture

#### Components
1. **Workflow Scheduler**: Manages workflow queues and execution
2. **Step Executor**: Executes individual workflow steps
3. **Agent Manager**: Handles AI agent interactions
4. **Context Manager**: Manages knowledge sources and context
5. **Result Processor**: Processes and stores execution results

#### Execution Flow
```typescript
interface WorkflowEngine {
  // Start workflow execution
  executeWorkflow(workflowId: string, input: any): Promise<ExecutionResult>;
  
  // Pause/resume execution
  pauseExecution(executionId: string): Promise<void>;
  resumeExecution(executionId: string): Promise<void>;
  
  // Cancel execution
  cancelExecution(executionId: string): Promise<void>;
  
  // Get execution status
  getExecutionStatus(executionId: string): Promise<ExecutionStatus>;
}

// Example implementation
class WorkflowEngine {
  async executeWorkflow(workflowId: string, input: any): Promise<ExecutionResult> {
    const workflow = await this.getWorkflow(workflowId);
    const execution = await this.createExecution(workflow, input);
    
    // Queue workflow for execution
    await this.queueExecution(execution);
    
    return {
      execution_id: execution.id,
      status: 'queued',
      estimated_duration: this.estimateDuration(workflow)
    };
  }
  
  private async executeStep(step: WorkflowStep, context: ExecutionContext): Promise<StepResult> {
    switch (step.type) {
      case 'agent':
        return await this.executeAgentStep(step, context);
      case 'condition':
        return await this.executeConditionStep(step, context);
      case 'parallel':
        return await this.executeParallelSteps(step, context);
      default:
        throw new Error(`Unknown step type: ${step.type}`);
    }
  }
}
```

### Message Queue Integration

#### Queue Structure
```typescript
// Workflow execution queue
interface WorkflowJob {
  execution_id: string;
  workflow_id: string;
  input_data: any;
  priority: number;
  retry_count: number;
  max_retries: number;
}

// Step execution queue
interface StepJob {
  execution_id: string;
  step_id: string;
  agent_id?: string;
  input_data: any;
  context_sources: string[];
  retry_count: number;
}

// Result processing queue
interface ResultJob {
  execution_id: string;
  step_id: string;
  result_data: any;
  requires_review: boolean;
}
```

---

## 🤖 AI Integration

### LLM Provider Abstraction

```typescript
interface LLMProvider {
  name: string;
  type: 'openai' | 'anthropic' | 'azure' | 'custom';
  
  // Generate completion
  complete(request: CompletionRequest): Promise<CompletionResponse>;
  
  // Generate embeddings
  embed(text: string): Promise<number[]>;
  
  // Stream completion
  streamComplete(request: CompletionRequest): AsyncIterable<CompletionChunk>;
}

interface CompletionRequest {
  model: string;
  messages: Message[];
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
  context?: string;
}

interface CompletionResponse {
  content: string;
  token_usage: TokenUsage;
  model: string;
  finish_reason: string;
  confidence?: number;
}

// Provider implementations
class OpenAIProvider implements LLMProvider {
  async complete(request: CompletionRequest): Promise<CompletionResponse> {
    const response = await this.client.chat.completions.create({
      model: request.model,
      messages: request.messages,
      temperature: request.temperature,
      max_tokens: request.max_tokens
    });
    
    return {
      content: response.choices[0].message.content,
      token_usage: {
        prompt_tokens: response.usage.prompt_tokens,
        completion_tokens: response.usage.completion_tokens,
        total_tokens: response.usage.total_tokens
      },
      model: response.model,
      finish_reason: response.choices[0].finish_reason
    };
  }
}
```

### Context Management

```typescript
interface ContextManager {
  // Retrieve relevant context for a query
  getContext(query: string, sources: string[]): Promise<ContextResult>;
  
  // Add documents to context sources
  addDocuments(sourceId: string, documents: Document[]): Promise<void>;
  
  // Search within context sources
  search(query: string, sourceId: string, limit?: number): Promise<SearchResult[]>;
}

interface ContextResult {
  chunks: ContextChunk[];
  total_tokens: number;
  sources: string[];
}

interface ContextChunk {
  content: string;
  source: string;
  relevance_score: number;
  metadata: any;
}

// RAG implementation
class RAGContextManager implements ContextManager {
  async getContext(query: string, sources: string[]): Promise<ContextResult> {
    // Generate query embedding
    const queryEmbedding = await this.embedQuery(query);
    
    // Search across specified sources
    const chunks = await this.vectorSearch(queryEmbedding, sources);
    
    // Rank and filter results
    const rankedChunks = this.rankChunks(chunks, query);
    
    return {
      chunks: rankedChunks,
      total_tokens: this.calculateTokens(rankedChunks),
      sources: sources
    };
  }
}
```

---

## 🔐 Security Implementation

### Authentication & Authorization

```typescript
// JWT token structure
interface JWTPayload {
  user_id: string;
  email: string;
  role: string;
  permissions: string[];
  session_id: string;
  exp: number;
  iat: number;
}

// Permission checking middleware
function requirePermission(permission: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as JWTPayload;
    
    if (!user.permissions.includes(permission)) {
      return res.status(403).json({
        error: 'Insufficient permissions',
        required: permission
      });
    }
    
    next();
  };
}

// Rate limiting
const rateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP'
});
```

### Data Encryption

```typescript
// Encryption service
class EncryptionService {
  private readonly algorithm = 'aes-256-gcm';
  private readonly keyLength = 32;
  
  encrypt(data: string, key: Buffer): EncryptedData {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipher(this.algorithm, key, iv);
    
    let encrypted = cipher.update(data, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    const authTag = cipher.getAuthTag();
    
    return {
      encrypted,
      iv: iv.toString('hex'),
      authTag: authTag.toString('hex')
    };
  }
  
  decrypt(encryptedData: EncryptedData, key: Buffer): string {
    const decipher = crypto.createDecipher(
      this.algorithm,
      key,
      Buffer.from(encryptedData.iv, 'hex')
    );
    
    decipher.setAuthTag(Buffer.from(encryptedData.authTag, 'hex'));
    
    let decrypted = decipher.update(encryptedData.encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    
    return decrypted;
  }
}
```

---

## 📊 Monitoring & Observability

### Metrics Collection

```typescript
// Metrics service
class MetricsService {
  // Workflow metrics
  recordWorkflowExecution(workflowId: string, duration: number, status: string) {
    this.histogram('workflow_execution_duration', duration, {
      workflow_id: workflowId,
      status
    });
    
    this.counter('workflow_executions_total', 1, {
      workflow_id: workflowId,
      status
    });
  }
  
  // Agent metrics
  recordAgentCall(agentId: string, tokens: number, duration: number) {
    this.histogram('agent_call_duration', duration, { agent_id: agentId });
    this.histogram('agent_token_usage', tokens, { agent_id: agentId });
  }
  
  // API metrics
  recordAPICall(endpoint: string, method: string, status: number, duration: number) {
    this.histogram('api_request_duration', duration, {
      endpoint,
      method,
      status: status.toString()
    });
  }
}
```

### Health Checks

```typescript
// Health check endpoints
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.APP_VERSION
  });
});

app.get('/health/detailed', async (req, res) => {
  const checks = await Promise.allSettled([
    checkDatabase(),
    checkRedis(),
    checkMessageQueue(),
    checkLLMProviders()
  ]);
  
  const results = checks.map((check, index) => ({
    service: ['database', 'redis', 'queue', 'llm'][index],
    status: check.status === 'fulfilled' ? 'healthy' : 'unhealthy',
    details: check.status === 'fulfilled' ? check.value : check.reason
  }));
  
  const overallStatus = results.every(r => r.status === 'healthy') ? 'healthy' : 'unhealthy';
  
  res.status(overallStatus === 'healthy' ? 200 : 503).json({
    status: overallStatus,
    checks: results,
    timestamp: new Date().toISOString()
  });
});
```

---

## 🚀 Deployment Guide

### Docker Configuration

#### Dockerfile
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

USER nextjs

EXPOSE 3000

CMD ["npm", "start"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/ansvar
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=ansvar
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ansvar-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ansvar-api
  template:
    metadata:
      labels:
        app: ansvar-api
    spec:
      containers:
      - name: api
        image: ansvar/api:latest
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ansvar-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: ansvar-secrets
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ansvar-api-service
spec:
  selector:
    app: ansvar-api
  ports:
  - port: 80
    targetPort: 3000
  type: ClusterIP
```

---

## 🔧 Development Setup

### Environment Variables

```bash
# .env.development
NODE_ENV=development
PORT=3000

# Database
DATABASE_URL=postgresql://localhost:5432/ansvar_dev
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRES_IN=24h

# LLM Providers
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
AZURE_OPENAI_ENDPOINT=your-azure-endpoint
AZURE_OPENAI_KEY=your-azure-key

# File Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=ansvar-documents

# Monitoring
PROMETHEUS_ENDPOINT=http://localhost:9090
GRAFANA_ENDPOINT=http://localhost:3001
```

### Development Scripts

```json
{
  "scripts": {
    "dev": "nodemon src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "migrate": "knex migrate:latest",
    "migrate:rollback": "knex migrate:rollback",
    "seed": "knex seed:run",
    "lint": "eslint src/**/*.ts",
    "lint:fix": "eslint src/**/*.ts --fix"
  }
}
```

### Database Migrations

```typescript
// migrations/001_initial_schema.ts
import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  // Create users table
  await knex.schema.createTable('users', (table) => {
    table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    table.string('email').unique().notNullable();
    table.string('password_hash').notNullable();
    table.string('name').notNullable();
    table.text('avatar_url');
    table.string('role').notNullable().defaultTo('user');
    table.jsonb('permissions').defaultTo('[]');
    table.timestamp('last_login');
    table.timestamps(true, true);
  });

  // Create agents table
  await knex.schema.createTable('agents', (table) => {
    table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    table.string('name').notNullable();
    table.text('description');
    table.string('category').notNullable();
    table.string('provider').notNullable();
    table.text('system_prompt').notNullable();
    table.jsonb('capabilities').defaultTo('[]');
    table.jsonb('settings').notNullable();
    table.boolean('is_active').defaultTo(true);
    table.uuid('created_by').references('id').inTable('users');
    table.timestamps(true, true);
  });

  // Add more tables...
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTableIfExists('agents');
  await knex.schema.dropTableIfExists('users');
}
```

---

## 🧪 Testing Strategy

### Unit Tests

```typescript
// tests/services/workflow.test.ts
import { WorkflowService } from '../../src/services/WorkflowService';
import { mockAgent, mockWorkflow } from '../fixtures';

describe('WorkflowService', () => {
  let workflowService: WorkflowService;

  beforeEach(() => {
    workflowService = new WorkflowService();
  });

  describe('executeWorkflow', () => {
    it('should execute a simple workflow successfully', async () => {
      const result = await workflowService.executeWorkflow(
        mockWorkflow.id,
        { input: 'test data' }
      );

      expect(result.status).toBe('completed');
      expect(result.steps).toHaveLength(mockWorkflow.steps.length);
    });

    it('should handle agent failures gracefully', async () => {
      // Mock agent failure
      jest.spyOn(workflowService, 'executeAgent')
        .mockRejectedValue(new Error('Agent failed'));

      const result = await workflowService.executeWorkflow(
        mockWorkflow.id,
        { input: 'test data' }
      );

      expect(result.status).toBe('failed');
      expect(result.error_message).toContain('Agent failed');
    });
  });
});
```

### Integration Tests

```typescript
// tests/integration/api.test.ts
import request from 'supertest';
import { app } from '../../src/app';
import { setupTestDatabase, teardownTestDatabase } from '../helpers/database';

describe('API Integration Tests', () => {
  beforeAll(async () => {
    await setupTestDatabase();
  });

  afterAll(async () => {
    await teardownTestDatabase();
  });

  describe('POST /api/v1/workflows/:id/execute', () => {
    it('should execute workflow and return execution ID', async () => {
      const response = await request(app)
        .post('/api/v1/workflows/test-workflow-id/execute')
        .set('Authorization', 'Bearer valid-token')
        .send({ input_data: { test: 'data' } })
        .expect(200);

      expect(response.body).toHaveProperty('execution_id');
      expect(response.body.status).toBe('queued');
    });
  });
});
```

---

## 📈 Performance Optimization

### Database Optimization

```sql
-- Indexes for common queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_agents_category ON agents(category);
CREATE INDEX idx_workflows_created_by ON workflows(created_by);
CREATE INDEX idx_executions_status ON workflow_executions(status);
CREATE INDEX idx_executions_created_at ON workflow_executions(created_at);

-- Composite indexes
CREATE INDEX idx_executions_workflow_status ON workflow_executions(workflow_id, status);
CREATE INDEX idx_steps_execution_order ON execution_steps(execution_id, step_order);

-- Vector similarity search (if using pgvector)
CREATE INDEX ON document_embeddings USING ivfflat (embedding vector_cosine_ops);
```

### Caching Strategy

```typescript
// Redis caching service
class CacheService {
  private redis: Redis;

  async get<T>(key: string): Promise<T | null> {
    const cached = await this.redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  async set(key: string, value: any, ttl: number = 3600): Promise<void> {
    await this.redis.setex(key, ttl, JSON.stringify(value));
  }

  async invalidate(pattern: string): Promise<void> {
    const keys = await this.redis.keys(pattern);
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }
}

// Usage in services
class AgentService {
  async getAgent(id: string): Promise<Agent> {
    const cacheKey = `agent:${id}`;
    let agent = await this.cache.get<Agent>(cacheKey);
    
    if (!agent) {
      agent = await this.db.agents.findById(id);
      await this.cache.set(cacheKey, agent, 1800); // 30 minutes
    }
    
    return agent;
  }
}
```

---

## 🔍 Troubleshooting Guide

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
pg_isready -h localhost -p 5432

# Check database logs
docker logs ansvar-db

# Test connection from application
npm run db:test
```

#### LLM Provider Issues
```typescript
// Provider health check
async function checkLLMProviders(): Promise<HealthStatus> {
  const providers = await this.getActiveProviders();
  const results = await Promise.allSettled(
    providers.map(provider => provider.healthCheck())
  );
  
  return {
    healthy: results.every(r => r.status === 'fulfilled'),
    details: results.map((r, i) => ({
      provider: providers[i].name,
      status: r.status,
      error: r.status === 'rejected' ? r.reason.message : null
    }))
  };
}
```

#### Memory Issues
```bash
# Monitor memory usage
docker stats ansvar-api

# Check for memory leaks
node --inspect src/index.js
```

### Debugging Tools

```typescript
// Debug middleware
function debugMiddleware(req: Request, res: Response, next: NextFunction) {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`${req.method} ${req.path} - ${res.statusCode} - ${duration}ms`);
  });
  
  next();
}

// Request logging
import winston from 'winston';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});
```

This comprehensive backend integration guide provides the foundation for building a scalable, secure, and maintainable backend for your Ansvar Security Agents platform.