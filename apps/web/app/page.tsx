// apps/web/app/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { PipelineSidebar } from '@/components/pipeline/sidebar'
import { StatusPanel } from '@/components/pipeline/status-panel'
import { DocumentUpload } from '@/components/pipeline/steps/document-upload'
import { usePipelineStore } from '@/lib/store'
import { Settings, Play } from 'lucide-react'
import { api } from '@/lib/api'

export default function Home() {
  const { currentStep, pipelineId, uploadedFile } = usePipelineStore()
  const [isLoading, setIsLoading] = useState(false)

  const handleRunPipeline = async () => {
    if (!pipelineId || !uploadedFile) {
      alert('Please upload a document first')
      return
    }

    setIsLoading(true)
    try {
      // Run the full pipeline
      await api.runPipeline(pipelineId, {
        filename: uploadedFile.name,
        content: await readFileContent(uploadedFile),
        type: uploadedFile.type
      })
    } catch (error) {
      console.error('Pipeline execution failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => resolve(e.target?.result as string)
      reader.onerror = reject
      reader.readAsText(file)
    })
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 'document_upload':
        return <DocumentUpload />
      case 'dfd_extraction':
        return (
          <div className="h-full card-bg rounded-2xl p-8 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-purple-600/10 to-blue-600/10 rounded-full blur-3xl" />
            <div className="relative z-10">
              <h2 className="text-2xl font-bold mb-4 gradient-text">DFD Extraction</h2>
              <p className="text-gray-400 mb-6">Extracting Data Flow Diagram components from your document...</p>
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
              </div>
            </div>
          </div>
        )
      case 'threat_generation':
        return (
          <div className="h-full card-bg rounded-2xl p-8 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-purple-600/10 to-blue-600/10 rounded-full blur-3xl" />
            <div className="relative z-10">
              <h2 className="text-2xl font-bold mb-4 gradient-text">Threat Generation</h2>
              <p className="text-gray-400 mb-6">Generating threats using STRIDE methodology...</p>
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
              </div>
            </div>
          </div>
        )
      case 'threat_refinement':
        return (
          <div className="h-full card-bg rounded-2xl p-8 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-purple-600/10 to-blue-600/10 rounded-full blur-3xl" />
            <div className="relative z-10">
              <h2 className="text-2xl font-bold mb-4 gradient-text">Threat Refinement</h2>
              <p className="text-gray-400 mb-6">Refining and enhancing identified threats...</p>
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
              </div>
            </div>
          </div>
        )
      case 'attack_path_analysis':
        return (
          <div className="h-full card-bg rounded-2xl p-8 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-purple-600/10 to-blue-600/10 rounded-full blur-3xl" />
            <div className="relative z-10">
              <h2 className="text-2xl font-bold mb-4 gradient-text">Attack Path Analysis</h2>
              <p className="text-gray-400 mb-6">Analyzing potential attack paths...</p>
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
              </div>
            </div>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className="flex h-screen" style={{ background: 'var(--bg-dark)' }}>
      {/* Background Effects */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full opacity-20" 
          style={{ background: 'radial-gradient(circle, #667eea 0%, transparent 70%)' }} />
        <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full opacity-20"
          style={{ background: 'radial-gradient(circle, #764ba2 0%, transparent 70%)' }} />
      </div>

      {/* Sidebar */}
      <PipelineSidebar />

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative">
        {/* Header */}
        <header className="p-6 border-b" style={{ borderColor: 'var(--border-color)' }}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Security Requirements Analysis</h1>
              <p className="text-gray-400 mt-1">Upload your security documentation to begin threat modeling</p>
            </div>
            <div className="flex items-center gap-4">
              <button 
                className="p-2 rounded-lg hover:bg-gray-800 transition-colors"
                title="Settings"
              >
                <Settings className="w-5 h-5" />
              </button>
              <button
                onClick={handleRunPipeline}
                disabled={isLoading || !uploadedFile}
                className="px-6 py-2 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="w-4 h-4" />
                {isLoading ? 'Running...' : 'Run Pipeline'}
              </button>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 p-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
            {/* Main Panel */}
            <div className="lg:col-span-2">
              {renderStepContent()}
            </div>

            {/* Status Panel */}
            <div className="lg:col-span-1">
              <StatusPanel />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}