'use client'

import { useState, useMemo } from 'react'
import { useStore } from '@/lib/store'
import { Code, Network, Copy, CheckCircle } from 'lucide-react'
import type { DFDComponents } from '@/lib/api'

interface DFDVisualizationProps {
  dfdComponents: DFDComponents | null
}

export function DFDVisualization({ dfdComponents }: DFDVisualizationProps) {
  const [activeTab, setActiveTab] = useState<'json' | 'mermaid'>('json')
  const [copied, setCopied] = useState(false)

  // Define helper function before useMemo
  const findComponentId = (name: string, dfd: DFDComponents): string | null => {
    // Check external entities
    const eeIndex = dfd.external_entities.indexOf(name)
    if (eeIndex !== -1) return `EE${eeIndex}`
    
    // Check processes
    const pIndex = dfd.processes.indexOf(name)
    if (pIndex !== -1) return `P${pIndex}`
    
    // Check assets
    const dsIndex = dfd.assets.indexOf(name)
    if (dsIndex !== -1) return `DS${dsIndex}`
    
    return null
  }

  const mermaidCode = useMemo(() => {
    if (!dfdComponents) return ''

    let diagram = 'graph TB\n'
    diagram += '    %% Project: ' + dfdComponents.project_name + ' v' + dfdComponents.project_version + '\n'
    diagram += '    %% Industry: ' + dfdComponents.industry_context + '\n\n'
    
    // Define external entities with square brackets
    diagram += '    %% External Entities\n'
    dfdComponents.external_entities.forEach((entity, idx) => {
      const id = `EE${idx}`
      diagram += `    ${id}[${entity}]\n`
      diagram += `    style ${id} fill:#ff6b6b,stroke:#c92a2a,color:#fff\n`
    })
    diagram += '\n'
    
    // Define processes with rounded rectangles
    diagram += '    %% Processes\n'
    dfdComponents.processes.forEach((process, idx) => {
      const id = `P${idx}`
      diagram += `    ${id}(${process})\n`
      diagram += `    style ${id} fill:#4c6ef5,stroke:#364fc7,color:#fff\n`
    })
    diagram += '\n'
    
    // Define assets/data stores with cylinders
    diagram += '    %% Data Stores/Assets\n'
    dfdComponents.assets.forEach((asset, idx) => {
      const id = `DS${idx}`
      diagram += `    ${id}[(${asset})]\n`
      diagram += `    style ${id} fill:#37b24d,stroke:#2b8a3e,color:#fff\n`
    })
    diagram += '\n'
    
    // Define trust boundaries as subgraphs
    diagram += '    %% Trust Boundaries\n'
    dfdComponents.trust_boundaries.forEach((boundary, idx) => {
      diagram += `    subgraph TB${idx}[${boundary}]\n`
      diagram += `        direction TB\n`
      diagram += `    end\n`
      diagram += `    style TB${idx} fill:none,stroke:#ffd43b,stroke-width:2px,stroke-dasharray:5 5\n`
    })
    diagram += '\n'
    
    // Add data flows
    diagram += '    %% Data Flows\n'
    dfdComponents.data_flows.forEach((flow, idx) => {
      // Map source and destination to their IDs
      const sourceId = findComponentId(flow.source, dfdComponents)
      const destId = findComponentId(flow.destination, dfdComponents)
      
      if (sourceId && destId) {
        const label = `${flow.protocol}\\n${flow.data_classification}\\n${flow.data_description.substring(0, 30)}${flow.data_description.length > 30 ? '...' : ''}`
        diagram += `    ${sourceId} -->|${label}| ${destId}\n`
      }
    })

    return diagram
  }, [dfdComponents])

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
      <div className="p-6 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
        <p className="text-yellow-400">No DFD components available for visualization</p>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
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
          JSON View
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
      <div className="flex-1 overflow-auto">
        {activeTab === 'json' && (
          <div className="relative">
            <button
              onClick={() => handleCopy(JSON.stringify(dfdComponents, null, 2))}
              className="absolute top-4 right-4 p-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-all flex items-center gap-2"
            >
              {copied ? (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  Copy JSON
                </>
              )}
            </button>
            <pre className="p-6 bg-[#0a0a0f] rounded-xl border border-[#2a2a4a] overflow-auto">
              <code className="text-sm text-gray-300">
                {JSON.stringify(dfdComponents, null, 2)}
              </code>
            </pre>
          </div>
        )}

        {activeTab === 'mermaid' && (
          <div className="space-y-4">
            <div className="relative">
              <button
                onClick={() => handleCopy(mermaidCode)}
                className="absolute top-4 right-4 p-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-all flex items-center gap-2 z-10"
              >
                {copied ? (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copy Mermaid
                  </>
                )}
              </button>
              <pre className="p-6 bg-[#0a0a0f] rounded-xl border border-[#2a2a4a] overflow-auto">
                <code className="text-sm text-gray-300">
                  {mermaidCode}
                </code>
              </pre>
            </div>
            
            <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
              <p className="text-blue-400 text-sm">
                💡 <strong>Tip:</strong> Copy the Mermaid code above and paste it into:
              </p>
              <ul className="mt-2 ml-6 text-blue-400 text-sm list-disc">
                <li>Mermaid Live Editor: <a href="https://mermaid.live" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-300">mermaid.live</a></li>
                <li>GitHub markdown files (supported natively)</li>
                <li>Notion pages (using code blocks with mermaid language)</li>
                <li>VS Code with Mermaid preview extension</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}