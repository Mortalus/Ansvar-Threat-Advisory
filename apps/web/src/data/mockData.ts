import { Agent, Workflow, User } from '../types';
import { Agent, Workflow, User, UserRole, AuditLog } from '../types';

export const mockRoles: UserRole[] = [
  {
    id: '1',
    name: 'admin',
    permissions: ['read', 'write', 'delete', 'manage_users', 'view_logs', 'manage_settings'],
    description: 'Full system access with user management and audit capabilities'
  },
  {
    id: '2',
    name: 'user',
    permissions: ['read', 'write', 'execute_workflows', 'manage_own_content'],
    description: 'Standard user with workflow creation and execution rights'
  },
  {
    id: '3',
    name: 'viewer',
    permissions: ['read', 'view_workflows', 'view_executions'],
    description: 'Read-only access to workflows and execution history'
  }
];

export const mockAuditLogs: AuditLog[] = [
  {
    id: '1',
    userId: '1',
    userName: 'Sarah Johnson',
    action: 'CREATE_THREAT_MODEL',
    resource: 'workflow',
    resourceId: '1',
    details: { workflowName: 'Threat Modeling Pipeline' },
    timestamp: '2024-01-22T14:30:00Z',
    ipAddress: '192.168.1.100'
  },
  {
    id: '2',
    userId: '1',
    userName: 'Sarah Johnson',
    action: 'UPDATE_SECURITY_AGENT',
    resource: 'agent',
    resourceId: '1',
    details: { agentName: 'DFD Generator', changes: ['systemPrompt', 'temperature'] },
    timestamp: '2024-01-22T13:15:00Z',
    ipAddress: '192.168.1.100'
  },
  {
    id: '3',
    userId: '2',
    userName: 'John Doe',
    action: 'EXECUTE_THREAT_ANALYSIS',
    resource: 'workflow',
    resourceId: '1',
    details: { executionId: 'exec-123', status: 'completed' },
    timestamp: '2024-01-22T12:00:00Z',
    ipAddress: '192.168.1.101'
  }
];

export const mockContextSources = [
  {
    id: '1',
    name: 'Security Knowledge Base',
    type: 'rag_database' as const,
    description: 'Comprehensive cybersecurity knowledge base with threat intelligence',
    configuration: {
      endpoint: 'https://api.security-kb.com/v1',
      apiKey: '***hidden***',
      parameters: { index: 'security-threats' }
    },
    isActive: true,
    createdAt: '2024-01-15T10:00:00Z'
  },
  {
    id: '2',
    name: 'NIST Framework Documents',
    type: 'document' as const,
    description: 'NIST Cybersecurity Framework documentation',
    configuration: {
      documentPath: '/documents/nist-framework/'
    },
    isActive: true,
    createdAt: '2024-01-12T14:30:00Z'
  }
];

export const mockUser: User = {
  id: '1',
  name: 'Sarah Johnson',
  email: 'sarah@company.com',
  avatar: 'https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=150&h=150&dpr=2&crop=face',
  role: 'admin',
  permissions: ['read', 'write', 'delete', 'manage_users', 'view_logs', 'manage_settings'],
  lastLogin: '2024-01-22T14:30:00Z',
  createdAt: '2024-01-01T10:00:00Z'
};

