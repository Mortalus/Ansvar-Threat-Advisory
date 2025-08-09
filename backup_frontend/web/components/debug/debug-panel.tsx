'use client'

import { useState } from 'react'
import { useStore } from '@/lib/store'
import { Bug, ChevronDown, ChevronUp, Play, FileText, Target, Brain, Shield } from 'lucide-react'
import { SAMPLE_DFD_COMPONENTS, SAMPLE_THREATS, SAMPLE_REFINED_THREATS, DEBUG_PIPELINE_DATA } from '@/lib/debug-data'

interface DebugPanelProps {
  setThreats: (threats: any[]) => void
  setRefinedThreats: (threats: any[]) => void
}

export function DebugPanel({ setThreats, setRefinedThreats }: DebugPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  const {
    setCurrentStep,
    setDfdComponents,
    setStepStatus,
    setStepResult,
    setPipelineId,
    setUploadedFiles,
    setDocumentText,
  } = useStore()

  const jumpToStep = (step: string, setupData?: () => void) => {
    if (setupData) setupData()
    setCurrentStep(step as any)
  }

  const setupDocumentUpload = () => {
    setPipelineId(DEBUG_PIPELINE_DATA.pipeline_id)
    setUploadedFiles(DEBUG_PIPELINE_DATA.files as any)
    setDocumentText(`Extracted ${DEBUG_PIPELINE_DATA.text_length} characters`)
    setStepStatus('document_upload', 'complete')
    setStepResult('document_upload', DEBUG_PIPELINE_DATA)
  }

  const setupDFDExtraction = () => {
    setupDocumentUpload()
    setDfdComponents(SAMPLE_DFD_COMPONENTS)
    setStepStatus('dfd_extraction', 'complete')
    setStepResult('dfd_extraction', {
      dfd_components: SAMPLE_DFD_COMPONENTS,
      validation: { quality_score: 0.85, suggestions: [] }
    })
  }

  const setupDFDReview = () => {
    setupDFDExtraction()
    setStepStatus('dfd_review', 'complete')
    setStepResult('dfd_review', {
      dfd_components: SAMPLE_DFD_COMPONENTS,
      reviewed_at: new Date().toISOString()
    })
  }

  const setupThreatGeneration = () => {
    setupDFDReview()
    setThreats(SAMPLE_THREATS)
    setStepStatus('threat_generation', 'complete')
    setStepResult('threat_generation', {
      threats: SAMPLE_THREATS,
      total_count: SAMPLE_THREATS.length,
      components_analyzed: 6,
      knowledge_sources_used: ['STRIDE', 'OWASP Top 10'],
      generated_at: new Date().toISOString()
    })
  }

  const setupThreatRefinement = () => {
    setupThreatGeneration()
    setRefinedThreats(SAMPLE_REFINED_THREATS)
    setStepStatus('threat_refinement', 'complete')
    setStepResult('threat_refinement', {
      refined_threats: SAMPLE_REFINED_THREATS,
      total_count: SAMPLE_REFINED_THREATS.length,
      refinement_stats: {
        original_count: SAMPLE_THREATS.length,
        deduplicated_count: 0,
        final_count: SAMPLE_REFINED_THREATS.length,
        risk_distribution: {
          'Critical': 2,
          'High': 2, 
          'Medium': 2,
          'Low': 0
        },
        refinement_method: 'optimized_batch'
      },
      refined_at: new Date().toISOString()
    })
  }

  if (!isExpanded) {
    return (
      <button
        onClick={() => setIsExpanded(true)}
        className="fixed bottom-4 right-4 z-50 p-3 bg-yellow-600/90 hover:bg-yellow-600 text-white rounded-full shadow-lg transition-all"
        title="Debug Mode"
      >
        <Bug className="w-5 h-5" />
      </button>
    )
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 w-80 bg-[#1a1a2e] border border-yellow-500/30 rounded-xl shadow-xl">
      <div className="flex items-center justify-between p-4 border-b border-yellow-500/20">
        <div className="flex items-center gap-2">
          <Bug className="w-4 h-4 text-yellow-400" />
          <span className="text-yellow-400 font-semibold">Debug Mode</span>
        </div>
        <button
          onClick={() => setIsExpanded(false)}
          className="text-gray-400 hover:text-white transition-colors"
        >
          <ChevronDown className="w-4 h-4" />
        </button>
      </div>
      
      <div className="p-4 space-y-3">
        <p className="text-xs text-gray-400 mb-4">
          Jump to any step with pre-loaded sample data for testing
        </p>
        
        <div className="space-y-2">
          <button
            onClick={() => jumpToStep('document_upload', setupDocumentUpload)}
            className="w-full text-left p-2 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 text-sm flex items-center gap-2 transition-colors"
          >
            <FileText className="w-3 h-3" />
            Documents Uploaded
          </button>
          
          <button
            onClick={() => jumpToStep('dfd_extraction', setupDFDExtraction)}
            className="w-full text-left p-2 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 text-sm flex items-center gap-2 transition-colors"
          >
            <Play className="w-3 h-3" />
            DFD Extracted (6 components)
          </button>
          
          <button
            onClick={() => jumpToStep('dfd_review', setupDFDReview)}
            className="w-full text-left p-2 rounded-lg bg-green-600/20 hover:bg-green-600/30 text-green-300 text-sm flex items-center gap-2 transition-colors"
          >
            <Shield className="w-3 h-3" />
            DFD Reviewed
          </button>
          
          <button
            onClick={() => jumpToStep('threat_generation', setupThreatGeneration)}
            className="w-full text-left p-2 rounded-lg bg-red-600/20 hover:bg-red-600/30 text-red-300 text-sm flex items-center gap-2 transition-colors"
          >
            <Target className="w-3 h-3" />
            Threats Generated (6 threats)
          </button>
          
          <button
            onClick={() => jumpToStep('threat_refinement', setupThreatRefinement)}
            className="w-full text-left p-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 text-sm flex items-center gap-2 transition-colors"
          >
            <Brain className="w-3 h-3" />
            Threats Refined (6 enhanced)
          </button>
        </div>
        
        <div className="pt-3 border-t border-gray-700">
          <p className="text-xs text-gray-500">
            Sample data includes realistic e-commerce threats with business context, risk scoring, and prioritization.
          </p>
        </div>
      </div>
    </div>
  )
}