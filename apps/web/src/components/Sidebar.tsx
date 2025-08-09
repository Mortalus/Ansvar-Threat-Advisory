import React from 'react';
import {
  LayoutDashboard,
  Bot,
  Workflow,
  Settings,
  ChevronLeft,
  ChevronRight,
  Layers,
  Database,
  Activity,
  Shield,
  Users
} from 'lucide-react';

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  activeView: string;
  onViewChange: (view: string) => void;
  userRole: string;
}

const menuItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'agents', label: 'AI Agents', icon: Bot },
  { id: 'workflows', label: 'Workflows', icon: Workflow },
  { id: 'chat-document', label: 'Chat with Document', icon: Database },
  { id: 'executions', label: 'Execution History', icon: Activity },
  { id: 'workflow-builder', label: 'Workflow Builder', icon: Layers },
  { id: 'context-sources', label: 'Knowledge Sources', icon: Database },
  { id: 'audit-logs', label: 'Audit Logs', icon: Shield, adminOnly: true },
  { id: 'user-management', label: 'User Management', icon: Users, adminOnly: true },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export function Sidebar({ isCollapsed, onToggle, activeView, onViewChange, userRole }: SidebarProps) {
  const filteredMenuItems = menuItems.filter(item => 
    !item.adminOnly || userRole === 'admin'
  );

  return (
    <div className={`
      fixed left-0 top-0 h-full bg-gradient-to-b from-purple-900/95 to-blue-900/95 
      backdrop-blur-xl border-r border-purple-500/20 transition-all duration-300 z-40
      ${isCollapsed ? 'w-16' : 'w-64'}
    `}>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-purple-500/20">
          {!isCollapsed && (
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-white font-bold text-lg">Ansvar Security</h1>
            </div>
          )}
          <button
            onClick={onToggle}
            className="p-2 rounded-lg hover:bg-purple-500/20 text-purple-200 hover:text-white transition-colors"
          >
            {isCollapsed ? (
              <ChevronRight className="w-5 h-5" />
            ) : (
              <ChevronLeft className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-2">
          {filteredMenuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={`
                  w-full flex items-center space-x-3 px-3 py-3 rounded-lg 
                  transition-all duration-200 group
                  ${isActive 
                    ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white shadow-lg' 
                    : 'text-purple-200 hover:text-white hover:bg-purple-500/20'
                  }
                `}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-purple-300'}`} />
                {!isCollapsed && (
                  <span className="font-medium">{item.label}</span>
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
}