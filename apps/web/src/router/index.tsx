import React from 'react';
import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { Sidebar } from '../components/Sidebar';
import { TopBar } from '../components/TopBar';
import { mockAgents, mockWorkflows, additionalAgents, mockContextSources } from '../data/mockData';

// Direct imports since components use named exports, not default exports
import { Dashboard } from '../components/Dashboard';
import { LoginPage } from '../components/LoginPage';
import { AgentsView } from '../components/AgentsView';
import { AgentDetail } from '../components/AgentDetail';
import { WorkflowsView } from '../components/WorkflowsView';
import { WorkflowDetail } from '../components/WorkflowDetail';
import { WorkflowBuilder } from '../components/WorkflowBuilder';
import { ContextSources } from '../components/ContextSources';
import { ExecutionHistory } from '../components/ExecutionHistory';
import { Settings } from '../components/Settings';
import { AuditLogs } from '../components/AuditLogs';
import { ProfilePage } from '../components/ProfilePage';
import { UserManagement } from '../components/UserManagement';
import { ChatWithDocument } from '../components/ChatWithDocument';

// Loading component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
  </div>
);

// Protected Route Component
interface ProtectedRouteProps {
  children?: React.ReactNode;
  requiredRole?: string;
  requiredPermission?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole,
  requiredPermission 
}) => {
  const { isAuthenticated, user, loading, checkAuth } = useAuthStore();

  // Check auth on mount
  React.useEffect(() => {
    if (!isAuthenticated && !loading) {
      checkAuth();
    }
  }, [isAuthenticated, loading, checkAuth]);

  // Show loading state while checking auth
  if (loading) {
    return <PageLoader />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user?.role !== requiredRole && user?.role !== 'admin') {
    return <Navigate to="/unauthorized" replace />;
  }

  if (requiredPermission && !user?.permissions?.includes(requiredPermission)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children || <Outlet />}</>;
};

// Main Layout Component
const MainLayout: React.FC = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);
  const { user, logout } = useAuthStore();

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        <Sidebar
          isCollapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          activeView=""
          onViewChange={() => {}}
          userRole={user?.role || 'user'}
        />
        
        <TopBar 
          user={user}
          sidebarCollapsed={sidebarCollapsed}
          onProfileClick={() => {}}
          onLogout={logout}
        />
        
        <main 
          className={`
            transition-all duration-300 pt-16 p-6
            ${sidebarCollapsed ? 'ml-16' : 'ml-64'}
          `}
        >
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </ErrorBoundary>
  );
};

// Router configuration
export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <MainLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Dashboard workflows={mockWorkflows} onWorkflowClick={() => {}} />,
      },
      {
        path: 'agents',
        children: [
          {
            index: true,
            element: <AgentsView agents={[...mockAgents, ...additionalAgents]} onAgentClick={() => {}} />,
          },
          {
            path: ':id',
            element: <AgentDetail agent={null} onBack={() => {}} onSave={() => {}} />,
          },
        ],
      },
      {
        path: 'workflows',
        children: [
          {
            index: true,
            element: <WorkflowsView workflows={mockWorkflows} onWorkflowClick={() => {}} />,
          },
          {
            path: 'builder',
            element: <WorkflowBuilder agents={[...mockAgents, ...additionalAgents]} />,
          },
          {
            path: ':id',
            element: <WorkflowDetail workflow={null} agents={[]} contextSources={[]} onBack={() => {}} onRunWorkflow={() => {}} onEditAgent={() => {}} />,
          },
        ],
      },
      {
        path: 'context-sources',
        element: <ContextSources />,
      },
      {
        path: 'chat',
        element: <ChatWithDocument providers={[]} contextSources={[]} chatSettings={{}} />,
      },
      {
        path: 'executions',
        element: <ExecutionHistory onAgentClick={() => {}} />,
      },
      {
        path: 'settings',
        element: <Settings />,
      },
      {
        path: 'profile',
        element: <ProfilePage user={null} onUpdateUser={() => {}} onBack={() => {}} />,
      },
      {
        path: 'admin',
        element: <ProtectedRoute requiredRole="admin" />,
        children: [
          {
            path: 'users',
            element: <UserManagement />,
          },
          {
            path: 'audit-logs',
            element: <AuditLogs />,
          },
        ],
      },
    ],
  },
  {
    path: '/unauthorized',
    element: (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <h1 className="text-2xl font-bold mb-4">Unauthorized Access</h1>
        <p className="text-gray-600 mb-8">You don't have permission to access this page.</p>
        <a href="/" className="text-purple-600 hover:text-purple-700">
          Return to Dashboard
        </a>
      </div>
    ),
  },
  {
    path: '*',
    element: (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <h1 className="text-2xl font-bold mb-4">404 - Page Not Found</h1>
        <p className="text-gray-600 mb-8">The page you're looking for doesn't exist.</p>
        <a href="/" className="text-purple-600 hover:text-purple-700">
          Return to Dashboard
        </a>
      </div>
    ),
  },
]);