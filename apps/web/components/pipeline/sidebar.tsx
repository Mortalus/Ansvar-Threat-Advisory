'use client'

import { cn } from '@/lib/utils'
import { usePipelineStore } from '@/lib/store'
import { Shield, FileText, Network, AlertTriangle, RefreshCw, Route } from 'lucide-react'

const steps = [
  {
    id: 'document_upload',
    name: 'Document Upload',
    icon: FileText,
    description: 'Upload security documentation',
  },
  {
    id: 'dfd_extraction',
    name: 'DFD Extraction',
    icon: Network,
    description: 'Extract system components',
  },
  {
    id: 'threat_generation',
    name: 'Threat Generation',
    icon: AlertTriangle,
    description: 'Generate STRIDE threats',
  },
  {
    id: 'threat_refinement',
    name: 'Threat Refinement',
    icon: RefreshCw,
    description: 'Quality check & enhancement',
  },
  {
    id: 'attack_path_analysis',
    name: 'Attack Path Analysis',
    icon: Route,
    description: 'Analyze attack chains',
  },
]

export function PipelineSidebar() {
  const { currentStep, steps: stepStatuses, setCurrentStep } = usePipelineStore()

  return (
    <aside className="w-80 bg-card border-r border-border p-6 flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
          <Shield className="w-6 h-6 text-white" />
        </div>
        <span className="text-xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
          ThreatModel AI
        </span>
      </div>

      <nav className="flex flex-col gap-2">
        {steps.map((step, index) => {
          const status = stepStatuses[step.id as keyof typeof stepStatuses].status
          const Icon = step.icon
          const isActive = currentStep === step.id
          const isCompleted = status === 'completed'
          const isRunning = status === 'running'

          return (
            <button
              key={step.id}
              onClick={() => setCurrentStep(step.id as any)}
              className={cn(
                'relative flex items-center gap-3 p-3 rounded-lg transition-all',
                'hover:bg-accent/50',
                isActive && 'bg-accent border border-purple-500/30',
                isCompleted && 'border-green-500/30'
              )}
            >
              {isActive && (
                <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-purple-600/10 to-blue-600/10" />
              )}
              
              <div
                className={cn(
                  'w-9 h-9 rounded-lg flex items-center justify-center text-sm font-semibold relative z-10',
                  isCompleted
                    ? 'bg-green-500 text-white'
                    : isActive
                    ? 'bg-gradient-to-br from-purple-600 to-blue-600 text-white'
                    : isRunning
                    ? 'bg-yellow-500 text-white animate-pulse'
                    : 'bg-muted text-muted-foreground'
                )}
              >
                {isCompleted ? '✓' : index + 1}
              </div>

              <div className="flex-1 text-left relative z-10">
                <div className="font-medium text-sm">{step.name}</div>
                <div className="text-xs text-muted-foreground">
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

      <div className="mt-auto p-4 rounded-lg bg-muted/50">
        <div className="text-xs text-muted-foreground mb-2">Pipeline Status</div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm font-medium">Ready</span>
        </div>
      </div>
    </aside>
  )
}