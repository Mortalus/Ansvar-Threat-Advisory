'use client'

import { usePipelineStore } from '@/lib/store'
import { DocumentUpload } from './steps/document-upload'
import { DFDExtraction } from './steps/dfd-extraction'
import { ThreatGeneration } from './steps/threat-generation'
import { ThreatRefinement } from './steps/threat-refinement'
import { AttackPathAnalysis } from './steps/attack-path-analysis'
import { StatusPanel } from './status-panel'

export function PipelineContent() {
  const { currentStep } = usePipelineStore()

  const renderStep = () => {
    switch (currentStep) {
      case 'document_upload':
        return <DocumentUpload />
      case 'dfd_extraction':
        return <DFDExtraction />
      case 'threat_generation':
        return <ThreatGeneration />
      case 'threat_refinement':
        return <ThreatRefinement />
      case 'attack_path_analysis':
        return <AttackPathAnalysis />
      default:
        return <DocumentUpload />
    }
  }

  return (
    <div className="flex-1 p-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
        <div className="lg:col-span-2">{renderStep()}</div>
        <div className="lg:col-span-1">
          <StatusPanel />
        </div>
      </div>
    </div>
  )
}