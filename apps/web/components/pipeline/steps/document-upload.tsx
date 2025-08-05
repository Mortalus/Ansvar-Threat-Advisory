'use client'

import { useState, useCallback } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Upload, FileText, X } from 'lucide-react'
import { usePipelineStore } from '@/lib/store'
import { api } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

export function DocumentUpload() {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const { uploadedFile, setUploadedFile, pipelineId, setStepData, setStepStatus } = usePipelineStore()
  const { toast } = useToast()

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
    const files = e.target.files
    if (files && files.length > 0) {
      await handleFileUpload(files[0])
    }
  }, [])

  const handleFileUpload = async (file: File) => {
    setIsUploading(true)
    setUploadedFile(file)

    try {
      // Upload to backend
      const response = await api.uploadDocument(file)
      
      // Execute document upload step
      if (pipelineId) {
        await api.executeStep(pipelineId, 'document_upload', {
          filename: file.name,
          content: response.full_content
        })
        
        setStepData('document_upload', response)
        setStepStatus('document_upload', 'completed')
      }

      toast({
        title: "Upload Successful",
        description: `${file.name} has been uploaded and processed`,
      })
    } catch (error) {
      toast({
        title: "Upload Failed",
        description: "Failed to upload document",
        variant: "destructive",
      })
      setUploadedFile(null)
    } finally {
      setIsUploading(false)
    }
  }

  const removeFile = () => {
    setUploadedFile(null)
    setStepData('document_upload', null)
    setStepStatus('document_upload', 'pending')
  }

  return (
    <Card className="h-full relative overflow-hidden">
      <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-purple-600/10 to-blue-600/10 rounded-full blur-3xl" />
      
      <CardContent className="p-8 h-full flex items-center justify-center relative z-10">
        {!uploadedFile ? (
          <div
            className={`
              w-full h-full border-2 border-dashed rounded-lg
              flex flex-col items-center justify-center
              transition-all cursor-pointer
              ${isDragging ? 'border-purple-500 bg-purple-500/10' : 'border-border hover:border-purple-500/50'}
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
              disabled={isUploading}
            />
            
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center mb-6">
              <Upload className="w-10 h-10 text-white" />
            </div>
            
            <h3 className="text-xl font-semibold mb-2">
              {isUploading ? 'Uploading...' : 'Drop files here or click to upload'}
            </h3>
            <p className="text-muted-foreground mb-6">
              Supports PDF, DOCX, and TXT files up to 10MB
            </p>
            
            <label htmlFor="file-upload">
              <Button variant="gradient" disabled={isUploading}>
                Choose Files
              </Button>
            </label>
          </div>
        ) : (
          <div className="w-full max-w-md">
            <div className="p-4 rounded-lg bg-muted/50 flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
                <FileText className="w-6 h-6 text-white" />
              </div>
              
              <div className="flex-1">
                <p className="font-medium">{uploadedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  {(uploadedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
              
              <Button
                variant="ghost"
                size="icon"
                onClick={removeFile}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            
            <div className="mt-6 p-4 rounded-lg bg-green-500/10 border border-green-500/30">
              <p className="text-sm text-green-600 dark:text-green-400">
                ✓ Document ready for processing
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}