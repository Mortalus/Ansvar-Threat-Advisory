'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertTriangle, Shield, Lock, Eye, Zap, TrendingUp } from 'lucide-react'
import { usePipelineStore } from '@/lib/store'

const threatIcons = {
  spoofing: Shield,
  tampering: Lock,
  repudiation: Eye,
  information_disclosure: Eye,
  denial_of_service: Zap,
  elevation_of_privilege: TrendingUp,
}

const severityColors = {
  low: 'bg-blue-500/10 border-blue-500/30 text-blue-600',
  medium: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-600',
  high: 'bg-orange-500/10 border-orange-500/30 text-orange-600',
  critical: 'bg-red-500/10 border-red-500/30 text-red-600',
}

export function ThreatGeneration() {
  const { steps } = usePipelineStore()
  const threatsData = steps.threat_generation.data

  if (!threatsData) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Threat Generation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <p className="text-muted-foreground">
              Waiting for DFD extraction...
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full overflow-auto">
      <CardHeader>
        <CardTitle>Generated Threats (STRIDE)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {Object.entries(threatsData).map(([category, threats]) => {
          if (!Array.isArray(threats)) return null
          const Icon = threatIcons[category as keyof typeof threatIcons] || AlertTriangle
          
          return (
            <div key={category}>
              <div className="flex items-center gap-2 mb-3">
                <Icon className="w-5 h-5 text-purple-500" />
                <h3 className="font-semibold capitalize">
                  {category.replace(/_/g, ' ')}
                </h3>
                <span className="text-xs text-muted-foreground">
                  ({threats.length} threats)
                </span>
              </div>
              
              <div className="space-y-2">
                {threats.map((threat: any, i: number) => (
                  <div
                    key={i}
                    className="p-3 rounded-lg bg-muted/50 border border-border"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-sm">{threat.title}</h4>
                      <span
                        className={`
                          px-2 py-1 rounded text-xs font-medium
                          ${severityColors[threat.severity as keyof typeof severityColors]}
                        `}
                      >
                        {threat.severity}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">
                      {threat.description}
                    </p>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>Component: {threat.affected_component}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}