import React, { useState, useEffect } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ErrorNotification } from './components/ErrorNotification';
import { OfflineIndicator } from './components/OfflineIndicator';
import { useErrorHandler } from './hooks/useErrorHandler';
import { useAuthStore } from './store/authStore';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { Dashboard } from './components/Dashboard';
import { AgentsView } from './components/AgentsView';
import { AgentDetail } from './components/AgentDetail';
import { WorkflowsView } from './components/WorkflowsView';
import { WorkflowDetail } from './components/WorkflowDetail';
import { WorkflowBuilder } from './components/WorkflowBuilder';
import { ContextSources } from './components/ContextSources';
import { ExecutionHistory } from './components/ExecutionHistory';
import { Settings } from './components/Settings';
import { AuditLogs } from './components/AuditLogs';
import { LoginPage } from './components/LoginPage';
import { ProfilePage } from './components/ProfilePage';
import { UserManagement } from './components/UserManagement';
import { ChatWithDocument } from './components/ChatWithDocument';
import { mockAgents, mockWorkflows, additionalAgents, mockContextSources } from './data/mockData';
import { Agent, Workflow } from './types';

function App() {
  const { error, clearError } = useErrorHandler();
  
  // Use Zustand auth store instead of local state
  const { isAuthenticated, user: currentUser, loading, checkAuth, logout } = useAuthStore();
  
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

  // Check authentication on app load
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const handleLogout = () => {
    logout();
    setActiveView('dashboard');
  };

  const handleProfileClick = () => {
    setActiveView('profile');
  };

  const handleUpdateUser = (updatedUser: any) => {
    // Update user in auth store
    useAuthStore.getState().updateUser(updatedUser);
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

  // Listen for navigation events from child components
  React.useEffect(() => {
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
        return currentUser?.role === 'admin' ? <AuditLogs /> : <div>Access Denied</div>;
      case 'user-management':
        return currentUser?.role === 'admin' ? <UserManagement /> : <div>Access Denied</div>;
      case 'settings':
        return <Settings />;
      case 'profile':
        return (
          <ProfilePage 
            user={currentUser} 
            onUpdateUser={handleUpdateUser}
            onBack={() => setActiveView('dashboard')}
          />
        );
      default:
        return null;
    }
  };

  // Show loading state while checking auth
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        <Sidebar
          isCollapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          activeView={activeView}
          onViewChange={setActiveView}
          userRole={currentUser?.role || 'user'}
        />
        
        <TopBar 
          user={currentUser} 
          sidebarCollapsed={sidebarCollapsed} 
          onProfileClick={handleProfileClick}
          onLogout={handleLogout}
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

export default App;