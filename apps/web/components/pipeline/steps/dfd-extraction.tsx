'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Network, Database, User, ArrowRight } from 'lucide-react'
import { usePipelineStore } from '@/lib/store'

export function DFDExtraction() {
  const { steps } = usePipelineStore()
  const dfdData = steps.dfd_extraction.data

  if (!dfdData) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>DFD Extraction</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <p className="text-muted-foreground">
              Waiting for document upload...
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Data Flow Diagram Components</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <h3 className="text-sm font-semibold mb-3 text-muted-foreground">Entities</h3>
          <div className="flex flex-wrap gap-2">
            {dfdData.entities?.map((entity: string, i: number) => (
              <div
                key={i}
                className="px-3 py-2 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center gap-2"
              >
                <User className="w-4 h-4 text-blue-500" />
                <span className="text-sm">{entity}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold mb-3 text-muted-foreground">Processes</h3>
          <div className="flex flex-wrap gap-2">
            {dfdData.processes?.map((process: string, i: number) => (
              <div
                key={i}
                className="px-3 py-2 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center gap-2"
              >
                <Network className="w-4 h-4 text-purple-500" />
                <span className="text-sm">{process}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold mb-3 text-muted-foreground">Data Stores</h3>
          <div className="flex flex-wrap gap-2">
            {dfdData.data_stores?.map((store: string, i: number) => (
              <div
                key={i}
                className="px-3 py-2 rounded-lg bg-green-500/10 border border-green-500/30 flex items-center gap-2"
              >
                <Database className="w-4 h-4 text-green-500" />
                <span className="text-sm">{store}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold mb-3 text-muted-foreground">Data Flows</h3>
          <div className="space-y-2">
            {dfdData.data_flows?.map((flow: any, i: number) => (
              <div
                key={i}
                className="flex items-center gap-2 p-2 rounded-lg bg-muted/50"
              >
                <span className="text-sm font-medium">{flow.from}</span>
                <ArrowRight className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">{flow.to}</span>
                <span className="text-xs text-muted-foreground ml-auto">
                  {flow.data}
                </span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}