# Create the sidebar component
cat << 'EOF' > components/pipeline/sidebar.tsx
'use client'

import { usePipelineStore } from '@/lib/store'

export function PipelineSidebar() {
  const { currentStep, setCurrentStep } = usePipelineStore()

  const steps = [
    { id: 'document_upload', name: 'Document Upload' },
    { id: 'dfd_extraction', name: 'DFD Extraction' },
    { id: 'threat_generation', name: 'Threat Generation' },
    { id: 'threat_refinement', name: 'Threat Refinement' },
    { id: 'attack_path_analysis', name: 'Attack Path Analysis' },
  ]

  return (
    <aside className="w-80 bg-gray-900 border-r border-gray-800 p-6">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-white">ThreatModel AI</h1>
      </div>
      <nav className="space-y-2">
        {steps.map((step, index) => (
          <button
            key={step.id}
            onClick={() => setCurrentStep(step.id)}
            className={`w-full text-left p-3 rounded-lg ${
              currentStep === step.id ? 'bg-gray-800 text-white' : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            <span className="mr-3">{index + 1}.</span>
            {step.name}
          </button>
        ))}
      </nav>
    </aside>
  )
}
EOF

# Create the header component
cat << 'EOF' > components/pipeline/header.tsx
'use client'

interface PipelineHeaderProps {
  onRunPipeline: () => void
  isLoading: boolean
}

export function PipelineHeader({ onRunPipeline, isLoading }: PipelineHeaderProps) {
  return (
    <header className="p-6 border-b border-gray-800">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Security Requirements Analysis</h1>
          <p className="text-gray-400 mt-1">Upload your security documentation to begin threat modeling</p>
        </div>
        <button
          onClick={onRunPipeline}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? 'Running...' : 'Run Pipeline'}
        </button>
      </div>
    </header>
  )
}
EOF

# Create the content component
cat << 'EOF' > components/pipeline/content.tsx
'use client'

import { usePipelineStore } from '@/lib/store'

export function PipelineContent() {
  const { currentStep } = usePipelineStore()

  return (
    <div className="flex-1 p-6">
      <div className="bg-gray-900 rounded-lg p-6 h-full">
        <h2 className="text-xl font-bold text-white mb-4">
          {currentStep.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
        </h2>
        <div className="text-gray-400">
          Step content will be displayed here
        </div>
      </div>
    </div>
  )
}
EOF

# Create the toaster component
cat << 'EOF' > components/ui/toaster.tsx
'use client'

import { useToast } from '@/hooks/use-toast'

export function Toaster() {
  const { toasts } = useToast()

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="px-4 py-3 rounded-lg shadow-lg bg-gray-800 text-white border border-gray-700"
        >
          {toast.title && <div className="font-semibold">{toast.title}</div>}
          {toast.description && <div className="text-sm mt-1">{toast.description}</div>}
        </div>
      ))}
    </div>
  )
}
EOF

# Create the toast hook
cat << 'EOF' > hooks/use-toast.ts
import { useState, useEffect } from 'react'

type Toast = {
  id: string
  title?: string
  description?: string
  variant?: 'default' | 'destructive'
}

let toastCount = 0
const toasts: Toast[] = []
const listeners: ((toasts: Toast[]) => void)[] = []

function emitChange() {
  for (let listener of listeners) {
    listener(toasts)
  }
}

export function toast(props: Omit<Toast, 'id'>) {
  const id = String(++toastCount)
  const toast = { ...props, id }
  toasts.push(toast)
  emitChange()
  
  setTimeout(() => {
    const index = toasts.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.splice(index, 1)
      emitChange()
    }
  }, 5000)
  
  return { id }
}

export function useToast() {
  const [, setVersion] = useState(0)
  
  useEffect(() => {
    const listener = () => setVersion(v => v + 1)
    listeners.push(listener)
    return () => {
      const index = listeners.indexOf(listener)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }, [])
  
  return { toasts, toast }
}
EOF

# Update the API client
cat << 'EOF' > lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = {
  createPipeline: async () => {
    const response = await fetch(`${API_URL}/api/pipeline/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    return response.json()
  },

  executeStep: async (pipelineId: string, step: string, data?: any) => {
    const response = await fetch(`${API_URL}/api/pipeline/${pipelineId}/step/${step}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input_data: data }),
    })
    return response.json()
  },

  uploadDocument: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await fetch(`${API_URL}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    })
    return response.json()
  },
}
EOF

# Verify all files were created
echo "Checking created files:"
ls -la components/pipeline/
ls -la components/ui/
ls -la hooks/
ls -la lib/