export const mockAgents: Agent[] = [
  {
    id: '1',
    name: 'DFD Generator',
    description: 'Specialized agent that analyzes documents and creates Data Flow Diagrams (DFDs) in JSON format for threat modeling purposes.',
    category: 'security',
    provider: 'OpenAI',
    systemPrompt: 'You are a cybersecurity expert specializing in Data Flow Diagram creation. Analyze the provided documents and create comprehensive DFDs in JSON format. Focus on identifying all data flows, processes, external entities, and data stores. Output should be structured JSON that clearly represents the system architecture and data movement patterns.',
    capabilities: ['Document Analysis', 'DFD Creation', 'JSON Output', 'System Architecture', 'Data Flow Mapping'],
    settings: {
      temperature: 0.3,
      maxTokens: 4096,
      model: 'gpt-4'
    },
    isActive: true,
    createdAt: '2024-01-15T10:00:00Z'
  },
  {
    id: '2',
    name: 'DFD Quality Checker',
    description: 'Quality assurance agent that validates and improves Data Flow Diagrams by cross-referencing with original documents.',
    category: 'security',
    provider: 'OpenAI',
    systemPrompt: 'You are a cybersecurity quality assurance expert. Review the generated DFD JSON against the original documents to ensure accuracy, completeness, and consistency. Identify missing elements, incorrect relationships, or inconsistencies. Provide corrected and enhanced DFD JSON output.',
    capabilities: ['Quality Assurance', 'Document Validation', 'DFD Review', 'Accuracy Checking', 'JSON Validation'],
    settings: {
      temperature: 0.2,
      maxTokens: 4096,
      model: 'gpt-4'
    },
    isActive: true,
    createdAt: '2024-01-12T14:30:00Z'
  },
  {
    id: '3',
    name: 'STRIDE Threat Analyzer',
    description: 'Security expert that applies STRIDE methodology to DFDs to identify potential threats and vulnerabilities.',
    category: 'security',
    provider: 'OpenAI',
    systemPrompt: 'You are a cybersecurity threat modeling expert specializing in STRIDE methodology. Analyze the provided DFD JSON and systematically apply STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) to identify potential threats. Output detailed threat analysis in JSON format.',
    capabilities: ['STRIDE Analysis', 'Threat Identification', 'Vulnerability Assessment', 'Security Analysis', 'Risk Evaluation'],
    settings: {
      temperature: 0.4,
      maxTokens: 3072,
      model: 'gpt-4'
    },
    isActive: true,
    createdAt: '2024-01-10T09:15:00Z'
  },
  {
    id: '4',
    name: 'Business Risk Assessor',
    description: 'Business-focused security analyst that evaluates threats from a business risk perspective and fine-tunes risk assessments.',
    category: 'security',
    provider: 'OpenAI',
    systemPrompt: 'You are a business risk analyst with cybersecurity expertise. Review the identified threats and assess them from a business impact perspective. Consider factors like business continuity, financial impact, regulatory compliance, and reputation. Fine-tune risk ratings and provide business-contextualized threat analysis in JSON format.',
    capabilities: ['Business Risk Analysis', 'Impact Assessment', 'Risk Prioritization', 'Compliance Review', 'Business Context'],
    settings: {
      temperature: 0.5,
      maxTokens: 3072,
      model: 'gpt-4'
    },
    isActive: true,
    createdAt: '2024-01-08T16:45:00Z'
  },
  {
    id: '5',
    name: 'Attack Path Generator',
    description: 'Advanced security analyst that converts threat information into detailed attack paths and scenarios.',
    category: 'security',
    provider: 'OpenAI',
    systemPrompt: 'You are an advanced cybersecurity analyst specializing in attack path modeling. Convert the business-contextualized threats into detailed attack paths, showing step-by-step how an attacker might exploit identified vulnerabilities. Include attack vectors, prerequisites, and potential impact chains in structured JSON format.',
    capabilities: ['Attack Path Modeling', 'Attack Vector Analysis', 'Exploit Chaining', 'Scenario Planning', 'Security Simulation'],
    settings: {
      temperature: 0.6,
      maxTokens: 4096,
      model: 'gpt-4'
    },
    isActive: true,
    createdAt: '2024-01-05T11:20:00Z'
  },
  {
    id: '6',
    name: 'Content Writer Pro',
    description: 'Advanced AI agent specialized in creating high-quality content across multiple formats including blog posts, social media content, and technical documentation.',
    category: 'content',
    provider: 'OpenAI',
    systemPrompt: 'You are a professional content writer with expertise in creating engaging, SEO-optimized content across multiple formats. Focus on clarity, engagement, and value for the target audience. Always maintain a professional tone while adapting to the specific content type requested.',
    capabilities: ['Blog Writing', 'Social Media', 'Technical Docs', 'SEO Optimization', 'Copy Editing'],
    settings: {
      temperature: 0.7,
      maxTokens: 2048,
      model: 'gpt-4'
    },
    isActive: true,
    createdAt: '2024-01-15T10:00:00Z'
  },
  {
    id: '7',
    name: 'Research Assistant',
    description: 'Conducts thorough research across multiple sources, synthesizes information, and provides comprehensive research reports on various topics.',
    category: 'research',
    provider: 'Anthropic',
    systemPrompt: 'You are a meticulous research assistant with expertise in information gathering, source verification, and academic writing. Conduct thorough research using reliable sources, synthesize information objectively, and present findings in a clear, well-structured format.',
    capabilities: ['Information Gathering', 'Source Verification', 'Report Writing', 'Citation Management', 'Literature Review'],
    settings: {
      temperature: 0.4,
      maxTokens: 3072,
      model: 'claude-3-opus'
    },
    isActive: false,
    createdAt: '2024-01-03T13:10:00Z'
  }
];

