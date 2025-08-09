import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../store/authStore';
import { ErrorBoundary } from './ErrorBoundary';
import { ErrorNotification } from './ErrorNotification';
import { OfflineIndicator } from './OfflineIndicator';
import { useErrorHandler } from '../hooks/useErrorHandler';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { Dashboard } from './Dashboard';
import { AgentsView } from './AgentsView';
import { AgentDetail } from './AgentDetail';
import { WorkflowsView } from './WorkflowsView';
import { WorkflowDetail } from './WorkflowDetail';
import { WorkflowBuilder } from './WorkflowBuilder';
import { ContextSources } from './ContextSources';
import { ExecutionHistory } from './ExecutionHistory';
import { Settings } from './Settings';
import { AuditLogs } from './AuditLogs';
import { ProfilePage } from './ProfilePage';
import { UserManagement } from './UserManagement';
import { ChatWithDocument } from './ChatWithDocument';
import { mockAgents, mockWorkflows, additionalAgents, mockContextSources } from '../data/mockData';
import { Agent, Workflow } from '../types';

export function AuthenticatedApp() {
  const { user, logout } = useAuthStore();
  const { error, clearError } = useErrorHandler();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeView, setActiveView] = useState('dashboard');
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [agents, setAgents] = useState([...mockAgents, ...additionalAgents]);
  const [workflows, setWorkflows] = useState(mockWorkflows);
  
  // Mock chat settings
  const [chatSettings] = useState({
    enabledProviders: ['1', '2'], // Enable first two providers by default
    defaultModel: 'gpt-4',
    maxTokens: 4096,
    temperature: 0.7
  });

  // Mock providers for chat
  const [mockProviders] = useState([
    {
      id: '1',
      name: 'OpenAI GPT-4',
      type: 'openai' as const,
      configuration: {
        apiKey: '***hidden***',
        models: ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo']
      },
      isActive: true,
      createdAt: '2024-01-15T10:00:00Z'
    },
    {
      id: '2',
      name: 'Anthropic Claude',
      type: 'custom' as const,
      configuration: {
        apiKey: '***hidden***',
        endpoint: 'https://api.anthropic.com/v1',
        models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku']
      },
      isActive: true,
      createdAt: '2024-01-12T14:30:00Z'
    }
  ]);

  const handleProfileClick = () => {
    setActiveView('profile');
  };

  const handleAgentClick = (agent: Agent) => {
    setSelectedAgent(agent);
    setActiveView('agent-detail');
  };

  const handleAgentSave = (updatedAgent: Agent) => {
    setAgents(prev => prev.map(agent => 
      agent.id === updatedAgent.id ? updatedAgent : agent
    ));
    setSelectedAgent(updatedAgent);
  };

  const handleEditAgent = (agent: Agent) => {
    setSelectedAgent(agent);
    setActiveView('agent-detail');
  };

  const handleWorkflowClick = (workflow: Workflow) => {
    setSelectedWorkflow(workflow);
    setActiveView('workflow-detail');
  };

  const handleRunWorkflow = (workflowId: string) => {
    console.log('Running workflow:', workflowId);
    // Implement workflow execution logic
  };

  const handleUpdateUser = (updatedUser: any) => {
    // Update user in auth store
    useAuthStore.getState().updateUser(updatedUser);
  };

  // Listen for navigation events from child components
  useEffect(() => {
    const handleNavigate = (event: any) => {
      setActiveView(event.detail);
    };

    const handleSaveWorkflow = (event: any) => {
      const newWorkflow = event.detail;
      setWorkflows(prev => [...prev, newWorkflow]);
    };
    
    window.addEventListener('navigate', handleNavigate);
    window.addEventListener('saveWorkflow', handleSaveWorkflow);
    
    return () => {
      window.removeEventListener('navigate', handleNavigate);
      window.removeEventListener('saveWorkflow', handleSaveWorkflow);
    };
  }, []);

  const renderContent = () => {
    switch (activeView) {
      case 'dashboard':
        return <Dashboard workflows={workflows} onWorkflowClick={handleWorkflowClick} />;
      case 'agents':
        return <AgentsView agents={agents} onAgentClick={handleAgentClick} />;
      case 'agent-detail':
        return selectedAgent ? (
          <AgentDetail 
            agent={selectedAgent} 
            onBack={() => {
              setActiveView('agents');
              setSelectedAgent(null);
            }}
            onSave={handleAgentSave}
          />
        ) : null;
      case 'workflows':
        return <WorkflowsView workflows={workflows} onWorkflowClick={handleWorkflowClick} />;
      case 'workflow-detail':
        return selectedWorkflow ? (
          <WorkflowDetail 
            workflow={selectedWorkflow} 
            agents={agents}
            contextSources={mockContextSources}
            onBack={() => {
              setActiveView('workflows');
              setSelectedWorkflow(null);
            }}
            onRunWorkflow={handleRunWorkflow}
            onEditAgent={(agent) => {
              setSelectedAgent(agent);
              setActiveView('agent-detail');
            }}
          />
        ) : null;
      case 'workflow-builder':
        return <WorkflowBuilder agents={agents} />;
      case 'context-sources':
        return <ContextSources />;
      case 'chat-document':
        return <ChatWithDocument providers={mockProviders} contextSources={mockContextSources} chatSettings={chatSettings} />;
      case 'executions':
        return <ExecutionHistory onAgentClick={handleAgentClick} />;
      case 'audit-logs':
        return user?.role === 'admin' ? <AuditLogs /> : <div>Access Denied</div>;
      case 'user-management':
        return user?.role === 'admin' ? <UserManagement /> : <div>Access Denied</div>;
      case 'settings':
        return <Settings />;
      case 'profile':
        return (
          <ProfilePage 
            user={user} 
            onUpdateUser={handleUpdateUser}
            onBack={() => setActiveView('dashboard')}
          />
        );
      default:
        return null;
    }
  };

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        <Sidebar
          isCollapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          activeView={activeView}
          onViewChange={setActiveView}
          userRole={user.role}
        />
        
        <TopBar 
          user={user} 
          sidebarCollapsed={sidebarCollapsed} 
          onProfileClick={handleProfileClick}
          onLogout={logout}
        />
        
        <main 
          className={`
            transition-all duration-300 pt-16 p-6
            ${sidebarCollapsed ? 'ml-16' : 'ml-64'}
          `}
        >
          <div className="max-w-7xl mx-auto">
            {renderContent()}
          </div>
        </main>
        
        {/* Error Notifications */}
        {error && (
          <ErrorNotification 
            error={error} 
            onClose={clearError}
          />
        )}
        
        {/* Offline Indicator */}
        <OfflineIndicator />
      </div>
    </ErrorBoundary>
  );
}