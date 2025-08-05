'use client'

import { usePipelineStore } from '@/lib/store'
import { Shield, FileText, Network, AlertTriangle, RefreshCw, Route } from 'lucide-react'

export function PipelineSidebar() {
  const { currentStep, steps: stepStatuses, setCurrentStep } = usePipelineStore()

  const steps = [
    { id: 'document_upload', name: 'Document Upload', icon: FileText, description: 'Upload security documentation' },
    { id: 'dfd_extraction', name: 'DFD Extraction', icon: Network, description: 'Extract system components' },
    { id: 'threat_generation', name: 'Threat Generation', icon: AlertTriangle, description: 'Generate STRIDE threats' },
    { id: 'threat_refinement', name: 'Threat Refinement', icon: RefreshCw, description: 'Quality check & enhancement' },
    { id: 'attack_path_analysis', name: 'Attack Path Analysis', icon: Route, description: 'Analyze attack chains' },
  ]

  return (
    <aside className="w-80 bg-[#1a1a2e] border-r border-[#2a2a4a] p-8 flex flex-col gap-8">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl gradient-purple-blue flex items-center justify-center shadow-lg">
          <Shield className="w-7 h-7 text-white" />
        </div>
        <span className="text-xl font-bold gradient-text">ThreatModel AI</span>
      </div>

      <nav className="flex flex-col gap-2">
        {steps.map((step, index) => {
          const stepData = stepStatuses[step.id as keyof typeof stepStatuses]
          const status = stepData?.status || 'pending'
          const Icon = step.icon
          const isActive = currentStep === step.id
          const isCompleted = status === 'completed'
          const isRunning = status === 'running'

          return (
            <button
              key={step.id}
              onClick={() => setCurrentStep(step.id as any)}
              className={`
                relative flex items-center gap-4 p-4 rounded-xl transition-all duration-300
                hover:bg-[#252541] group
                ${isActive ? 'bg-[#252541] border border-purple-500/30' : ''}
                ${isCompleted ? 'border-green-500/30' : ''}
              `}
            >
              {isActive && (
                <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-purple-600/10 to-blue-600/10" />
              )}
              
              <div className={`
                w-10 h-10 rounded-xl flex items-center justify-center text-sm font-semibold relative z-10 transition-all
                ${isCompleted ? 'bg-green-500 text-white' : 
                  isActive ? 'gradient-purple-blue text-white shadow-lg' : 
                  isRunning ? 'bg-yellow-500 text-white animate-pulse' : 
                  'bg-[#252541] text-gray-400 group-hover:text-white'}
              `}>
                {isCompleted ? '✓' : index + 1}
              </div>

              <div className="flex-1 text-left relative z-10">
                <div className="font-semibold text-sm">{step.name}</div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {isRunning ? 'In Progress...' : status === 'pending' ? 'Pending' : step.description}
                </div>
              </div>

              {isRunning && (
                <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
              )}
            </button>
          )
        })}
      </nav>

      <div className="mt-auto p-4 rounded-xl bg-[#252541]/50">
        <div className="text-xs text-gray-500 mb-2">Pipeline Status</div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm font-medium">Ready</span>
        </div>
      </div>
    </aside>
  )
}