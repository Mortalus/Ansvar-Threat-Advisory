// apps/web/components/pipeline/steps/document-upload.tsx
'use client'

import { useState, useCallback, useRef } from 'react'
import { Upload, FileText, X } from 'lucide-react'
import { usePipelineStore } from '@/lib/store'
import { api } from '@/lib/api'

export function DocumentUpload() {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { uploadedFile, setUploadedFile, pipelineId, setPipelineId, setStepData, setStepStatus } = usePipelineStore()
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      await handleFileUpload(files[0])
    }
  }, [pipelineId, setPipelineId])

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      await handleFileUpload(files[0])
    }
  }, [pipelineId, setPipelineId])

  const handleFileUpload = async (file: File) => {
    setError(null)
    
    // Validate file type
    const validExtensions = ['.pdf', '.docx', '.txt']
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    
    if (!validExtensions.includes(fileExtension)) {
      setError('Invalid file type. Please upload a PDF, DOCX, or TXT file')
      return
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setError('File too large. Please upload a file smaller than 10MB')
      return
    }

    setIsUploading(true)
    setUploadedFile(file)

    try {
      // Read file content
      const content = await readFileContent(file)
      
      let currentPipelineId = pipelineId
      
      // Create pipeline if none exists
      if (!currentPipelineId) {
        const newPipeline = await api.createPipeline('Threat Model Analysis')
        currentPipelineId = newPipeline.pipeline_id
        setPipelineId(currentPipelineId)
      }
      
      // Execute document upload step
      await api.executeStep(currentPipelineId, 'document_upload', {
        filename: file.name,
        content: content,
        type: file.type || 'text/plain'
      })
      
      setStepData('document_upload', { 
        filename: file.name, 
        content: content,
        size: file.size,
        type: file.type 
      })
      setStepStatus('document_upload', 'completed')
    } catch (error) {
      console.error('Upload error:', error)
      setError(error instanceof Error ? error.message : 'Failed to upload document')
      setUploadedFile(null)
    } finally {
      setIsUploading(false)
    }
  }

  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        resolve(e.target?.result as string)
      }
      reader.onerror = reject
      reader.readAsText(file)
    })
  }

  const removeFile = () => {
    setUploadedFile(null)
    setStepData('document_upload', null)
    setStepStatus('document_upload', 'pending')
    setError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const triggerFileInput = () => {
    fileInputRef.current?.click()
  }

  const runDFDExtraction = async () => {
    if (!pipelineId) return
    
    setError(null)
    try {
      await api.executeStep(pipelineId, 'dfd_extraction', {})
      usePipelineStore.getState().setCurrentStep('dfd_extraction')
      usePipelineStore.getState().setStepStatus('dfd_extraction', 'running')
    } catch (error) {
      setError('Failed to start DFD extraction')
    }
  }

  return (
    <div className="h-full bg-[#1a1a2e] rounded-2xl p-8 relative overflow-hidden">
      {/* Background gradient effect */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-purple-600/10 to-blue-600/10 rounded-full blur-3xl" />
      
      <div className="relative z-10 h-full flex flex-col">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-white mb-2">Document Upload</h2>
          <p className="text-gray-400">Upload your system architecture or design document to begin threat modeling</p>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        <div className="flex-1 flex items-center justify-center">
          {!uploadedFile ? (
            <div
              className={`
                w-full max-w-2xl h-96 border-2 border-dashed rounded-xl
                flex flex-col items-center justify-center
                transition-all cursor-pointer
                ${isDragging ? 'border-purple-500 bg-purple-500/10' : 'border-[#2a2a4a] hover:border-purple-500/50'}
              `}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={triggerFileInput}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
                disabled={isUploading}
              />
              
              <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center mb-6 shadow-lg">
                <Upload className="w-12 h-12 text-white" />
              </div>
              
              <h3 className="text-xl font-semibold mb-2 text-white">
                {isUploading ? 'Uploading...' : 'Drop files here or click to upload'}
              </h3>
              <p className="text-gray-400 mb-6">
                Supports PDF, DOCX, and TXT files up to 10MB
              </p>
              
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  triggerFileInput()
                }}
                disabled={isUploading}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium rounded-xl hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Choose Files
              </button>
            </div>
          ) : (
            <div className="w-full max-w-md">
              <div className="p-4 rounded-xl bg-[#252541] flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                
                <div className="flex-1">
                  <p className="font-medium text-white">{uploadedFile.name}</p>
                  <p className="text-sm text-gray-400">
                    {(uploadedFile.size / 1024).toFixed(2)} KB
                  </p>
                </div>
                
                <button
                  onClick={removeFile}
                  className="p-2 hover:bg-[#2a2a4a] rounded-lg transition-colors"
                >
                  <X className="w-4 h-4 text-gray-400 hover:text-white" />
                </button>
              </div>
              
              <div className="mt-6 p-4 rounded-xl bg-green-500/10 border border-green-500/30">
                <p className="text-sm text-green-400">
                  ✓ Document ready for processing
                </p>
              </div>
              
              <button
                onClick={runDFDExtraction}
                className="w-full mt-6 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium rounded-xl hover:shadow-lg transition-all"
              >
                Proceed to DFD Extraction →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}