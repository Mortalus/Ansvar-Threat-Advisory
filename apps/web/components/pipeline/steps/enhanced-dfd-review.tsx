'use client'

import { useState, useEffect, useMemo, useCallback } from 'react'
import { useStore } from '@/lib/store'
import { api } from '@/lib/api'
import { Save, CheckCircle, AlertCircle, ArrowRight, Code, Network, Copy, Eye, Columns } from 'lucide-react'
import type { DFDComponents } from '@/lib/api'
import { InteractiveMermaid } from './interactive-mermaid'

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
  const [activeTab, setActiveTab] = useState<'json' | 'mermaid' | 'visual' | 'split'>('visual')
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
      
      // Generate top-down flowchart style diagram for workshop presentation
      let diagram = 'flowchart TD\n'
      
      if (parsed.project_name) {
        diagram += `    %% ${parsed.project_name} v${parsed.project_version || '1.0'} - ${parsed.industry_context || 'System'}\n\n`
      }
      
      // Define all components with clean, workshop-friendly styling
      
      // External Entities with STRIDE threat modeling styling
      if (parsed.external_entities?.length) {
        parsed.external_entities.forEach((entity, idx) => {
          const id = `EE${idx}`
          const sanitized = entity.replace(/[^a-zA-Z0-9\s]/g, '').substring(0, 18)
          // Use STRIDE External Entity icon
          diagram += `    ${id}["🌐 ${sanitized}\\n(External Entity)"]\n`
          diagram += `    style ${id} fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px,color:#fff\n`
        })
        diagram += '\n'
      }
      
      // Processes with STRIDE process styling
      if (parsed.processes?.length) {
        parsed.processes.forEach((process, idx) => {
          const id = `P${idx}`
          const sanitized = process.replace(/[^a-zA-Z0-9\s]/g, '').substring(0, 18)
          // Use STRIDE Process icon
          diagram += `    ${id}("⚙️ ${sanitized}\\n(Process)")\n`
          diagram += `    style ${id} fill:#4c6ef5,stroke:#364fc7,stroke-width:3px,color:#fff\n`
        })
        diagram += '\n'
      }
      
      // Data Stores with STRIDE data store styling
      if (parsed.assets?.length) {
        parsed.assets.forEach((asset, idx) => {
          const id = `DS${idx}`
          const sanitized = asset.replace(/[^a-zA-Z0-9\s]/g, '').substring(0, 18)
          // Use STRIDE Data Store icon
          diagram += `    ${id}[("🗄️ ${sanitized}\\n(Data Store)")]\n`
          diagram += `    style ${id} fill:#37b24d,stroke:#2b8a3e,stroke-width:3px,color:#fff\n`
        })
        diagram += '\n'
      }

      // Add Trust Boundaries as simple subgraphs (after all nodes are defined)
      if (parsed.trust_boundaries?.length) {
        diagram += '    %% Trust Boundaries\n'
        parsed.trust_boundaries.forEach((boundary, idx) => {
          const boundaryId = `TB${idx}`
          const sanitizedBoundary = boundary.replace(/[^a-zA-Z0-9\s]/g, '').substring(0, 25)
          
          diagram += `    subgraph ${boundaryId}["🛡️ ${sanitizedBoundary}"]\n`
          diagram += '        direction TB\n'
          
          // Add placeholder content for visual boundaries
          diagram += `        TB${idx}_PLACEHOLDER["Security Perimeter:\\n${sanitizedBoundary}"]\n`
          diagram += `        style TB${idx}_PLACEHOLDER fill:transparent,stroke:none,color:#ffd700\n`
          
          diagram += `    end\n`
          
          // Style the boundary
          const boundaryColors = ['#2d3748', '#4a5568', '#1a202c', '#718096']
          const color = boundaryColors[idx % boundaryColors.length]
          diagram += `    style ${boundaryId} fill:${color},stroke:#ffd700,stroke-width:3px,color:#fff,stroke-dasharray: 5 5\n`
        })
        diagram += '\n'
      }
      
      // Add data flows
      if (parsed.data_flows?.length) {
        diagram += '    %% Data Flows\n'
        let flowIndex = 0 // Track flow index for styling
        
        // Helper function for fuzzy matching
        const fuzzyMatch = (needle: string, haystack: string[]): number => {
          // Try exact match first
          const exactMatch = haystack.findIndex(item => item === needle)
          if (exactMatch !== -1) return exactMatch
          
          // Try case-insensitive match
          const lowerNeedle = needle.toLowerCase()
          const caseMatch = haystack.findIndex(item => item.toLowerCase() === lowerNeedle)
          if (caseMatch !== -1) return caseMatch
          
          // Try substring match (needle contains haystack or vice versa)
          const substringMatch = haystack.findIndex(item => {
            const lowerItem = item.toLowerCase()
            return lowerNeedle.includes(lowerItem) || lowerItem.includes(lowerNeedle)
          })
          if (substringMatch !== -1) return substringMatch
          
          // Try word matching (any word in needle matches any word in haystack)
          const needleWords = lowerNeedle.split(/\s+/)
          const wordMatch = haystack.findIndex(item => {
            const itemWords = item.toLowerCase().split(/\s+/)
            return needleWords.some(nWord => itemWords.some(iWord => nWord.includes(iWord) || iWord.includes(nWord)))
          })
          
          return wordMatch
        }

        parsed.data_flows.forEach((flow, idx) => {
          // Use fuzzy matching for better component matching
          const sourceIdx = fuzzyMatch(flow.source, parsed.external_entities || [])
          const destIdx = fuzzyMatch(flow.destination, parsed.external_entities || [])
          const sourceProcessIdx = fuzzyMatch(flow.source, parsed.processes || [])
          const destProcessIdx = fuzzyMatch(flow.destination, parsed.processes || [])
          const sourceAssetIdx = fuzzyMatch(flow.source, parsed.assets || [])
          const destAssetIdx = fuzzyMatch(flow.destination, parsed.assets || [])
          
          let sourceId = null
          let destId = null
          
          // Find source ID (prefer external entities, then processes, then assets)
          if (sourceIdx !== -1) sourceId = `EE${sourceIdx}`
          else if (sourceProcessIdx !== -1) sourceId = `P${sourceProcessIdx}`
          else if (sourceAssetIdx !== -1) sourceId = `DS${sourceAssetIdx}`
          
          // Find destination ID
          if (destIdx !== -1) destId = `EE${destIdx}`
          else if (destProcessIdx !== -1) destId = `P${destProcessIdx}`
          else if (destAssetIdx !== -1) destId = `DS${destAssetIdx}`
          
          if (sourceId && destId) {
            // Clean, workshop-friendly labels
            const dataType = flow.data_description || 'Data'
            const protocol = flow.protocol || ''
            
            // Create concise label for flowchart
            let label = dataType
            if (protocol && protocol !== 'Unknown') {
              label = `${protocol}: ${dataType}`
            }
            
            // Limit label length for clean appearance
            if (label.length > 25) {
              label = label.substring(0, 22) + '...'
            }
            
            // STRIDE-based data flow styling with threat indicators
            let arrowStyle = '-->'
            let arrowColor = ''
            let threatIcon = ''
            
            // Color-code based on data sensitivity (explains red lines!)
            if (flow.data_classification === 'Confidential' || flow.data_classification === 'PII') {
              arrowStyle = '==>' // Thick arrows for sensitive data
              arrowColor = 'stroke:#ff4444,stroke-width:4px' // RED = High Risk Data
              threatIcon = '🔒' // Indicates potential I(nformation Disclosure) threats
            } else if (flow.data_classification === 'Internal') {
              arrowStyle = '-->'
              arrowColor = 'stroke:#ffa500,stroke-width:3px' // ORANGE = Medium Risk Data  
              threatIcon = '⚠️' // Indicates moderate risk
            } else {
              arrowStyle = '-->'
              arrowColor = 'stroke:#4ade80,stroke-width:2px' // GREEN = Public/Low Risk Data
              threatIcon = '✅' // Indicates lower risk
            }
            
            // Enhanced label with STRIDE threat context
            let enhancedLabel = `${threatIcon} ${label}`
            if (flow.authentication_mechanism && flow.authentication_mechanism !== 'None') {
              enhancedLabel += `\\n🔐 ${flow.authentication_mechanism}` // Shows authentication controls
            }
            
            diagram += `    ${sourceId} ${arrowStyle}|"${enhancedLabel}"| ${destId}\n`
            
            // Add link styling with STRIDE color coding
            diagram += `    linkStyle ${flowIndex} ${arrowColor}\n`
            flowIndex++
          }
        })
      }

      // Add STRIDE Threat Modeling Legend
      diagram += '\n    %% STRIDE Threat Modeling Legend\n'
      diagram += '    subgraph LEGEND["📋 STRIDE Threat Modeling Legend"]\n'
      diagram += '        direction TB\n'
      diagram += '        L1["🌐 External Entity - Potential S(poofing) threats"]\n'
      diagram += '        L2["⚙️ Process - Potential T(ampering) & E(levation) threats"]\n'  
      diagram += '        L3["🗄️ Data Store - Potential I(nfo Disclosure) & D(enial) threats"]\n'
      diagram += '        L4["🔒 RED Lines = Confidential/PII Data (High Risk)"]\n'
      diagram += '        L5["⚠️ ORANGE Lines = Internal Data (Medium Risk)"]\n'
      diagram += '        L6["✅ GREEN Lines = Public Data (Low Risk)"]\n'
      diagram += '        L7["🛡️ Trust Boundaries = Security Perimeters"]\n'
      diagram += '    end\n'
      diagram += '    style LEGEND fill:#1a1a2e,stroke:#8b5cf6,stroke-width:2px,color:#fff\n'
      diagram += '    style L1 fill:#2d1b4e,stroke:#ff6b6b,color:#fff\n'
      diagram += '    style L2 fill:#1e3a5f,stroke:#4c6ef5,color:#fff\n'
      diagram += '    style L3 fill:#1e4d3b,stroke:#37b24d,color:#fff\n'
      diagram += '    style L4 fill:#4a1e1e,stroke:#ff4444,color:#fff\n'
      diagram += '    style L5 fill:#4a3a1e,stroke:#ffa500,color:#fff\n'
      diagram += '    style L6 fill:#1e4a2e,stroke:#4ade80,color:#fff\n'
      diagram += '    style L7 fill:#3a3a1e,stroke:#ffd700,color:#fff\n'

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
          onClick={() => setActiveTab('visual')}
          className={`px-4 py-2 flex items-center gap-2 transition-all ${
            activeTab === 'visual'
              ? 'text-purple-400 border-b-2 border-purple-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Eye className="w-4 h-4" />
          Interactive Diagram
        </button>
        <button
          onClick={() => setActiveTab('split')}
          className={`px-4 py-2 flex items-center gap-2 transition-all ${
            activeTab === 'split'
              ? 'text-purple-400 border-b-2 border-purple-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Columns className="w-4 h-4" />
          Workshop View
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
          Mermaid Code
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

        {activeTab === 'visual' && (
          <div className="h-full">
            {mermaidCode && !parseError ? (
              <InteractiveMermaid 
                chart={mermaidCode} 
                title={parsedDFD?.project_name || 'DFD Diagram'} 
              />
            ) : (
              <div className="h-full flex items-center justify-center bg-gray-500/10 border border-gray-500/30 rounded-xl">
                <div className="text-center p-8">
                  <Network className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <p className="text-lg font-semibold mb-2 text-gray-400">No Diagram Available</p>
                  <p className="text-gray-500">
                    {parseError ? 'Fix JSON errors to see diagram' : 'Enter valid JSON data to generate diagram'}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'split' && (
          <div className="h-full flex gap-4">
            {/* JSON Editor Side */}
            <div className="w-1/2 flex flex-col">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Edit DFD Components</h3>
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
              {parseError && (
                <div className="mt-2 p-2 bg-red-500/10 border border-red-500/30 rounded-lg">
                  <p className="text-red-400 text-sm">{parseError}</p>
                </div>
              )}
            </div>

            {/* Interactive Diagram Side */}
            <div className="w-1/2 flex flex-col">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-white">Live Diagram Preview</h3>
                <p className="text-sm text-gray-400">Changes update in real-time</p>
              </div>
              <div className="flex-1 border border-[#2a2a4a] rounded-xl overflow-hidden">
                {mermaidCode && !parseError ? (
                  <InteractiveMermaid 
                    chart={mermaidCode} 
                    title={parsedDFD?.project_name || 'DFD Diagram'} 
                  />
                ) : (
                  <div className="h-full flex items-center justify-center bg-gray-500/10">
                    <div className="text-center p-6">
                      <Network className="w-12 h-12 text-gray-500 mx-auto mb-3" />
                      <p className="text-gray-400 text-sm">
                        {parseError ? 'Fix JSON to see diagram' : 'Waiting for valid JSON'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
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
                💡 <strong>Tip:</strong> Use the Interactive Diagram tab for better visualization, or copy this code to:
              </p>
              <ul className="text-blue-400 text-sm list-disc ml-6 space-y-1">
                <li><a href="https://mermaid.live" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-300">Mermaid Live Editor</a></li>
                <li>GitHub markdown files • VS Code • Notion pages</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}