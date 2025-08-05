'use client'

import { Button } from '@/components/ui/button'
import { Settings, Play, Pause, RotateCcw } from 'lucide-react'
import { usePipelineStore } from '@/lib/store'

interface PipelineHeaderProps {
  onRunPipeline: () => void
  isLoading: boolean
}

export function PipelineHeader({ onRunPipeline, isLoading }: PipelineHeaderProps) {
  const { status, reset } = usePipelineStore()

  return (
    <header className="p-6 border-b border-border">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Security Requirements Analysis</h1>
          <p className="text-muted-foreground mt-1">
            Upload your security documentation to begin threat modeling
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>

          {status === 'completed' && (
            <Button variant="outline" size="sm" onClick={reset}>
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>
          )}

          <Button
            variant="gradient"
            onClick={onRunPipeline}
            disabled={isLoading || status === 'running'}
          >
            {isLoading ? (
              <>
                <Pause className="w-4 h-4 mr-2" />
                Running...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Run Pipeline
              </>
            )}
          </Button>
        </div>
      </div>
    </header>
  )
}