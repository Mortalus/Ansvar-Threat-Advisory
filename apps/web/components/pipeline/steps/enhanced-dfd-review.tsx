'use client'

import { useState, useEffect, useMemo, useCallback } from 'react'
import { useStore } from '@/lib/store'
import { api } from '@/lib/api'
import { Save, CheckCircle, AlertCircle, ArrowRight, Code, Network, Copy } from 'lucide-react'
import type { DFDComponents } from '@/lib/api'

export function EnhancedDFDReview() {
  const {
    currentPipelineId,
    dfdComponents,
    setDfdComponents,
    setStepStatus,
    setStepResult,
    setCurrentStep,
    stepStates,
  } = useStore()

  const [jsonText, setJsonText] = useState('')
  const [activeTab, setActiveTab] = useState<'json' | 'mermaid'>('json')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  // Initialize JSON text when component loads
  useEffect(() => {
    if (dfdComponents && !jsonText) {
      setJsonText(JSON.stringify(dfdComponents, null, 2))
    }
  }, [dfdComponents, jsonText])

  // Parse JSON and generate Mermaid diagram
  const { parsedDFD, mermaidCode, parseError } = useMemo(() => {
    try {
      const parsed = JSON.parse(jsonText || '{}') as DFDComponents
      
      // Generate Mermaid diagram
      let diagram = 'graph TB\n'
      
      if (parsed.project_name) {
        diagram += `    %% Project: ${parsed.project_name} v${parsed.project_version || '1.0'}\n`
        diagram += `    %% Industry: ${parsed.industry_context || 'Unknown'}\n\n`
      }
      
      // Define external entities with square brackets
      if (parsed.external_entities?.length) {
        diagram += '    %% External Entities\n'
        parsed.external_entities.forEach((entity, idx) => {
          const id = `EE${idx}`
          const sanitized = entity.replace(/[^a-zA-Z0-9\s]/g, '').substring(0, 20)
          diagram += `    ${id}["${sanitized}"]\n`
          diagram += `    style ${id} fill:#ff6b6b,stroke:#c92a2a,color:#fff\n`
        })
        diagram += '\n'
      }
      
      // Define processes with rounded rectangles
      if (parsed.processes?.length) {
        diagram += '    %% Processes\n'
        parsed.processes.forEach((process, idx) => {
          const id = `P${idx}`
          const sanitized = process.replace(/[^a-zA-Z0-9\s]/g, '').substring(0, 20)
          diagram += `    ${id}("${sanitized}")\n`
          diagram += `    style ${id} fill:#4c6ef5,stroke:#364fc7,color:#fff\n`
        })
        diagram += '\n'
      }
      
      // Define assets/data stores with cylinders
      if (parsed.assets?.length) {
        diagram += '    %% Data Stores/Assets\n'
        parsed.assets.forEach((asset, idx) => {
          const id = `DS${idx}`
          const sanitized = asset.replace(/[^a-zA-Z0-9\s]/g, '').substring(0, 20)
          diagram += `    ${id}[("${sanitized}")]\n`
          diagram += `    style ${id} fill:#37b24d,stroke:#2b8a3e,color:#fff\n`
        })
        diagram += '\n'
      }
      
      // Define trust boundaries as subgraphs
      if (parsed.trust_boundaries?.length) {
        diagram += '    %% Trust Boundaries (as comments)\n'
        parsed.trust_boundaries.forEach((boundary, idx) => {
          diagram += `    %% Trust Boundary: ${boundary}\n`
        })
        diagram += '\n'
      }
      
      // Add data flows
      if (parsed.data_flows?.length) {
        diagram += '    %% Data Flows\n'
        parsed.data_flows.forEach((flow, idx) => {
          const sourceIdx = parsed.external_entities?.indexOf(flow.source) ?? -1
          const destIdx = parsed.external_entities?.indexOf(flow.destination) ?? -1
          const sourceProcessIdx = parsed.processes?.indexOf(flow.source) ?? -1
          const destProcessIdx = parsed.processes?.indexOf(flow.destination) ?? -1
          const sourceAssetIdx = parsed.assets?.indexOf(flow.source) ?? -1
          const destAssetIdx = parsed.assets?.indexOf(flow.destination) ?? -1
          
          let sourceId = null
          let destId = null
          
          // Find source ID
          if (sourceIdx !== -1) sourceId = `EE${sourceIdx}`
          else if (sourceProcessIdx !== -1) sourceId = `P${sourceProcessIdx}`
          else if (sourceAssetIdx !== -1) sourceId = `DS${sourceAssetIdx}`
          
          // Find destination ID
          if (destIdx !== -1) destId = `EE${destIdx}`
          else if (destProcessIdx !== -1) destId = `P${destProcessIdx}`
          else if (destAssetIdx !== -1) destId = `DS${destAssetIdx}`
          
          if (sourceId && destId) {
            const label = `${flow.protocol || 'Unknown'}`
            diagram += `    ${sourceId} -->|"${label}"| ${destId}\n`
          }
        })
      }

      return {
        parsedDFD: parsed,
        mermaidCode: diagram,
        parseError: null
      }
    } catch (err) {
      return {
        parsedDFD: null,
        mermaidCode: '',
        parseError: err instanceof Error ? err.message : 'Invalid JSON'
      }
    }
  }, [jsonText])

  const handleSave = async () => {
    if (!parsedDFD || !currentPipelineId) {
      setError('Invalid DFD data or missing pipeline ID')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const result = await api.reviewDFDComponents(currentPipelineId, parsedDFD)
      
      // Update store with reviewed DFD
      setDfdComponents(result.dfd_components)
      setStepStatus('dfd_review', 'complete')
      setStepResult('dfd_review', result)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save DFD review'
      setError(errorMessage)
      setStepStatus('dfd_review', 'error', errorMessage)
    } finally {
      setSaving(false)
    }
  }

  const handleContinue = () => {
    setCurrentStep('threat_generation')
  }

  const handleCopy = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
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

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">DFD Review & Edit</h2>
            <p className="text-gray-400">
              Edit the JSON to modify DFD components and see the diagram update live
            </p>
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={handleSave}
              disabled={saving || !!parseError}
              className="px-4 py-2 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
            
            {stepStates.dfd_review.status === 'complete' && (
              <button
                onClick={handleContinue}
                className="px-4 py-2 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2"
              >
                <ArrowRight className="w-4 h-4" />
                Continue to Threats
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {stepStates.dfd_review.status === 'complete' && (
        <div className="mb-6 p-4 rounded-xl bg-green-500/10 border border-green-500/30 flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-green-500" />
          <p className="text-green-400">DFD changes saved successfully!</p>
        </div>
      )}

      {parseError && (
        <div className="mb-6 p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/30 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-500" />
          <p className="text-yellow-400">JSON Parse Error: {parseError}</p>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-4 border-b border-[#2a2a4a]">
        <button
          onClick={() => setActiveTab('json')}
          className={`px-4 py-2 flex items-center gap-2 transition-all ${
            activeTab === 'json'
              ? 'text-purple-400 border-b-2 border-purple-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Code className="w-4 h-4" />
          Edit JSON
        </button>
        <button
          onClick={() => setActiveTab('mermaid')}
          className={`px-4 py-2 flex items-center gap-2 transition-all ${
            activeTab === 'mermaid'
              ? 'text-purple-400 border-b-2 border-purple-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Network className="w-4 h-4" />
          Mermaid Diagram
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'json' && (
          <div className="h-full flex flex-col">
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm text-gray-400">
                Edit the JSON below. Changes will update the Mermaid diagram in real-time.
              </p>
              <button
                onClick={() => handleCopy(jsonText)}
                className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-all flex items-center gap-2 text-sm"
              >
                {copied ? <CheckCircle className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <textarea
              value={jsonText}
              onChange={(e) => setJsonText(e.target.value)}
              className="flex-1 p-4 bg-[#0a0a0f] border border-[#2a2a4a] rounded-xl text-white font-mono text-sm resize-none focus:outline-none focus:border-purple-500"
              placeholder="Enter DFD JSON here..."
              spellCheck={false}
            />
          </div>
        )}

        {activeTab === 'mermaid' && (
          <div className="h-full flex flex-col space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-400">
                Live-generated Mermaid diagram based on your JSON edits
              </p>
              <button
                onClick={() => handleCopy(mermaidCode)}
                className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-all flex items-center gap-2 text-sm"
              >
                {copied ? <CheckCircle className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                {copied ? 'Copied!' : 'Copy Mermaid'}
              </button>
            </div>
            
            <div className="flex-1 overflow-auto">
              <pre className="p-4 bg-[#0a0a0f] rounded-xl border border-[#2a2a4a] text-sm text-gray-300 whitespace-pre-wrap">
                {mermaidCode || 'No valid data to display'}
              </pre>
            </div>
            
            <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
              <p className="text-blue-400 text-sm mb-2">
                💡 <strong>Visualization:</strong> Copy the Mermaid code above and paste it into:
              </p>
              <ul className="text-blue-400 text-sm list-disc ml-6 space-y-1">
                <li><a href="https://mermaid.live" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-300">Mermaid Live Editor</a> for immediate visualization</li>
                <li>GitHub markdown files (natively supported)</li>
                <li>VS Code with Mermaid preview extension</li>
                <li>Notion pages using mermaid code blocks</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}