// Add Mermaid Diagram Generator agent
export const mermaidAgent: Agent = {
  id: '10',
  name: 'Mermaid Diagram Generator',
  description: 'Converts DFD JSON data into Mermaid diagram code for visual representation of data flows and system architecture.',
  category: 'security',
  provider: 'OpenAI',
  systemPrompt: 'You are a technical diagram specialist. Convert the provided DFD JSON data into clean, well-structured Mermaid diagram code. Focus on creating clear flowcharts that represent data flows, processes, external entities, and data stores. Use appropriate Mermaid syntax and ensure the diagram is readable and properly formatted.',
  capabilities: ['JSON to Mermaid', 'Diagram Generation', 'Data Flow Visualization', 'Technical Documentation', 'System Architecture'],
  settings: {
    temperature: 0.2,
    maxTokens: 2048,
    model: 'gpt-4'
  },
  isActive: true,
  createdAt: '2024-01-18T12:00:00Z'
};

export const mockWorkflows: Workflow[] = [
  {
    id: '1',
    name: 'Threat Modeling Pipeline',
    description: 'Comprehensive threat modeling workflow that analyzes documents, creates DFDs, performs STRIDE analysis, assesses business risks, and generates attack paths with optional review after each agent step.',
    steps: [
      {
        id: 's1',
        type: 'input',
        name: 'Document Upload',
        description: 'Upload system documentation, architecture diagrams, and requirements',
        position: { x: 50, y: 100 },
        connections: ['s2']
      },
      {
        id: 's2',
        type: 'agent',
        agentId: '1',
        name: 'DFD Generation',
        description: 'Generate Data Flow Diagrams from documents',
        position: { x: 250, y: 100 },
        connections: ['s3']
      },
      {
        id: 's3',
        type: 'agent',
        agentId: '2',
        name: 'DFD Quality Check',
        description: 'Validate and improve DFD quality',
        position: { x: 450, y: 100 },
        connections: ['s4']
      },
      {
        id: 's4',
        type: 'agent',
        agentId: '10',
        name: 'Mermaid Diagram Generation',
        description: 'Convert DFD to visual Mermaid diagram',
        position: { x: 850, y: 100 },
        connections: ['s5']
      },
      {
        id: 's5',
        type: 'agent',
        agentId: '3',
        name: 'STRIDE Analysis',
        description: 'Apply STRIDE methodology to identify threats',
        position: { x: 250, y: 300 },
        connections: ['s6']
      },
      {
        id: 's6',
        type: 'agent',
        agentId: '4',
        name: 'Business Risk Assessment',
        description: 'Evaluate threats from business perspective',
        position: { x: 450, y: 300 },
        connections: ['s7']
      },
      {
        id: 's7',
        type: 'agent',
        agentId: '5',
        name: 'Attack Path Generation',
        description: 'Convert threats into detailed attack paths',
        position: { x: 650, y: 300 },
        connections: ['s8']
      },
      {
        id: 's8',
        type: 'output',
        name: 'Final Threat Model',
        description: 'Complete threat model with attack paths',
        position: { x: 450, y: 500 },
        connections: []
      }
    ],
    isTemplate: true,
    createdAt: '2024-01-22T09:00:00Z'
  },
  {
    id: '2',
    name: 'Content Creation Pipeline',
    description: 'Complete content creation workflow from topic research to final publication, including SEO optimization and social media posting.',
    steps: [
      {
        id: 's1',
        type: 'input',
        name: 'Topic Input',
        description: 'Provide topic or keywords',
        position: { x: 50, y: 100 },
        connections: ['s2']
      },
      {
        id: 's2',
        type: 'agent',
        agentId: '7',
        name: 'Research Phase',
        description: 'Research topic and gather information',
        position: { x: 250, y: 100 },
        connections: ['s3']
      },
      {
        id: 's3',
        type: 'agent',
        agentId: '6',
        name: 'Content Writing',
        description: 'Create blog post content',
        position: { x: 450, y: 100 },
        connections: ['s4']
      },
      {
        id: 's4',
        type: 'output',
        name: 'Published Content',
        description: 'Final published content',
        position: { x: 650, y: 100 },
        connections: []
      }
    ],
    isTemplate: true,
    createdAt: '2024-01-20T08:00:00Z'
  },
  {
    id: '3',
    name: 'Customer Support Automation',
    description: 'Automated customer support workflow that categorizes inquiries, provides initial responses, and escalates complex issues.',
    steps: [
      {
        id: 's1',
        type: 'input',
        name: 'Customer Inquiry',
        description: 'Customer submits support ticket',
        position: { x: 50, y: 100 },
        connections: ['s2']
      },
      {
        id: 's2',
        type: 'agent',
        agentId: '8',
        name: 'Categorize Issue',
        description: 'Analyze and categorize the inquiry',
        position: { x: 250, y: 100 },
        connections: ['s3']
      },
      {
        id: 's3',
        type: 'condition',
        name: 'Complexity Check',
        description: 'Determine if issue needs escalation',
        position: { x: 450, y: 100 },
        connections: ['s4', 's5']
      },
      {
        id: 's4',
        type: 'agent',
        agentId: '8',
        name: 'Auto Response',
        description: 'Provide automated solution',
        position: { x: 350, y: 250 },
        connections: ['s6']
      },
      {
        id: 's5',
        type: 'output',
        name: 'Escalate to Human',
        description: 'Forward to human agent',
        position: { x: 550, y: 250 },
        connections: []
      },
      {
        id: 's6',
        type: 'output',
        name: 'Resolution Sent',
        description: 'Solution sent to customer',
        position: { x: 350, y: 400 },
        connections: []
      }
    ],
    isTemplate: true,
    createdAt: '2024-01-18T14:20:00Z'
  },
  {
    id: '4',
    name: 'Code Review Process',
    description: 'Automated code review workflow that analyzes code quality, identifies issues, and provides improvement suggestions.',
    steps: [
      {
        id: 's1',
        type: 'input',
        name: 'Code Submission',
        description: 'Developer submits code for review',
        position: { x: 50, y: 100 },
        connections: ['s2']
      },
      {
        id: 's2',
        type: 'agent',
        agentId: '9',
        name: 'Code Analysis',
        description: 'Analyze code quality and structure',
        position: { x: 250, y: 100 },
        connections: ['s3']
      },
      {
        id: 's3',
        type: 'agent',
        agentId: '9',
        name: 'Generate Report',
        description: 'Create detailed review report',
        position: { x: 450, y: 100 },
        connections: ['s4']
      },
      {
        id: 's4',
        type: 'output',
        name: 'Review Complete',
        description: 'Send report to developer',
        position: { x: 650, y: 100 },
        connections: []
      }
    ],
    isTemplate: false,
    createdAt: '2024-01-16T10:30:00Z'
  }
];

