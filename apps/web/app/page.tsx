'use client'

import { useState, useCallback, useEffect } from 'react'
import { useStore } from '@/lib/store'
import { api } from '@/lib/api'
import { Upload, FileText, X, AlertCircle, CheckCircle, Play, ArrowRight } from 'lucide-react'
import { DFDReviewStep } from '@/components/pipeline/steps/dfd-review'

export default function HomePage() {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  
  const {
    currentStep,
    setCurrentStep,
    uploadedFiles,
    setUploadedFiles,
    setDocumentText,
    dfdComponents,
    setDfdComponents,
    setDfdValidation,
    setPipelineId,
    setStepStatus,
    setStepResult,
    isLoading,
    setLoading,
    stepStates,
    updateFromPipelineStatus,
  } = useStore()

  // WebSocket connection for real-time updates
  useEffect(() => {
    const pipelineId = useStore.getState().currentPipelineId
    if (!pipelineId) return

    const ws = api.connectWebSocket(pipelineId, {
      onMessage: (data) => {
        console.log('Pipeline update:', data)
        if (data.status) {
          updateFromPipelineStatus(data)
        }
      },
      onError: (error) => {
        console.error('WebSocket error:', error)
      },
    })

    return () => {
      ws.close()
    }
  }, [useStore.getState().currentPipelineId])

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
    await handleFiles(files)
  }, [])

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files ? Array.from(e.target.files) : []
    await handleFiles(files)
  }, [])

  const handleFiles = async (files: File[]) => {
    if (files.length === 0) return

    setUploadError(null)
    setLoading(true)
    setStepStatus('document_upload', 'in_progress')

    try {
      // Validate files
      const validFiles = files.filter(file => {
        const validTypes = ['application/pdf', 'text/plain', 'text/markdown']
        const maxSize = 10 * 1024 * 1024 // 10MB
        
        if (!validTypes.includes(file.type) && !file.name.endsWith('.txt')) {
          setUploadError(`Invalid file type: ${file.name}`)
          return false
        }
        
        if (file.size > maxSize) {
          setUploadError(`File too large: ${file.name} (max 10MB)`)
          return false
        }
        
        return true
      })

      if (validFiles.length === 0) {
        setStepStatus('document_upload', 'error', uploadError || 'No valid files')
        return
      }

      // Store files in state
      setUploadedFiles(validFiles)

      // Upload to backend
      console.log('Uploading files:', validFiles.map(f => f.name))
      const response = await api.uploadDocuments(validFiles)
      
      console.log('Upload response:', response)

      // Update state based on response
      if (response.pipeline_id) {
        setPipelineId(response.pipeline_id)
      }

      if (response.text_length) {
        setDocumentText(`Extracted ${response.text_length} characters`)
      }

      // Mark upload as complete
      setStepStatus('document_upload', 'complete')
      setStepResult('document_upload', { files: response.files })

      // Stay on document upload step to show completion

    } catch (error) {
      console.error('Upload failed:', error)
      const errorMessage = error instanceof Error ? error.message : 'Upload failed'
      setUploadError(errorMessage)
      setStepStatus('document_upload', 'error', errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const removeFile = useCallback(() => {
    setUploadedFiles([])
    setDocumentText('')
    setDfdComponents(null)
    setStepStatus('document_upload', 'pending')
    setUploadError(null)
  }, [])

  const handleExtractDFD = async () => {
    if (!useStore.getState().currentPipelineId) {
      console.error('No pipeline ID available')
      return
    }

    setLoading(true)
    setStepStatus('dfd_extraction', 'in_progress')

    try {
      const result = await api.extractDFDComponents(useStore.getState().currentPipelineId!)
      
      // Update state with extracted DFD
      setDfdComponents(result.dfd_components)
      setDfdValidation(result.validation)
      setStepStatus('dfd_extraction', 'complete')
      setStepResult('dfd_extraction', result)
      
    } catch (error) {
      console.error('DFD extraction failed:', error)
      const errorMessage = error instanceof Error ? error.message : 'DFD extraction failed'
      setStepStatus('dfd_extraction', 'error', errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 'document_upload':
        return (
          <div className="h-full flex flex-col">
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2">Upload Documents</h2>
              <p className="text-gray-400">
                Upload your system architecture documents to begin threat modeling
              </p>
            </div>

            {uploadedFiles.length === 0 ? (
              <div
                className={`
                  flex-1 border-2 border-dashed rounded-xl
                  flex flex-col items-center justify-center transition-all
                  ${isDragging ? 'border-purple-500 bg-purple-500/10' : 'border-[#2a2a4a] hover:border-purple-500/50'}
                  ${isLoading ? 'opacity-50 pointer-events-none' : ''}
                `}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  accept=".pdf,.txt,.md"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                  disabled={isLoading}
                />
                
                <div className="w-24 h-24 rounded-2xl gradient-purple-blue flex items-center justify-center mb-6 shadow-lg">
                  <Upload className="w-12 h-12 text-white" />
                </div>
                
                <h3 className="text-xl font-semibold mb-2">
                  {isLoading ? 'Processing...' : 'Drop files here or click to upload'}
                </h3>
                <p className="text-gray-400 mb-6">
                  Supports PDF and TXT files up to 10MB each
                </p>
                
                <label htmlFor="file-upload">
                  <span className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all cursor-pointer inline-block">
                    Choose Files
                  </span>
                </label>
              </div>
            ) : (
              <div className="flex-1 flex flex-col">
                <div className="space-y-3 mb-6">
                  {uploadedFiles.map((file, index) => (
                    <div key={index} className="p-4 rounded-xl bg-[#252541] flex items-center gap-4">
                      <div className="w-12 h-12 rounded-lg gradient-purple-blue flex items-center justify-center">
                        <FileText className="w-6 h-6 text-white" />
                      </div>
                      
                      <div className="flex-1">
                        <p className="font-medium">{file.name}</p>
                        <p className="text-sm text-gray-400">
                          {(file.size / 1024).toFixed(2)} KB
                        </p>
                      </div>
                      
                      {!isLoading && (
                        <button
                          onClick={removeFile}
                          className="p-2 hover:bg-red-500/20 rounded-lg transition-colors"
                        >
                          <X className="w-5 h-5 text-red-400" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                {stepStates.document_upload.status === 'complete' && (
                  <div className="space-y-4">
                    <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/30 flex items-center gap-3">
                      <CheckCircle className="w-5 h-5 text-green-500" />
                      <p className="text-green-400">Documents uploaded successfully!</p>
                    </div>
                    
                    <div className="flex items-center justify-between p-4 rounded-xl bg-purple-500/10 border border-purple-500/30">
                      <div>
                        <p className="text-white font-medium">Ready for DFD Extraction</p>
                        <p className="text-gray-400 text-sm">Extract system components from your documents</p>
                      </div>
                      <button
                        onClick={() => setCurrentStep('dfd_extraction')}
                        className="px-4 py-2 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2"
                      >
                        <ArrowRight className="w-4 h-4" />
                        Next Step
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {uploadError && (
              <div className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <p className="text-red-400">{uploadError}</p>
              </div>
            )}
          </div>
        )

      case 'dfd_extraction':
        return (
          <div className="h-full flex flex-col">
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2">DFD Extraction</h2>
              <p className="text-gray-400">
                Analyzing documents to extract system components and data flows
              </p>
            </div>

            {stepStates.document_upload.status !== 'complete' && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center p-8 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
                  <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
                  <p className="text-lg font-semibold mb-2">Documents Required</p>
                  <p className="text-gray-400 mb-4">
                    Please upload documents first before proceeding with DFD extraction.
                  </p>
                  <button
                    onClick={() => setCurrentStep('document_upload')}
                    className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all"
                  >
                    Go to Document Upload
                  </button>
                </div>
              </div>
            )}

            {stepStates.document_upload.status === 'complete' && stepStates.dfd_extraction.status === 'pending' && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center p-8 bg-blue-500/10 border border-blue-500/30 rounded-xl max-w-md">
                  <div className="w-16 h-16 rounded-full gradient-purple-blue flex items-center justify-center mx-auto mb-4">
                    <Play className="w-8 h-8 text-white" />
                  </div>
                  <p className="text-lg font-semibold mb-2">Ready to Extract DFD</p>
                  <p className="text-gray-400 mb-6">
                    Click the button below to analyze your documents and extract system components.
                  </p>
                  <button
                    onClick={handleExtractDFD}
                    disabled={isLoading}
                    className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2 mx-auto disabled:opacity-50"
                  >
                    <Play className="w-4 h-4" />
                    {isLoading ? 'Extracting...' : 'Start DFD Extraction'}
                  </button>
                </div>
              </div>
            )}

            {stepStates.document_upload.status === 'complete' && stepStates.dfd_extraction.status === 'in_progress' && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-lg">Extracting DFD components...</p>
                  <p className="text-gray-400 mt-2">This may take a few moments</p>
                </div>
              </div>
            )}

            {stepStates.dfd_extraction.status === 'complete' && (
              <div className="mb-6 p-4 rounded-xl bg-green-500/10 border border-green-500/30 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <p className="text-green-400">DFD extraction completed successfully!</p>
                </div>
                <button
                  onClick={() => setCurrentStep('dfd_review')}
                  className="px-4 py-2 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2"
                >
                  <ArrowRight className="w-4 h-4" />
                  Review DFD
                </button>
              </div>
            )}

            {dfdComponents && dfdComponents.external_entities && (
              <div className="flex-1 overflow-auto">
                <div className="space-y-6">
                  <div className="card-bg rounded-xl p-6">
                    <h3 className="text-lg font-semibold mb-3">Project Information</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Name:</span>
                        <span>{dfdComponents.project_name || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Version:</span>
                        <span>{dfdComponents.project_version || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Industry:</span>
                        <span>{dfdComponents.industry_context || 'N/A'}</span>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="card-bg rounded-xl p-6">
                      <h3 className="text-lg font-semibold mb-3">External Entities</h3>
                      <div className="space-y-2">
                        {(dfdComponents.external_entities || []).map((entity, i) => (
                          <div key={i} className="text-sm text-gray-300">{entity}</div>
                        ))}
                      </div>
                    </div>

                    <div className="card-bg rounded-xl p-6">
                      <h3 className="text-lg font-semibold mb-3">Processes</h3>
                      <div className="space-y-2">
                        {(dfdComponents.processes || []).map((process, i) => (
                          <div key={i} className="text-sm text-gray-300">{process}</div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="card-bg rounded-xl p-6">
                    <h3 className="text-lg font-semibold mb-3">Data Flows</h3>
                    <div className="space-y-3">
                      {(dfdComponents.data_flows || []).slice(0, 5).map((flow, i) => (
                        <div key={i} className="p-3 bg-[#1a1a2e] rounded-lg">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-sm font-medium">{flow.source}</span>
                            <span className="text-gray-500">→</span>
                            <span className="text-sm font-medium">{flow.destination}</span>
                          </div>
                          <div className="text-xs text-gray-400">
                            <span className="inline-block mr-3">{flow.protocol}</span>
                            <span className="inline-block px-2 py-1 bg-purple-500/20 rounded">
                              {flow.data_classification}
                            </span>
                          </div>
                        </div>
                      ))}
                      {(dfdComponents.data_flows || []).length > 5 && (
                        <p className="text-sm text-gray-400 text-center">
                          +{(dfdComponents.data_flows || []).length - 5} more flows
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )

      case 'dfd_review':
        return <DFDReviewStep />

      case 'threat_generation':
        return (
          <div className="h-full flex flex-col">
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2">Threat Generation</h2>
              <p className="text-gray-400">
                Identifying potential security threats based on your system architecture
              </p>
            </div>
            <div className="flex-1 flex items-center justify-center">
              <p className="text-gray-500">Threat generation coming soon...</p>
            </div>
          </div>
        )

      case 'threat_refinement':
        return (
          <div className="h-full flex flex-col">
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2">Threat Refinement</h2>
              <p className="text-gray-400">
                Refining and prioritizing identified threats
              </p>
            </div>
            <div className="flex-1 flex items-center justify-center">
              <p className="text-gray-500">Threat refinement coming soon...</p>
            </div>
          </div>
        )

      case 'attack_path_analysis':
        return (
          <div className="h-full flex flex-col">
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2">Attack Path Analysis</h2>
              <p className="text-gray-400">
                Analyzing potential attack paths and mitigation strategies
              </p>
            </div>
            <div className="flex-1 flex items-center justify-center">
              <p className="text-gray-500">Attack path analysis coming soon...</p>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <div className="flex h-screen">
        {/* Sidebar */}
        <div className="w-80 bg-[#151520] border-r border-[#2a2a4a] p-6">
          <h1 className="text-2xl font-bold mb-8">Threat Modeling</h1>
          
          <div className="space-y-4">
            {[
              { id: 'document_upload', name: 'Document Upload' },
              { id: 'dfd_extraction', name: 'DFD Extraction' },
              { id: 'dfd_review', name: 'DFD Review' },
              { id: 'threat_generation', name: 'Threat Generation' },
              { id: 'threat_refinement', name: 'Threat Refinement' },
              { id: 'attack_path_analysis', name: 'Attack Path Analysis' },
            ].map((step) => {
              const status = stepStates[step.id as keyof typeof stepStates].status
              const isActive = currentStep === step.id
              const isComplete = status === 'complete'
              const isError = status === 'error'
              const isInProgress = status === 'in_progress'
              
              // Check if step is accessible based on previous steps
              const steps = ['document_upload', 'dfd_extraction', 'dfd_review', 'threat_generation', 'threat_refinement', 'attack_path_analysis']
              const stepIndex = steps.indexOf(step.id)
              const canAccess = stepIndex === 0 || steps.slice(0, stepIndex).every(prevStep => 
                stepStates[prevStep as keyof typeof stepStates]?.status === 'complete'
              )
              
              return (
                <button
                  key={step.id}
                  onClick={() => canAccess ? setCurrentStep(step.id as any) : null}
                  disabled={!canAccess}
                  className={`
                    w-full text-left p-4 rounded-xl transition-all
                    ${isActive ? 'bg-gradient-to-r from-purple-600/20 to-blue-600/20 border border-purple-500/50' : 
                      canAccess ? 'hover:bg-[#252541]' : 'opacity-50 cursor-not-allowed'}
                  `}
                >
                  <div className="flex items-center gap-3">
                    <div className={`
                      w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold
                      ${isComplete ? 'bg-green-500' : 
                        isError ? 'bg-red-500' :
                        isInProgress ? 'bg-purple-500 animate-pulse' :
                        isActive ? 'gradient-purple-blue' : 
                        'bg-[#2a2a4a]'}
                    `}>
                      {isComplete ? '✓' : 
                       isError ? '!' :
                       isInProgress ? '...' :
                       ['1', '2', '3', '4', '5', '6'][['document_upload', 'dfd_extraction', 'dfd_review', 'threat_generation', 'threat_refinement', 'attack_path_analysis'].indexOf(step.id)]}
                    </div>
                    <div className="flex-1">
                      <span className={isActive ? 'font-semibold' : ''}>{step.name}</span>
                    </div>
                    {isComplete && (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-8 overflow-auto">
          {renderStepContent()}
        </div>
      </div>
    </div>
  )
}