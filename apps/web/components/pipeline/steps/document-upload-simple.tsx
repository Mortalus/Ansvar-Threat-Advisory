// apps/web/components/pipeline/steps/document-upload-simple.tsx
'use client'

import { useState, useCallback, useRef } from 'react'
import { Upload, FileText, X } from 'lucide-react'
import { usePipelineStore } from '@/lib/store'

export function DocumentUploadSimple() {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const { uploadedFile, setUploadedFile, pipelineId, setStepData, setStepStatus } = usePipelineStore()
  
  // Use a ref for the file input
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
  }, [])

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    console.log('File input changed')
    const files = e.target.files
    if (files && files.length > 0) {
      await handleFileUpload(files[0])
    }
  }, [])

  const handleFileUpload = async (file: File) => {
    console.log('Handling file upload:', file.name)
    
    // Validate file type
    const validExtensions = ['.pdf', '.docx', '.txt']
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    
    if (!validExtensions.includes(fileExtension)) {
      alert('Invalid file type. Please upload a PDF, DOCX, or TXT file')
      return
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      alert('File too large. Please upload a file smaller than 10MB')
      return
    }

    setIsUploading(true)
    setUploadedFile(file)

    try {
      // Read file content
      const content = await readFileContent(file)
      console.log('File content read, length:', content.length)
      
      // Store in pipeline store
      setStepData('document_upload', { 
        filename: file.name, 
        content: content,
        size: file.size,
        type: file.type 
      })
      setStepStatus('document_upload', 'completed')

      alert(`File uploaded successfully: ${file.name}`)
    } catch (error) {
      console.error('Upload error:', error)
      alert('Failed to upload file')
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
    
    // Reset the file input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // Function to trigger file input click
  const handleButtonClick = () => {
    console.log('Button clicked, triggering file input')
    fileInputRef.current?.click()
  }

  return (
    <div className="h-full bg-gray-800 rounded-lg p-8">
      <div className="h-full flex items-center justify-center">
        {!uploadedFile ? (
          <div
            className={`
              w-full h-full border-2 border-dashed rounded-lg
              flex flex-col items-center justify-center
              transition-all
              ${isDragging ? 'border-purple-500 bg-purple-500/10' : 'border-gray-600 hover:border-purple-500/50'}
            `}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
              disabled={isUploading}
            />
            
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center mb-6">
              <Upload className="w-10 h-10 text-white" />
            </div>
            
            <h3 className="text-xl font-semibold mb-2 text-white">
              {isUploading ? 'Uploading...' : 'Drop files here or click to upload'}
            </h3>
            <p className="text-gray-400 mb-6">
              Supports PDF, DOCX, and TXT files up to 10MB
            </p>
            
            {/* Method 1: Button with onClick */}
            <button
              onClick={handleButtonClick}
              disabled={isUploading}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Choose Files (Click)
            </button>
            
            {/* Method 2: Label with htmlFor */}
            <div className="mt-4">
              <input
                id="file-upload-2"
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileSelect}
                className="hidden"
                disabled={isUploading}
              />
              <label
                htmlFor="file-upload-2"
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer inline-block transition-colors"
              >
                Choose Files (Label)
              </label>
            </div>
            
            {/* Method 3: Direct label wrap */}
            <label className="mt-4 cursor-pointer">
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileSelect}
                className="hidden"
                disabled={isUploading}
              />
              <span className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 inline-block transition-colors">
                Choose Files (Wrap)
              </span>
            </label>
          </div>
        ) : (
          <div className="w-full max-w-md">
            <div className="p-4 rounded-lg bg-gray-700 flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
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
                className="p-2 hover:bg-gray-600 rounded transition-colors"
              >
                <X className="w-4 h-4 text-white" />
              </button>
            </div>
            
            <div className="mt-6 p-4 rounded-lg bg-green-500/10 border border-green-500/30">
              <p className="text-sm text-green-400">
                ✓ Document ready for processing
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}