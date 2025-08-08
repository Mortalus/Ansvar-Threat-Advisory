'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { Card } from '@/components/ui/card'

interface ExecutionLog {
  id: string
  type: 'pipeline' | 'agent' | 'system'
  pipeline_id?: string
  agent_name?: string
  operation: string
  status: 'success' | 'error' | 'in_progress'
  executed_at: string
  execution_time?: number
  user_id?: string
  details?: any
  error_message?: string
}

interface PipelineHistory {
  pipeline_id: string
  name?: string
  status: string
  created_at: string
  updated_at: string
  steps_completed: number
  total_steps: number
  execution_time?: number
}

export default function HistoryViewer() {
  const [logs, setLogs] = useState<ExecutionLog[]>([])
  const [pipelines, setPipelines] = useState<PipelineHistory[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'recent' | 'pipelines' | 'agents' | 'errors'>('recent')
  const [searchTerm, setSearchTerm] = useState('')
  const [timeFilter, setTimeFilter] = useState<'1h' | '24h' | '7d' | '30d' | 'all'>('24h')

  useEffect(() => {
    loadHistoryData()
  }, [timeFilter])

  const loadHistoryData = async () => {
    try {
      setLoading(true)
      
      // For now, we'll simulate history data since we need to implement the backend endpoints
      // In a real implementation, these would call actual API endpoints
      
      // Simulate recent execution logs
      const simulatedLogs: ExecutionLog[] = [
        {
          id: '1',
          type: 'pipeline',
          pipeline_id: 'pipe-123',
          operation: 'Document Upload',
          status: 'success',
          executed_at: new Date(Date.now() - 5 * 60000).toISOString(),
          execution_time: 2.3,
          details: { files_processed: 3, text_length: 15000 }
        },
        {
          id: '2',
          type: 'agent',
          agent_name: 'architectural_risk',
          operation: 'Threat Analysis',
          status: 'success',
          executed_at: new Date(Date.now() - 15 * 60000).toISOString(),
          execution_time: 8.7,
          details: { threats_found: 12, confidence: 0.87 }
        },
        {
          id: '3',
          type: 'pipeline',
          pipeline_id: 'pipe-456',
          operation: 'DFD Extraction',
          status: 'error',
          executed_at: new Date(Date.now() - 30 * 60000).toISOString(),
          execution_time: 15.2,
          error_message: 'Failed to parse document structure'
        },
        {
          id: '4',
          type: 'system',
          operation: 'Agent Registry Reload',
          status: 'success',
          executed_at: new Date(Date.now() - 60 * 60000).toISOString(),
          execution_time: 0.8,
          details: { agents_loaded: 3 }
        }
      ]
      
      // Simulate pipeline history
      const simulatedPipelines: PipelineHistory[] = [
        {
          pipeline_id: 'pipe-123',
          name: 'Threat Model - E-commerce App',
          status: 'completed',
          created_at: new Date(Date.now() - 2 * 60 * 60000).toISOString(),
          updated_at: new Date(Date.now() - 5 * 60000).toISOString(),
          steps_completed: 6,
          total_steps: 6,
          execution_time: 45.2
        },
        {
          pipeline_id: 'pipe-456', 
          name: 'API Security Analysis',
          status: 'failed',
          created_at: new Date(Date.now() - 4 * 60 * 60000).toISOString(),
          updated_at: new Date(Date.now() - 30 * 60000).toISOString(),
          steps_completed: 2,
          total_steps: 6,
          execution_time: 23.1
        },
        {
          pipeline_id: 'pipe-789',
          name: 'Mobile App Threat Model',
          status: 'in_progress',
          created_at: new Date(Date.now() - 30 * 60000).toISOString(),
          updated_at: new Date(Date.now() - 10 * 60000).toISOString(),
          steps_completed: 4,
          total_steps: 6,
          execution_time: 28.5
        }
      ]
      
      setLogs(simulatedLogs)
      setPipelines(simulatedPipelines)
      
    } catch (error) {
      console.error('Failed to load history data:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredLogs = logs.filter(log => {
    const matchesSearch = !searchTerm || 
      log.operation.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.agent_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.pipeline_id?.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesTab = activeTab === 'recent' || 
      (activeTab === 'pipelines' && log.type === 'pipeline') ||
      (activeTab === 'agents' && log.type === 'agent') ||
      (activeTab === 'errors' && log.status === 'error')
    
    return matchesSearch && matchesTab
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': case 'completed': return 'text-green-600 bg-green-100'
      case 'error': case 'failed': return 'text-red-600 bg-red-100'  
      case 'in_progress': return 'text-blue-600 bg-blue-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'pipeline': return '🔄'
      case 'agent': return '🤖'
      case 'system': return '⚙️'
      default: return '📋'
    }
  }

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date()
    const time = new Date(timestamp)
    const diffMs = now.getTime() - time.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading execution history...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Execution History</h1>
          <p className="text-gray-600">View detailed audit logs and pipeline execution history</p>
        </div>
        <button
          onClick={loadHistoryData}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search by operation, agent, or pipeline ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={timeFilter}
              onChange={(e) => setTimeFilter(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="all">All Time</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'recent', label: 'Recent Activity', icon: '🕒' },
            { id: 'pipelines', label: 'Pipelines', icon: '🔄' },
            { id: 'agents', label: 'Agent Executions', icon: '🤖' },
            { id: 'errors', label: 'Errors', icon: '⚠️' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'pipelines' ? (
        /* Pipeline History View */
        <div className="space-y-4">
          {pipelines.map((pipeline) => (
            <Card key={pipeline.pipeline_id} className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {pipeline.name || pipeline.pipeline_id}
                  </h3>
                  <p className="text-sm text-gray-500">ID: {pipeline.pipeline_id}</p>
                </div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(pipeline.status)}`}>
                  {pipeline.status}
                </span>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Progress:</span>
                  <div className="font-medium">{pipeline.steps_completed}/{pipeline.total_steps} steps</div>
                </div>
                <div>
                  <span className="text-gray-500">Duration:</span>
                  <div className="font-medium">{pipeline.execution_time?.toFixed(1)}s</div>
                </div>
                <div>
                  <span className="text-gray-500">Started:</span>
                  <div className="font-medium">{formatTimeAgo(pipeline.created_at)}</div>
                </div>
                <div>
                  <span className="text-gray-500">Updated:</span>
                  <div className="font-medium">{formatTimeAgo(pipeline.updated_at)}</div>
                </div>
              </div>
              
              {/* Progress Bar */}
              <div className="mt-4">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(pipeline.steps_completed / pipeline.total_steps) * 100}%` }}
                  ></div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        /* Execution Logs View */
        <div className="space-y-4">
          {filteredLogs.map((log) => (
            <Card key={log.id} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className="text-lg">{getTypeIcon(log.type)}</div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="text-base font-medium text-gray-900">{log.operation}</h3>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(log.status)}`}>
                        {log.status}
                      </span>
                    </div>
                    <div className="mt-1 text-sm text-gray-500 space-x-4">
                      <span>Type: {log.type}</span>
                      {log.agent_name && <span>Agent: {log.agent_name}</span>}
                      {log.pipeline_id && <span>Pipeline: {log.pipeline_id}</span>}
                      {log.execution_time && <span>Duration: {log.execution_time}s</span>}
                    </div>
                    <div className="mt-1 text-xs text-gray-400">
                      {formatTimeAgo(log.executed_at)} • {new Date(log.executed_at).toLocaleString()}
                    </div>
                    {log.error_message && (
                      <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                        <span className="font-medium">Error:</span> {log.error_message}
                      </div>
                    )}
                    {log.details && (
                      <div className="mt-2 p-2 bg-gray-50 border border-gray-200 rounded text-sm text-gray-700">
                        <span className="font-medium">Details:</span> {JSON.stringify(log.details, null, 2)}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          ))}
          
          {filteredLogs.length === 0 && (
            <Card className="p-8 text-center">
              <div className="text-gray-400 text-4xl mb-4">📋</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No execution logs found</h3>
              <p className="text-gray-600">
                {searchTerm ? 'No logs match your search criteria.' : 'No execution logs available for the selected time period.'}
              </p>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}