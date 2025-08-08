'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import AgentManager from '@/components/admin/agent-manager'
import PromptEditor from '@/components/admin/prompt-editor'
import SystemMonitor from '@/components/admin/system-monitor'
import HistoryViewer from '@/components/admin/history-viewer'
import ReportExporter from '@/components/admin/report-exporter'
import UserManager from '@/components/admin/user-manager'
import { Card } from '@/components/ui/card'

type AdminTab = 'agents' | 'prompts' | 'history' | 'system' | 'export' | 'users'

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<AdminTab>('agents')
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)
  const [currentUser, setCurrentUser] = useState<any>(null)
  const router = useRouter()

  useEffect(() => {
    checkAuthentication()
  }, [])

  const checkAuthentication = async () => {
    try {
      const token = localStorage.getItem('session_token')
      if (!token) {
        router.push('/login')
        return
      }

      // Validate token with backend
      const response = await fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        localStorage.removeItem('session_token')
        localStorage.removeItem('user_data')
        router.push('/login')
        return
      }

      const userData = await response.json()
      setCurrentUser(userData)
      setIsAuthenticated(true)

    } catch (error) {
      console.error('Authentication check failed:', error)
      localStorage.removeItem('session_token')
      localStorage.removeItem('user_data')
      router.push('/login')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem('session_token')
      if (token) {
        await fetch('/api/v1/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
      }
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      localStorage.removeItem('session_token')
      localStorage.removeItem('user_data')
      router.push('/login')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Checking authentication...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null // Will redirect to login
  }

  const tabs = [
    {
      id: 'agents' as AdminTab,
      label: 'Agents',
      icon: '🤖',
      description: 'Manage threat analysis agents'
    },
    {
      id: 'prompts' as AdminTab,
      label: 'Prompts',
      icon: '📝',
      description: 'Configure system prompts'
    },
    {
      id: 'users' as AdminTab,
      label: 'Users',
      icon: '👥',
      description: 'Manage user accounts and roles'
    },
    {
      id: 'history' as AdminTab,
      label: 'History',
      icon: '📋',
      description: 'View execution logs'
    },
    {
      id: 'system' as AdminTab,
      label: 'System',
      icon: '⚙️',
      description: 'Monitor performance'
    },
    {
      id: 'export' as AdminTab,
      label: 'Reports',
      icon: '📊',
      description: 'Generate reports'
    }
  ]

  const renderTabContent = () => {
    switch (activeTab) {
      case 'agents':
        return <AgentManager />
      case 'prompts':
        return <PromptEditor />
      case 'users':
        return <UserManager />
      case 'history':
        return <HistoryViewer />
      case 'system':
        return <SystemMonitor />
      case 'export':
        return <ReportExporter />
      default:
        return <AgentManager />
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Admin Hub</h1>
              <p className="mt-1 text-sm text-gray-500">
                Manage system configuration, agents, and monitor performance
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <div className="h-2 w-2 bg-green-400 rounded-full"></div>
                <span>System Healthy</span>
              </div>
              {currentUser && (
                <div className="flex items-center space-x-3">
                  <div className="text-sm text-gray-700">
                    <div className="font-medium">{currentUser.full_name || currentUser.username}</div>
                    <div className="text-xs text-gray-500">
                      {currentUser.roles.map((role: string) => role).join(', ')}
                    </div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded text-sm"
                  >
                    Logout
                  </button>
                </div>
              )}
              <a
                href="/admin/agents"
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Legacy Agent Page
              </a>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Navigation Sidebar */}
          <div className="lg:w-64 flex-shrink-0">
            <Card className="p-4">
              <nav className="space-y-1">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-start p-3 rounded-lg text-left transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-50 text-blue-700 border-l-4 border-blue-700'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex-shrink-0 text-lg mr-3">{tab.icon}</div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium">{tab.label}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {tab.description}
                      </div>
                    </div>
                  </button>
                ))}
              </nav>
            </Card>

            {/* Quick Stats */}
            <Card className="p-4 mt-4">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Quick Stats</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Active Agents</span>
                  <span className="font-medium">7</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Running Pipelines</span>
                  <span className="font-medium">3</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Custom Prompts</span>
                  <span className="font-medium">12</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">System Uptime</span>
                  <span className="font-medium text-green-600">99.9%</span>
                </div>
              </div>
            </Card>
          </div>

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            {renderTabContent()}
          </div>
        </div>
      </div>
    </div>
  )
}

