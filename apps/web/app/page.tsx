'use client'

import { useState, useEffect } from 'react'
import { Shield, FileText, Network, AlertTriangle, RefreshCw, Route, Settings, Play, Upload, X } from 'lucide-react'

export default function Home() {
  const [currentStep, setCurrentStep] = useState('document_upload')
  const [isLoading, setIsLoading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  const steps = [
    { id: 'document_upload', name: 'Document Upload', icon: FileText },
    { id: 'dfd_extraction', name: 'DFD Extraction', icon: Network },
    { id: 'threat_generation', name: 'Threat Generation', icon: AlertTriangle },
    { id: 'threat_refinement', name: 'Threat Refinement', icon: RefreshCw },
    { id: 'attack_path_analysis', name: 'Attack Path Analysis', icon: Route },
  ]

  const handleRunPipeline = () => {
    setIsLoading(true)
    setTimeout(() => setIsLoading(false), 2000)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) setUploadedFile(files[0])
  }

  return (
    <div className="flex h-screen" style={{ background: 'var(--bg-dark)' }}>
      {/* Background Effect */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full opacity-20" 
          style={{ background: 'radial-gradient(circle, #667eea 0%, transparent 70%)' }} />
        <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full opacity-20"
          style={{ background: 'radial-gradient(circle, #764ba2 0%, transparent 70%)' }} />
      </div>

      {/* Sidebar */}
      <aside className="w-80 card-bg border-r" style={{ borderColor: 'var(--border-color)' }}>
        <div className="p-8">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-xl gradient-purple-blue flex items-center justify-center shadow-lg">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <span className="text-xl font-bold gradient-text">ThreatModel AI</span>
          </div>

          <nav className="space-y-2">
            {steps.map((step, index) => {
              const Icon = step.icon
              const isActive = currentStep === step.id

              return (
                <button
                  key={step.id}
                  onClick={() => setCurrentStep(step.id)}
                  className="w-full relative flex items-center gap-4 p-4 rounded-xl transition-all"
                  style={{
                    background: isActive ? 'var(--bg-hover)' : 'transparent',
                    border: isActive ? '1px solid rgba(102, 126, 234, 0.3)' : '1px solid transparent',
                  }}
                >
                  {isActive && (
                    <div className="absolute inset-0 rounded-xl opacity-10 gradient-purple-blue" />
                  )}
                  
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-sm font-semibold relative z-10 ${
                    isActive ? 'gradient-purple-blue text-white shadow-lg' : ''
                  }`}
                  style={{
                    background: !isActive ? 'var(--bg-hover)' : '',
                    color: !isActive ? 'var(--text-secondary)' : '',
                  }}>
                    {index + 1}
                  </div>

                  <div className="flex-1 text-left relative z-10">
                    <div className="font-semibold text-sm">{step.name}</div>
                    <div className="text-xs opacity-60 mt-0.5">Pending</div>
                  </div>
                </button>
              )
            })}
          </nav>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="p-8">
          <div className="card-bg rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold">Security Requirements Analysis</h1>
                <p className="opacity-60 mt-1">Upload your security documentation to begin threat modeling</p>
              </div>
              <div className="flex items-center gap-3">
                <button className="px-5 py-2.5 rounded-xl flex items-center gap-2 transition-all"
                  style={{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)' }}>
                  <Settings className="w-4 h-4" />
                  Settings
                </button>
                <button
                  onClick={handleRunPipeline}
                  disabled={isLoading}
                  className="px-6 py-2.5 gradient-purple-blue text-white rounded-xl shadow-lg hover:scale-105 transition-all disabled:opacity-50 flex items-center gap-2 font-medium"
                >
                  <Play className="w-4 h-4" />
                  {isLoading ? 'Running...' : 'Run Pipeline'}
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 p-8 pt-0">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
            {/* Main Panel */}
            <div className="lg:col-span-2">
              <div className="card-bg rounded-2xl p-8 h-full relative overflow-hidden">
                <div className="absolute top-0 right-0 w-80 h-80 opacity-10"
                  style={{ background: 'radial-gradient(circle, #764ba2 0%, transparent 70%)' }} />
                
                {!uploadedFile ? (
                  <div
                    className={`relative z-10 h-full min-h-[400px] border-2 border-dashed rounded-xl flex flex-col items-center justify-center transition-all cursor-pointer ${
                      isDragging ? 'border-purple-500 bg-purple-500 bg-opacity-10' : ''
                    }`}
                    style={{ borderColor: isDragging ? '#667eea' : 'var(--border-color)' }}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    <div className="w-24 h-24 rounded-2xl gradient-purple-blue flex items-center justify-center mb-6 shadow-lg">
                      <Upload className="w-12 h-12 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2">Drop files here or click to upload</h3>
                    <p className="opacity-60 mb-6">Supports PDF, DOCX, and TXT files up to 10MB</p>
                    <button className="px-6 py-3 gradient-purple-blue text-white rounded-xl shadow-lg">
                      Choose Files
                    </button>
                  </div>
                ) : (
                  <div className="relative z-10 flex items-center justify-center h-full">
                    <div className="w-full max-w-md">
                      <div className="p-4 rounded-xl flex items-center gap-4" style={{ background: 'var(--bg-hover)' }}>
                        <div className="w-12 h-12 rounded-xl gradient-purple-blue flex items-center justify-center">
                          <FileText className="w-6 h-6 text-white" />
                        </div>
                        <div className="flex-1">
                          <p className="font-medium">{uploadedFile.name}</p>
                          <p className="text-sm opacity-60">{(uploadedFile.size / 1024).toFixed(2)} KB</p>
                        </div>
                        <button onClick={() => setUploadedFile(null)} className="p-2 rounded-lg hover:bg-black hover:bg-opacity-20">
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Status Panel */}
            <div className="lg:col-span-1">
              <div className="card-bg rounded-2xl p-6 h-full">
                <h3 className="text-lg font-semibold mb-6">Pipeline Status</h3>
                <div className="space-y-4">
                  {[
                    { label: 'Components Identified', value: '0 entities', icon: '📊' },
                    { label: 'Threats Generated', value: '0 threats', icon: '🎯' },
                    { label: 'Quality Score', value: 'Not calculated', icon: '🔍' },
                    { label: 'Attack Paths', value: '0 paths', icon: '🛤️' },
                  ].map((item, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-xl" style={{ background: 'var(--bg-hover)' }}>
                      <span className="text-2xl">{item.icon}</span>
                      <div className="flex-1">
                        <p className="text-xs opacity-60">{item.label}</p>
                        <p className="text-sm font-medium">{item.value}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
