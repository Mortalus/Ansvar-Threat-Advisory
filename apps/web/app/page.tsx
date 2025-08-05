'use client'

import { useState, useEffect } from 'react'
import { PipelineSidebar } from '@/components/pipeline/sidebar'
import { PipelineHeader } from '@/components/pipeline/header'
import { PipelineContent } from '@/components/pipeline/content'
import { usePipelineStore } from '@/lib/store'
import { api } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

export default function Home() {
  const { 
    currentStep, 
    pipelineId, 
    setPipelineId,
    setStatus 
  } = usePipelineStore()
  
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    // Create pipeline on mount
    initializePipeline()
  }, [])

  const initializePipeline = async () => {
    try {
      const response = await api.createPipeline()
      setPipelineId(response.pipeline_id)
      toast({
        title: "Pipeline Created",
        description: "Ready to begin threat modeling",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create pipeline",
        variant: "destructive",
      })
    }
  }

  const handleRunPipeline = async () => {
    if (!pipelineId) {
      toast({
        title: "Error",
        description: "No pipeline initialized",
        variant: "destructive",
      })
      return
    }

    setIsLoading(true)
    setStatus('running')

    try {
      // Execute all steps sequentially
      const steps = [
        'document_upload',
        'dfd_extraction',
        'threat_generation',
        'threat_refinement',
        'attack_path_analysis'
      ]

      for (const step of steps) {
        await api.executeStep(pipelineId, step)
        toast({
          title: "Step Completed",
          description: `${step.replace('_', ' ')} completed successfully`,
        })
      }

      setStatus('completed')
      toast({
        title: "Pipeline Complete",
        description: "All steps executed successfully",
      })
    } catch (error) {
      setStatus('failed')
      toast({
        title: "Pipeline Failed",
        description: "An error occurred during execution",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-purple-500/10 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl" />
      </div>
      
      <PipelineSidebar />
      
      <main className="flex-1 flex flex-col">
        <PipelineHeader onRunPipeline={handleRunPipeline} isLoading={isLoading} />
        <PipelineContent />
      </main>
    </div>
  )
}