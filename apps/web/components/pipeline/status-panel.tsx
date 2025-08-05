'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Activity, FileText, AlertTriangle, Shield, Route } from 'lucide-react'
import { usePipelineStore } from '@/lib/store'

export function StatusPanel() {
  const { steps, status } = usePipelineStore()

  const getStepCount = (stepKey: string) => {
    const data = steps[stepKey as keyof typeof steps].data
    if (!data) return 0
    
    switch (stepKey) {
      case 'dfd_extraction':
        return (data.entities?.length || 0) + (data.processes?.length || 0)
      case 'threat_generation':
        return Object.values(data).reduce((acc: number, threats: any) => {
          return acc + (Array.isArray(threats) ? threats.length : 0)
        }, 0)
      case 'attack_path_analysis':
        return data.attack_paths?.length || 0
      default:
        return 0
    }
  }

  const statusItems = [
    {
      icon: FileText,
      label: 'Components Identified',
      value: `${getStepCount('dfd_extraction')} items`,
      color: 'text-blue-500',
    },
    {
      icon: AlertTriangle,
      label: 'Threats Generated',
      value: `${getStepCount('threat_generation')} threats`,
      color: 'text-yellow-500',
    },
    {
      icon: Shield,
      label: 'Quality Score',
      value: steps.threat_refinement.data?.quality_score 
        ? `${steps.threat_refinement.data.quality_score}%`
        : 'Not calculated',
      color: 'text-green-500',
    },
    {
      icon: Route,
      label: 'Attack Paths',
      value: `${getStepCount('attack_path_analysis')} paths`,
      color: 'text-purple-500',
    },
  ]

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Pipeline Status</CardTitle>
          <div className="flex items-center gap-2">
            <div className={`
              w-2 h-2 rounded-full
              ${status === 'running' ? 'bg-yellow-500 animate-pulse' : 
                status === 'completed' ? 'bg-green-500' : 
                status === 'failed' ? 'bg-red-500' : 
                'bg-gray-500'}
            `} />
            <span className="text-sm font-medium capitalize">{status}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {statusItems.map((item, i) => {
            const Icon = item.icon
            return (
              <div
                key={i}
                className="p-3 rounded-lg bg-muted/50 flex items-center gap-3"
              >
                <div className={`
                  w-8 h-8 rounded-lg bg-background flex items-center justify-center
                  ${item.color}
                `}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-muted-foreground">{item.label}</p>
                  <p className="text-sm font-medium">{item.value}</p>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}