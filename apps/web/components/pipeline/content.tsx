'use client'

import { useState } from 'react'
import { usePipelineStore } from '@/lib/store'
import { Upload, FileText, X } from 'lucide-react'

export function PipelineContent() {
  const { currentStep, uploadedFile, setUploadedFile } = usePipelineStore()
  const [isDragging, setIsDragging] = useState(false)

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
    if (files.length > 0) {
      setUploadedFile(files[0])
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      setUploadedFile(files[0])
    }
  }

  if (currentStep === 'document_upload') {
    return (
      <div className="flex-1 p-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="card-bg rounded-2xl p-8 h-full relative overflow-hidden">
            <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-purple-600/10 to-blue-600/10 rounded-full blur-3xl" />
            
            {!uploadedFile ? (
              <div
                className={`
                  relative z-10 h-full min-h-[500px] border-2 border-dashed rounded-xl
                  flex flex-col items-center justify-center transition-all
                  ${isDragging ? 'border-purple-500 bg-purple-500/10' : 'border-[#2a2a4a] hover:border-purple-500/50'}
                `}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                />
                
                <div className="w-24 h-24 rounded-2xl gradient-purple-blue flex items-center justify-center mb-6 shadow-lg">
                  <Upload className="w-12 h-12 text-white" />
                </div>
                
                <h3 className="text-xl font-semibold mb-2">
                  Drop files here or click to upload
                </h3>
                <p className="text-gray-400 mb-6">
                  Supports PDF, DOCX, and TXT files up to 10MB
                </p>
                
                <label htmlFor="file-upload">
                  <span className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all cursor-pointer inline-block">
                    Choose Files
                  </span>
                </label>
              </div>
            ) : (
              <div className="relative z-10 h-full flex items-center justify-center">
                <div className="w-full max-w-md">
                  <div className="p-4 rounded-xl bg-[#252541] flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl gradient-purple-blue flex items-center justify-center">
                      <FileText className="w-6 h-6 text-white" />
                    </div>
                    
                    <div className="flex-1">
                      <p className="font-medium">{uploadedFile.name}</p>
                      <p className="text-sm text-gray-400">
                        {(uploadedFile.size / 1024).toFixed(2)} KB
                      </p>
                    </div>
                    
                    <button
                      onClick={() => setUploadedFile(null)}
                      className="p-2 hover:bg-[#2a2a4a] rounded-lg transition-all"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div className="mt-6 p-4 rounded-xl bg-green-500/10 border border-green-500/30">
                    <p className="text-sm text-green-400">
                      ✓ Document ready for processing
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-1">
          <div className="card-bg rounded-2xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold">Pipeline Status</h3>
              <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-xs font-medium flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse"></span>
                Active
              </span>
            </div>
            
            <div className="space-y-4">
              {[
                { label: 'Components Identified', value: '0 entities, 0 processes', icon: '📊' },
                { label: 'Threats Generated', value: '0 threats across 0 categories', icon: '🎯' },
                { label: 'Quality Score', value: 'Not yet calculated', icon: '🔍' },
                { label: 'Attack Paths', value: '0 paths analyzed', icon: '🛤️' },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3 p-3 bg-[#252541]/50 rounded-xl">
                  <span className="text-2xl">{item.icon}</span>
                  <div className="flex-1">
                    <p className="text-xs text-gray-400">{item.label}</p>
                    <p className="text-sm font-medium">{item.value}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 p-8">
      <div className="card-bg rounded-2xl p-8 h-full">
        <h2 className="text-xl font-bold mb-4">
          {currentStep.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
        </h2>
        <div className="text-gray-400">
          Step content will be displayed here
        </div>
      </div>
    </div>
  )
}
