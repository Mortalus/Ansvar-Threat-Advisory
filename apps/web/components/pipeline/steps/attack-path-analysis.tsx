'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Route, AlertTriangle, TrendingUp, Shield } from 'lucide-react'
import { usePipelineStore } from '@/lib/store'

export function AttackPathAnalysis() {
  const { steps } = usePipelineStore()
  const analysisData = steps.attack_path_analysis.data

  if (!analysisData) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Attack Path Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <p className="text-muted-foreground">
              Waiting for threat refinement...
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full overflow-auto">
      <CardHeader>
        <CardTitle>Attack Path Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Route className="w-4 h-4 text-purple-500" />
            Attack Paths
          </h3>
          <div className="space-y-3">
            {analysisData.attack_paths?.map((path: any, i: number) => (
              <div key={i} className="p-4 rounded-lg bg-muted/50 border border-border">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium">{path.name}</h4>
                  <div className="flex gap-2">
                    <span className={`
                      px-2 py-1 rounded text-xs font-medium
                      ${path.likelihood === 'high' ? 'bg-orange-500/10 text-orange-600' : 
                        path.likelihood === 'medium' ? 'bg-yellow-500/10 text-yellow-600' : 
                        'bg-blue-500/10 text-blue-600'}
                    `}>
                      {path.likelihood} likelihood
                    </span>
                    <span className={`
                      px-2 py-1 rounded text-xs font-medium
                      ${path.impact === 'critical' ? 'bg-red-500/10 text-red-600' : 
                        path.impact === 'high' ? 'bg-orange-500/10 text-orange-600' : 
                        'bg-yellow-500/10 text-yellow-600'}
                    `}>
                      {path.impact} impact
                    </span>
                  </div>
                </div>
                <div className="space-y-1">
                  {path.steps?.map((step: string, j: number) => (
                    <div key={j} className="flex items-center gap-2 text-sm">
                      <span className="text-muted-foreground">{j + 1}.</span>
                      <span>{step}</span>
                      {j < path.steps.length - 1 && (
                        <span className="text-muted-foreground">→</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            Critical Paths
          </h3>
          <div className="flex flex-wrap gap-2">
            {analysisData.critical_paths?.map((path: string, i: number) => (
              <div
                key={i}
                className="px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/30"
              >
                <span className="text-sm font-medium text-red-600">{path}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Shield className="w-4 h-4 text-green-500" />
            Recommended Priorities
          </h3>
          <ol className="space-y-2">
            {analysisData.recommended_priorities?.map((priority: string, i: number) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-sm font-medium text-green-600">
                  {i + 1}.
                </span>
                <span className="text-sm">{priority}</span>
              </li>
            ))}
          </ol>
        </div>
      </CardContent>
    </Card>
  )
}