// Add missing agents for other workflows
export const additionalAgents: Agent[] = [
  mermaidAgent,
  {
    id: '8',
    name: 'Customer Support Agent',
    description: 'Specialized in handling customer inquiries, providing support solutions, and managing customer relationships with empathy and professionalism.',
    category: 'support',
    provider: 'Anthropic',
    systemPrompt: 'You are a helpful and empathetic customer support representative. Always be polite, understanding, and solution-focused. Listen carefully to customer concerns, ask clarifying questions when needed, and provide clear, actionable solutions. Escalate complex issues appropriately.',
    capabilities: ['Customer Inquiries', 'Technical Support', 'Escalation Management', 'Knowledge Base', 'Multi-language'],
    settings: {
      temperature: 0.8,
      maxTokens: 1024,
      model: 'claude-3-sonnet'
    },
    isActive: true,
    createdAt: '2024-01-08T16:45:00Z'
  },
  {
    id: '9',
    name: 'Code Assistant',
    description: 'Programming assistant that helps with code review, debugging, optimization, and documentation. Supports multiple programming languages.',
    category: 'development',
    provider: 'OpenAI',
    systemPrompt: 'You are a senior software engineer with expertise across multiple programming languages and frameworks. Provide clear, well-documented code solutions, identify potential issues, and suggest best practices. Focus on code quality, performance, and maintainability.',
    capabilities: ['Code Review', 'Debugging', 'Optimization', 'Documentation', 'Testing'],
    settings: {
      temperature: 0.2,
      maxTokens: 3072,
      model: 'gpt-3.5-turbo'
    },
    isActive: false,
    createdAt: '2024-01-10T09:15:00Z'
  }
];