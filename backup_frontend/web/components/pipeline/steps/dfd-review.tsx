'use client'

import { useState, useEffect } from 'react'
import { useStore } from '@/lib/store'
import { api } from '@/lib/api'
import { Edit3, Save, CheckCircle, AlertCircle, ArrowRight, Eye, FileText } from 'lucide-react'
import type { DFDComponents, DataFlow } from '@/lib/api'
import { DFDVisualization } from './dfd-visualization'

interface EditableDFDComponents extends DFDComponents {
  // Add any additional editable fields if needed
}

export function DFDReviewStep() {
  const {
    currentPipelineId,
    dfdComponents,
    setDfdComponents,
    setStepStatus,
    setStepResult,
    setCurrentStep,
    stepStates,
  } = useStore()

  const [editing, setEditing] = useState(false)
  const [editedDFD, setEditedDFD] = useState<EditableDFDComponents | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeView, setActiveView] = useState<'edit' | 'visualize'>('edit')

  // Initialize edited DFD when component loads
  useEffect(() => {
    if (dfdComponents && !editedDFD) {
      setEditedDFD(dfdComponents)
    }
  }, [dfdComponents, editedDFD])

  const handleSave = async () => {
    if (!editedDFD || !currentPipelineId) return

    setSaving(true)
    setError(null)

    try {
      const result = await api.reviewDFDComponents(currentPipelineId, editedDFD)
      
      // Update store with reviewed DFD
      setDfdComponents(result.dfd_components)
      setStepStatus('dfd_review', 'complete')
      setStepResult('dfd_review', result)
      
      // Auto-advance to next step
      setCurrentStep('agent_config')
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save DFD review'
      setError(errorMessage)
      setStepStatus('dfd_review', 'error', errorMessage)
    } finally {
      setSaving(false)
    }
  }

  const handleEdit = () => {
    setEditing(true)
    setStepStatus('dfd_review', 'in_progress')
  }

  const updateField = (field: keyof EditableDFDComponents, value: any) => {
    if (!editedDFD) return
    
    setEditedDFD({
      ...editedDFD,
      [field]: value
    })
  }

  const updateArrayField = (field: keyof EditableDFDComponents, index: number, value: string) => {
    if (!editedDFD) return
    
    const currentArray = editedDFD[field] as string[]
    const updatedArray = [...currentArray]
    updatedArray[index] = value
    
    setEditedDFD({
      ...editedDFD,
      [field]: updatedArray
    })
  }

  const addArrayItem = (field: keyof EditableDFDComponents) => {
    if (!editedDFD) return
    
    const currentArray = editedDFD[field] as string[]
    setEditedDFD({
      ...editedDFD,
      [field]: [...currentArray, '']
    })
  }

  const removeArrayItem = (field: keyof EditableDFDComponents, index: number) => {
    if (!editedDFD) return
    
    const currentArray = editedDFD[field] as string[]
    const updatedArray = currentArray.filter((_, i) => i !== index)
    
    setEditedDFD({
      ...editedDFD,
      [field]: updatedArray
    })
  }

  const updateDataFlow = (index: number, field: keyof DataFlow, value: string) => {
    if (!editedDFD) return
    
    const updatedFlows = [...editedDFD.data_flows]
    updatedFlows[index] = {
      ...updatedFlows[index],
      [field]: value
    }
    
    setEditedDFD({
      ...editedDFD,
      data_flows: updatedFlows
    })
  }

  const addDataFlow = () => {
    if (!editedDFD) return
    
    const newFlow: DataFlow = {
      source: '',
      destination: '',
      data_description: '',
      data_classification: 'Public',
      protocol: 'HTTPS',
      authentication_mechanism: 'None'
    }
    
    setEditedDFD({
      ...editedDFD,
      data_flows: [...editedDFD.data_flows, newFlow]
    })
  }

  const removeDataFlow = (index: number) => {
    if (!editedDFD) return
    
    const updatedFlows = editedDFD.data_flows.filter((_, i) => i !== index)
    setEditedDFD({
      ...editedDFD,
      data_flows: updatedFlows
    })
  }

  if (!dfdComponents) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center p-8 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
          <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <p className="text-lg font-semibold mb-2">DFD Extraction Required</p>
          <p className="text-gray-400 mb-4">
            Please complete DFD extraction first before reviewing components.
          </p>
          <button
            onClick={() => setCurrentStep('dfd_extraction')}
            className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all"
          >
            Go to DFD Extraction
          </button>
        </div>
      </div>
    )
  }

  const currentDFD = editing ? editedDFD : dfdComponents

  return (
    <div className="h-full flex flex-col">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">DFD Review</h2>
            <p className="text-gray-400">
              Review and edit the extracted DFD components before proceeding to threat generation
            </p>
          </div>
          
          <div className="flex gap-3">
            {/* View Toggle */}
            <div className="flex gap-1 bg-[#1a1a2e] rounded-lg p-1">
              <button
                onClick={() => setActiveView('edit')}
                className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-2 ${
                  activeView === 'edit' 
                    ? 'bg-purple-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <FileText className="w-4 h-4" />
                Edit
              </button>
              <button
                onClick={() => setActiveView('visualize')}
                className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-2 ${
                  activeView === 'visualize' 
                    ? 'bg-purple-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <Eye className="w-4 h-4" />
                Visualize
              </button>
            </div>

            {/* Action Buttons */}
            {activeView === 'edit' && (
              <>
                {!editing ? (
                  <button
                    onClick={handleEdit}
                    className="px-4 py-2 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2"
                  >
                    <Edit3 className="w-4 h-4" />
                    Edit DFD
                  </button>
                ) : (
                  <>
                    <button
                      onClick={handleSave}
                      disabled={saving}
                      className="px-4 py-2 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-all flex items-center gap-2 disabled:opacity-50"
                    >
                      <Save className="w-4 h-4" />
                      {saving ? 'Saving...' : 'Save & Continue'}
                    </button>
                    <button
                      onClick={() => {
                        setEditing(false)
                        setEditedDFD(dfdComponents)
                        setStepStatus('dfd_review', 'pending')
                      }}
                      className="px-4 py-2 bg-gray-600 text-white rounded-xl hover:bg-gray-700 transition-all"
                    >
                      Cancel
                    </button>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {stepStates.dfd_review.status === 'complete' && (
        <div className="mb-6 p-4 rounded-xl bg-green-500/10 border border-green-500/30 flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-green-500" />
          <p className="text-green-400">DFD review completed successfully!</p>
        </div>
      )}

      <div className="flex-1 overflow-auto">
        {activeView === 'visualize' ? (
          <DFDVisualization dfdComponents={currentDFD} />
        ) : (
          <div className="space-y-6">
          {/* Project Information */}
          <div className="card-bg rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4">Project Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Project Name</label>
                <input
                  type="text"
                  value={currentDFD?.project_name || ''}
                  onChange={(e) => updateField('project_name', e.target.value)}
                  disabled={!editing}
                  className="w-full p-3 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-white disabled:opacity-50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Version</label>
                <input
                  type="text"
                  value={currentDFD?.project_version || ''}
                  onChange={(e) => updateField('project_version', e.target.value)}
                  disabled={!editing}
                  className="w-full p-3 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-white disabled:opacity-50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Industry Context</label>
                <input
                  type="text"
                  value={currentDFD?.industry_context || ''}
                  onChange={(e) => updateField('industry_context', e.target.value)}
                  disabled={!editing}
                  className="w-full p-3 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-white disabled:opacity-50"
                />
              </div>
            </div>
          </div>

          {/* External Entities */}
          <div className="card-bg rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">External Entities</h3>
              {editing && (
                <button
                  onClick={() => addArrayItem('external_entities')}
                  className="px-3 py-1 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all text-sm"
                >
                  Add Entity
                </button>
              )}
            </div>
            <div className="space-y-2">
              {currentDFD?.external_entities.map((entity, index) => (
                <div key={index} className="flex items-center gap-2">
                  <input
                    type="text"
                    value={entity}
                    onChange={(e) => updateArrayField('external_entities', index, e.target.value)}
                    disabled={!editing}
                    className="flex-1 p-2 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-white disabled:opacity-50"
                  />
                  {editing && (
                    <button
                      onClick={() => removeArrayItem('external_entities', index)}
                      className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Processes */}
          <div className="card-bg rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Processes</h3>
              {editing && (
                <button
                  onClick={() => addArrayItem('processes')}
                  className="px-3 py-1 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all text-sm"
                >
                  Add Process
                </button>
              )}
            </div>
            <div className="space-y-2">
              {currentDFD?.processes.map((process, index) => (
                <div key={index} className="flex items-center gap-2">
                  <input
                    type="text"
                    value={process}
                    onChange={(e) => updateArrayField('processes', index, e.target.value)}
                    disabled={!editing}
                    className="flex-1 p-2 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-white disabled:opacity-50"
                  />
                  {editing && (
                    <button
                      onClick={() => removeArrayItem('processes', index)}
                      className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Assets */}
          <div className="card-bg rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Assets</h3>
              {editing && (
                <button
                  onClick={() => addArrayItem('assets')}
                  className="px-3 py-1 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all text-sm"
                >
                  Add Asset
                </button>
              )}
            </div>
            <div className="space-y-2">
              {currentDFD?.assets.map((asset, index) => (
                <div key={index} className="flex items-center gap-2">
                  <input
                    type="text"
                    value={asset}
                    onChange={(e) => updateArrayField('assets', index, e.target.value)}
                    disabled={!editing}
                    className="flex-1 p-2 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-white disabled:opacity-50"
                  />
                  {editing && (
                    <button
                      onClick={() => removeArrayItem('assets', index)}
                      className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Trust Boundaries */}
          <div className="card-bg rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Trust Boundaries</h3>
              {editing && (
                <button
                  onClick={() => addArrayItem('trust_boundaries')}
                  className="px-3 py-1 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all text-sm"
                >
                  Add Boundary
                </button>
              )}
            </div>
            <div className="space-y-2">
              {currentDFD?.trust_boundaries.map((boundary, index) => (
                <div key={index} className="flex items-center gap-2">
                  <input
                    type="text"
                    value={boundary}
                    onChange={(e) => updateArrayField('trust_boundaries', index, e.target.value)}
                    disabled={!editing}
                    className="flex-1 p-2 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-white disabled:opacity-50"
                  />
                  {editing && (
                    <button
                      onClick={() => removeArrayItem('trust_boundaries', index)}
                      className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Data Flows */}
          <div className="card-bg rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Data Flows</h3>
              {editing && (
                <button
                  onClick={addDataFlow}
                  className="px-3 py-1 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all text-sm"
                >
                  Add Flow
                </button>
              )}
            </div>
            <div className="space-y-4">
              {currentDFD?.data_flows.map((flow, index) => (
                <div key={index} className="p-4 bg-[#1a1a2e] rounded-lg border border-[#2a2a4a]">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-1">Source</label>
                      <input
                        type="text"
                        value={flow.source}
                        onChange={(e) => updateDataFlow(index, 'source', e.target.value)}
                        disabled={!editing}
                        className="w-full p-2 bg-[#0a0a0f] border border-[#2a2a4a] rounded-lg text-white disabled:opacity-50"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-1">Destination</label>
                      <input
                        type="text"
                        value={flow.destination}
                        onChange={(e) => updateDataFlow(index, 'destination', e.target.value)}
                        disabled={!editing}
                        className="w-full p-2 bg-[#0a0a0f] border border-[#2a2a4a] rounded-lg text-white disabled:opacity-50"
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-1">Protocol</label>
                      <input
                        type="text"
                        value={flow.protocol}
                        onChange={(e) => updateDataFlow(index, 'protocol', e.target.value)}
                        disabled={!editing}
                        className="w-full p-2 bg-[#0a0a0f] border border-[#2a2a4a] rounded-lg text-white disabled:opacity-50"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-1">Data Classification</label>
                      <select
                        value={flow.data_classification}
                        onChange={(e) => updateDataFlow(index, 'data_classification', e.target.value)}
                        disabled={!editing}
                        className="w-full p-2 bg-[#0a0a0f] border border-[#2a2a4a] rounded-lg text-white disabled:opacity-50"
                      >
                        <option value="Public">Public</option>
                        <option value="Internal">Internal</option>
                        <option value="Confidential">Confidential</option>
                        <option value="Restricted">Restricted</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-1">Authentication</label>
                      <input
                        type="text"
                        value={flow.authentication_mechanism}
                        onChange={(e) => updateDataFlow(index, 'authentication_mechanism', e.target.value)}
                        disabled={!editing}
                        className="w-full p-2 bg-[#0a0a0f] border border-[#2a2a4a] rounded-lg text-white disabled:opacity-50"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">Data Description</label>
                    <textarea
                      value={flow.data_description}
                      onChange={(e) => updateDataFlow(index, 'data_description', e.target.value)}
                      disabled={!editing}
                      rows={2}
                      className="w-full p-2 bg-[#0a0a0f] border border-[#2a2a4a] rounded-lg text-white disabled:opacity-50 resize-none"
                    />
                  </div>
                  
                  {editing && (
                    <div className="mt-3 flex justify-end">
                      <button
                        onClick={() => removeDataFlow(index)}
                        className="px-3 py-1 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors text-sm"
                      >
                        Remove Flow
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
        )}
      </div>
    </div>
  )
} 