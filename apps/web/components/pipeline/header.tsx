'use client'

import { Settings, Play, Pause, RotateCcw } from 'lucide-react'
import { usePipelineStore } from '@/lib/store'

interface PipelineHeaderProps {
  onRunPipeline: () => void
  isLoading: boolean
}

export function PipelineHeader({ onRunPipeline, isLoading }: PipelineHeaderProps) {
  const { status, reset } = usePipelineStore()

  return (
    <header className="p-8">
      <div className="card-bg rounded-2xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Security Requirements Analysis</h1>
            <p className="text-gray-400 mt-1">
              Upload your security documentation to begin threat modeling
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button className="px-5 py-2.5 bg-[#252541] border border-[#2a2a4a] rounded-xl text-gray-300 hover:bg-[#2a2a4a] transition-all flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Settings
            </button>

            {status === 'completed' && (
              <button 
                onClick={reset} 
                className="px-5 py-2.5 bg-[#252541] border border-[#2a2a4a] rounded-xl text-gray-300 hover:bg-[#2a2a4a] transition-all flex items-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                Reset
              </button>
            )}

            <button
              onClick={onRunPipeline}
              disabled={isLoading || status === 'running'}
              className="px-6 py-2.5 gradient-purple-blue text-white rounded-xl hover:shadow-lg hover:scale-105 transition-all disabled:opacity-50 disabled:hover:scale-100 flex items-center gap-2 font-medium"
            >
              {isLoading ? (
                <>
                  <Pause className="w-4 h-4" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Pipeline
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
