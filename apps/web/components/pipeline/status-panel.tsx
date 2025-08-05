// apps/web/components/pipeline/status-panel.tsx
'use client'

import { Activity, FileText, AlertTriangle, Shield, Route } from 'lucide-react'
import { usePipelineStore } from '@/lib/store'

export function StatusPanel() {
  const { steps, pipelineId } = usePipelineStore()

  const getStepCount = (stepKey: string) => {
    const data = steps[stepKey as keyof typeof steps]?.data
    if (!data) return 0
    
    switch (stepKey) {
      case 'dfd_extraction':
        return (data.dfd_components?.external_entities?.length || 0) + 
               (data.dfd_components?.processes?.length || 0)
      case 'threat_generation':
        return data.threats?.length || 0
      case 'attack_path_analysis':
        return data.attack_paths?.length || 0
      default:
        return 0
    }
  }

  const getStatus = () => {
    if (!pipelineId) return 'idle'
    const runningStep = Object.values(steps).find(s => s.status === 'running')
    if (runningStep) return 'running'
    const failedStep = Object.values(steps).find(s => s.status === 'failed')
    if (failedStep) return 'failed'
    const completedSteps = Object.values(steps).filter(s => s.status === 'completed')
    if (completedSteps.length === 5) return 'completed'
    return 'in_progress'
  }

  const status = getStatus()

  const statusItems = [
    {
      icon: FileText,
      label: 'Components Identified',
      value: `${getStepCount('dfd_extraction')} items`,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
      iconBg: 'bg-blue-500/20'
    },
    {
      icon: AlertTriangle,
      label: 'Threats Generated',
      value: `${getStepCount('threat_generation')} threats`,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-500/10',
      iconBg: 'bg-yellow-500/20'
    },
    {
      icon: Shield,
      label: 'Quality Score',
      value: steps.threat_refinement?.data?.quality_score 
        ? `${steps.threat_refinement.data.quality_score}%`
        : 'Not calculated',
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      iconBg: 'bg-green-500/20'
    },
    {
      icon: Route,
      label: 'Attack Paths',
      value: `${getStepCount('attack_path_analysis')} paths`,
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/10',
      iconBg: 'bg-purple-500/20'
    },
  ]

  return (
    <div className="h-full card-bg rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Pipeline Status</h3>
        <div className="flex items-center gap-2">
          <div className={`
            w-2 h-2 rounded-full
            ${status === 'running' ? 'bg-yellow-500 animate-pulse' : 
              status === 'completed' ? 'bg-green-500' : 
              status === 'failed' ? 'bg-red-500' : 
              'bg-gray-500'}
          `} />
          <span className="text-sm font-medium capitalize">
            {status.replace('_', ' ')}
          </span>
        </div>
      </div>

      <div className="space-y-4">
        {statusItems.map((item, i) => {
          const Icon = item.icon
          return (
            <div
              key={i}
              className={`p-3 rounded-xl ${item.bgColor} border border-gray-800 flex items-center gap-3`}
            >
              <div className={`
                w-10 h-10 rounded-lg ${item.iconBg} flex items-center justify-center
                ${item.color}
              `}>
                <Icon className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <p className="text-xs text-gray-400">{item.label}</p>
                <p className="text-sm font-medium">{item.value}</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Progress Bar */}
      <div className="mt-6 pt-6 border-t border-gray-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-400">Overall Progress</span>
          <span className="text-xs font-medium">
            {Math.round((Object.values(steps).filter(s => s.status === 'completed').length / 5) * 100)}%
          </span>
        </div>
        <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
          <div 
            className="h-full gradient-purple-blue transition-all duration-500"
            style={{ 
              width: `${(Object.values(steps).filter(s => s.status === 'completed').length / 5) * 100}%` 
            }}
          />
        </div>
      </div>
    </div>
  )
}