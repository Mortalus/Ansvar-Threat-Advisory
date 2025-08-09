'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { Card } from '@/components/ui/card'

interface SystemPrompt {
  id: string
  step_name: string
  agent_type: string | null
  prompt_text: string
  version: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export default function PromptEditor() {
  const [prompts, setPrompts] = useState<SystemPrompt[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPrompt, setSelectedPrompt] = useState<SystemPrompt | null>(null)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editText, setEditText] = useState('')

  useEffect(() => {
    loadPrompts()
  }, [])

  const loadPrompts = async () => {
    try {
      setLoading(true)
      const promptList = await api.getSystemPrompts()
      setPrompts(promptList)
    } catch (error) {
      console.error('Failed to load prompts:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleEditPrompt = (prompt: SystemPrompt) => {
    setSelectedPrompt(prompt)
    setEditText(prompt.prompt_text)
    setEditing(true)
  }

  const handleSavePrompt = async () => {
    if (!selectedPrompt) return

    try {
      setSaving(true)
      await api.updateSystemPrompt(selectedPrompt.id, {
        prompt_text: editText,
        step_name: selectedPrompt.step_name,
        agent_type: selectedPrompt.agent_type
      })
      
      // Refresh the prompts list
      await loadPrompts()
      setEditing(false)
      setSelectedPrompt(null)
    } catch (error) {
      console.error('Failed to save prompt:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleCancelEdit = () => {
    setEditing(false)
    setSelectedPrompt(null)
    setEditText('')
  }

  const getStepDisplayName = (stepName: string) => {
    const stepNames: Record<string, string> = {
      'dfd_extraction': 'DFD Extraction',
      'threat_generation': 'Threat Generation',
      'threat_refinement': 'Threat Refinement',
      'attack_path_analysis': 'Attack Path Analysis',
      'data_extraction': 'Data Extraction',
      'document_upload': 'Document Upload'
    }
    return stepNames[stepName] || stepName
  }

  const getAgentTypeColor = (agentType: string | null) => {
    if (!agentType) return 'bg-gray-100 text-gray-800'
    
    const colors: Record<string, string> = {
      'architectural': 'bg-blue-100 text-blue-800',
      'business': 'bg-green-100 text-green-800',
      'compliance': 'bg-purple-100 text-purple-800',
      'security': 'bg-red-100 text-red-800'
    }
    return colors[agentType.toLowerCase()] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading system prompts...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Prompt Editor</h1>
          <p className="text-gray-600">Configure AI system prompts for different pipeline steps</p>
        </div>
        <button
          onClick={loadPrompts}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Prompts List */}
      <div className="grid gap-4">
        {prompts.map((prompt) => (
          <Card key={prompt.id} className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {getStepDisplayName(prompt.step_name)}
                </h3>
                <div className="flex items-center gap-2 mt-1">
                  {prompt.agent_type && (
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getAgentTypeColor(prompt.agent_type)}`}>
                      {prompt.agent_type}
                    </span>
                  )}
                  <span className="text-sm text-gray-500">
                    Version {prompt.version} • {prompt.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
              <button
                onClick={() => handleEditPrompt(prompt)}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
              >
                ✏️ Edit
              </button>
            </div>

            <div className="bg-gray-50 rounded-md p-4">
              <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono max-h-32 overflow-y-auto">
                {prompt.prompt_text.length > 300 
                  ? `${prompt.prompt_text.substring(0, 300)}...`
                  : prompt.prompt_text
                }
              </pre>
            </div>

            <div className="flex justify-between items-center mt-4 text-xs text-gray-500">
              <span>Created: {new Date(prompt.created_at).toLocaleDateString()}</span>
              <span>Updated: {new Date(prompt.updated_at).toLocaleDateString()}</span>
            </div>
          </Card>
        ))}
      </div>

      {prompts.length === 0 && (
        <Card className="p-8 text-center">
          <div className="text-gray-400 text-4xl mb-4">📝</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No system prompts found</h3>
          <p className="text-gray-600">
            System prompts will appear here once they are configured in the backend.
          </p>
        </Card>
      )}

      {/* Edit Modal */}
      {editing && selectedPrompt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  Edit Prompt: {getStepDisplayName(selectedPrompt.step_name)}
                </h2>
                {selectedPrompt.agent_type && (
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-1 ${getAgentTypeColor(selectedPrompt.agent_type)}`}>
                    {selectedPrompt.agent_type}
                  </span>
                )}
              </div>
              <button
                onClick={handleCancelEdit}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prompt Text
                </label>
                <textarea
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  rows={15}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter the system prompt text..."
                />
              </div>

              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-500">
                  {editText.length} characters • Version {selectedPrompt.version + 1}
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleCancelEdit}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSavePrompt}
                    disabled={saving || editText.trim() === ''}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}