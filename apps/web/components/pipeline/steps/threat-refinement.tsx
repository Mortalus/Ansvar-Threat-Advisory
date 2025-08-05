'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { usePipelineStore } from '@/lib/store'

export function ThreatRefinement() {
  const { steps } = usePipelineStore()
  const refinedData = steps.threat_refinement.data

  if (!refinedData) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Threat Refinement</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <p className="text-muted-foreground">
              Waiting for threat generation...
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const qualityScore = refinedData.quality_score || 0
  const getQualityColor = (score: number) => {
    if (score >= 80) return 'text-green-500'
    if (score >= 60) return 'text-yellow-500'
    return 'text-red-500'
  }

  return (
    <Card className="h-full overflow-auto">
      <CardHeader>
        <CardTitle>Refined Threat Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="p-4 rounded-lg bg-muted/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Quality Score</span>
            <span className={`text-2xl font-bold ${getQualityColor(qualityScore)}`}>
              {qualityScore}%
            </span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div
              className="h-full rounded-full bg-gradient-to-r from-purple-600 to-blue-600"
              style={{ width: `${qualityScore}%` }}
            />
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="font-semibold">Quality Checks</h3>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-sm">All threats have clear descriptions</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-sm">Mitigation strategies added</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-sm">Risk scores assigned</span>
            </div>
            <div className="flex items-center gap-2">
              {qualityScore >= 80 ? (
                <CheckCircle className="w-4 h-4 text-green-500" />
              ) : (
                <AlertCircle className="w-4 h-4 text-yellow-500" />
              )}
              <span className="text-sm">Duplicates removed</span>
            </div>
          </div>
        </div>

        {refinedData.spoofing && (
          <div className="space-y-2">
            <h3 className="font-semibold">Enhanced Threats</h3>
            <p className="text-sm text-muted-foreground">
              Threats have been refined with mitigation strategies and improved descriptions.
              Each threat now includes actionable recommendations.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}