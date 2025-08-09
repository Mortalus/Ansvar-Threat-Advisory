'use client'

import { useState, useEffect } from 'react'
import { api, AgentConfiguration, AgentExecutionLog } from '@/lib/api'

interface AgentConfigModalProps {
  agentName: string
  onClose: () => void
  onSave: () => void
}

export default function AgentConfigModal({ agentName, onClose, onSave }: AgentConfigModalProps) {
  const [config, setConfig] = useState<AgentConfiguration | null>(null)
  const [executionHistory, setExecutionHistory] = useState<AgentExecutionLog[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activeTab, setActiveTab] = useState<'config' | 'history' | 'performance'>('config')
  const [performanceStats, setPerformanceStats] = useState<any>(null)

  useEffect(() => {
    loadAgentData()
  }, [agentName])

  const loadAgentData = async () => {
    try {
      setLoading(true)
      const [configData, historyData, performanceData] = await Promise.allSettled([
        api.getAgentConfiguration(agentName),
        api.getAgentExecutionHistory(agentName, 20),
        api.getAgentPerformanceStats(agentName)
      ])

      if (configData.status === 'fulfilled') {
        setConfig(configData.value)
      }
      if (historyData.status === 'fulfilled') {
        setExecutionHistory(historyData.value)
      }
      if (performanceData.status === 'fulfilled') {
        setPerformanceStats(performanceData.value)
      }
    } catch (error) {
      console.error('Failed to load agent data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!config) return

    try {
      setSaving(true)
      await api.updateAgentConfiguration(agentName, {
        enabled: config.enabled,
        priority: config.priority,
        custom_prompt: config.custom_prompt,
        max_tokens: config.max_tokens,
        temperature: config.temperature,
        rate_limit_per_hour: config.rate_limit_per_hour
      })
      onSave()
    } catch (error) {
      console.error('Failed to save configuration:', error)
      // Show error toast or message
    } finally {
      setSaving(false)
    }
  }

  const handleReload = async () => {
    try {
      await api.reloadAgentConfiguration(agentName)
      await loadAgentData() // Refresh data
    } catch (error) {
      console.error('Failed to reload agent:', error)
    }
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  if (!config) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <p>Failed to load agent configuration</p>
          <button onClick={onClose} className="mt-4 bg-gray-600 text-white px-4 py-2 rounded">
            Close
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              Configure Agent: {agentName}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex px-6">
            <button
              onClick={() => setActiveTab('config')}
              className={`py-2 px-4 border-b-2 font-medium text-sm ${
                activeTab === 'config'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Configuration
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`py-2 px-4 border-b-2 font-medium text-sm ${
                activeTab === 'history'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Execution History
            </button>
            <button
              onClick={() => setActiveTab('performance')}
              className={`py-2 px-4 border-b-2 font-medium text-sm ${
                activeTab === 'performance'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Performance
            </button>
          </nav>
        </div>

        {/* Content */}
        <div className="px-6 py-4 max-h-96 overflow-y-auto">
          {activeTab === 'config' && (
            <div className="space-y-4">
              {/* Basic Configuration */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Enabled
                  </label>
                  <input
                    type="checkbox"
                    checked={config.enabled}
                    onChange={(e) => setConfig({ ...config, enabled: e.target.checked })}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Priority (1-1000)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="1000"
                    value={config.priority}
                    onChange={(e) => setConfig({ ...config, priority: parseInt(e.target.value) || 100 })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Max Tokens
                  </label>
                  <input
                    type="number"
                    min="100"
                    max="8000"
                    value={config.max_tokens}
                    onChange={(e) => setConfig({ ...config, max_tokens: parseInt(e.target.value) || 4000 })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Temperature (0.0-2.0)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="2"
                    step="0.1"
                    value={config.temperature}
                    onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) || 0.7 })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Rate Limit (per hour)
                </label>
                <input
                  type="number"
                  min="1"
                  value={config.rate_limit_per_hour || ''}
                  onChange={(e) => setConfig({ ...config, rate_limit_per_hour: parseInt(e.target.value) || undefined })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="No limit"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Custom Prompt
                </label>
                <textarea
                  value={config.custom_prompt || ''}
                  onChange={(e) => setConfig({ ...config, custom_prompt: e.target.value || undefined })}
                  rows={4}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Leave empty to use default prompt"
                />
              </div>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="space-y-3">
              {executionHistory.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No execution history available</p>
              ) : (
                executionHistory.map((log, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-sm font-medium">
                          {log.success ? (
                            <span className="text-green-600">✅ Success</span>
                          ) : (
                            <span className="text-red-600">❌ Failed</span>
                          )}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(log.executed_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="text-xs text-gray-500 text-right">
                        <p>{log.execution_time.toFixed(2)}s</p>
                        {log.threats_found && <p>{log.threats_found} threats</p>}
                        {log.tokens_used && <p>{log.tokens_used} tokens</p>}
                      </div>
                    </div>
                    {log.error_message && (
                      <p className="mt-2 text-sm text-red-600">{log.error_message}</p>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'performance' && performanceStats && (
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 p-3 rounded">
                <h4 className="font-medium text-gray-900">Total Executions</h4>
                <p className="text-2xl font-bold text-blue-600">{performanceStats.total_executions}</p>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <h4 className="font-medium text-gray-900">Success Rate</h4>
                <p className="text-2xl font-bold text-green-600">{(performanceStats.success_rate * 100).toFixed(1)}%</p>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <h4 className="font-medium text-gray-900">Avg. Execution Time</h4>
                <p className="text-2xl font-bold text-yellow-600">{performanceStats.average_execution_time?.toFixed(2)}s</p>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <h4 className="font-medium text-gray-900">Avg. Threats</h4>
                <p className="text-2xl font-bold text-purple-600">{performanceStats.average_threats_per_execution?.toFixed(1)}</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-between">
          <div>
            <button
              onClick={handleReload}
              className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded text-sm font-medium"
            >
              Hot Reload
            </button>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={onClose}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded text-sm font-medium"
            >
              Cancel
            </button>
            {activeTab === 'config' && (
              <button
                onClick={handleSave}
                disabled={saving}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}