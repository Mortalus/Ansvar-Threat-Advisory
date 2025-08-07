'use client'

import { useState, useCallback, useEffect } from 'react'
import { useStore } from '@/lib/store'
import { api, Threat, RefinedThreat, ThreatRefinementResponse } from '@/lib/api'
import { Upload, FileText, X, AlertCircle, CheckCircle, Play, ArrowRight, Eye, Shield, Target, Brain, Star } from 'lucide-react'
import { EnhancedDFDReview } from '@/components/pipeline/steps/enhanced-dfd-review'
import { DebugPanel } from '@/components/debug/debug-panel'

export default function HomePage() {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [threats, setThreats] = useState<Threat[]>([])
  const [threatGenerationError, setThreatGenerationError] = useState<string | null>(null)
  const [refinedThreats, setRefinedThreats] = useState<RefinedThreat[]>([])
  const [threatRefinementError, setThreatRefinementError] = useState<string | null>(null)
  
  const {
    currentStep,
    setCurrentStep,
    uploadedFiles,
    setUploadedFiles,
    setDocumentText,
    tokenEstimate,
    setTokenEstimate,
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

    // Reset all state when new files are uploaded
    setUploadError(null)
    setLoading(true)
    
    // Clear previous pipeline data completely
    setDfdComponents(null)
    setDfdValidation(null)
    setPipelineId('')
    
    // Clear any persisted stale data
    const { resetPipeline } = useStore.getState()
    resetPipeline()
    
    // Reset all step statuses
    setStepStatus('document_upload', 'in_progress')
    setStepStatus('dfd_extraction', 'pending')
    setStepStatus('dfd_review', 'pending')
    setStepStatus('threat_generation', 'pending')
    setStepStatus('threat_refinement', 'pending')
    setStepStatus('attack_path_analysis', 'pending')

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

      // Store token estimate if available
      if (response.token_estimate) {
        setTokenEstimate(response.token_estimate)
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
    setTokenEstimate(null)
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

  const handleGenerateThreats = async () => {
    if (!useStore.getState().currentPipelineId) {
      console.error('No pipeline ID available')
      return
    }

    setLoading(true)
    setStepStatus('threat_generation', 'in_progress')
    setThreatGenerationError(null)

    try {
      const result = await api.generateThreats(useStore.getState().currentPipelineId!)
      
      // Update state with generated threats
      setThreats(result.threats)
      setStepStatus('threat_generation', 'complete')
      setStepResult('threat_generation', result)
      
    } catch (error) {
      console.error('Threat generation failed:', error)
      const errorMessage = error instanceof Error ? error.message : 'Threat generation failed'
      setThreatGenerationError(errorMessage)
      setStepStatus('threat_generation', 'error', errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleRefineThreats = async () => {
    if (!useStore.getState().currentPipelineId) {
      console.error('No pipeline ID available')
      return
    }

    setLoading(true)
    setStepStatus('threat_refinement', 'in_progress')
    setThreatRefinementError(null)

    try {
      const result = await api.refineThreats(useStore.getState().currentPipelineId!)
      
      // Update state with refined threats
      setRefinedThreats(result.refined_threats)
      setStepStatus('threat_refinement', 'complete')
      setStepResult('threat_refinement', result)
      
    } catch (error) {
      console.error('Threat refinement failed:', error)
      const errorMessage = error instanceof Error ? error.message : 'Threat refinement failed'
      setThreatRefinementError(errorMessage)
      setStepStatus('threat_refinement', 'error', errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleQuickRefineThreats = async () => {
    setLoading(true)
    setStepStatus('threat_refinement', 'in_progress')
    setThreatRefinementError(null)

    try {
      const result = await api.quickRefineThreats()
      
      // Update state with refined threats
      setRefinedThreats(result.refined_threats)
      setStepStatus('threat_refinement', 'complete')
      setStepResult('threat_refinement', result)
      
    } catch (error) {
      console.error('Quick threat refinement failed:', error)
      const errorMessage = error instanceof Error ? error.message : 'Quick threat refinement failed'
      setThreatRefinementError(errorMessage)
      setStepStatus('threat_refinement', 'error', errorMessage)
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
                        <div className="flex items-center gap-3 text-sm text-gray-400">
                          <span>{(file.size / 1024).toFixed(2)} KB</span>
                          {tokenEstimate && (
                            <span className="text-purple-400">
                              {tokenEstimate.discrete_summary}
                            </span>
                          )}
                        </div>
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
                  <div className="flex flex-col">
                    <p className="text-green-400">DFD extraction completed successfully!</p>
                    {stepStates.dfd_extraction.result?.quality_report?.token_usage && (
                      <p className="text-xs text-gray-500 mt-1">
                        🪙 {stepStates.dfd_extraction.result.quality_report.token_usage.total_tokens.toLocaleString()} tokens • ${stepStates.dfd_extraction.result.quality_report.token_usage.total_cost_usd.toFixed(4)}
                      </p>
                    )}
                  </div>
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

            {stepStates.dfd_extraction.status === 'complete' && dfdComponents && dfdComponents.external_entities && (
              <div className="flex-1 overflow-auto">
                <div className="space-y-6">
                  {/* Summary Card */}
                  <div className="card-bg rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold">Extraction Summary</h3>
                      {stepStates.dfd_extraction.result?.quality_report?.token_usage && (
                        <div className="text-xs text-gray-500 bg-gray-800/50 px-3 py-1 rounded-full">
                          🪙 {stepStates.dfd_extraction.result.quality_report.token_usage.total_tokens.toLocaleString()} tokens • ${stepStates.dfd_extraction.result.quality_report.token_usage.total_cost_usd.toFixed(4)}
                        </div>
                      )}
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-400">{dfdComponents.external_entities?.length || 0}</div>
                        <div className="text-sm text-gray-400">External Entities</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-400">{dfdComponents.processes?.length || 0}</div>
                        <div className="text-sm text-gray-400">Processes</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-400">{dfdComponents.assets?.length || 0}</div>
                        <div className="text-sm text-gray-400">Assets</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-yellow-400">{dfdComponents.data_flows?.length || 0}</div>
                        <div className="text-sm text-gray-400">Data Flows</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between p-4 bg-green-500/10 border border-green-500/30 rounded-xl">
                      <div>
                        <p className="text-green-400 font-medium">DFD Extraction Complete</p>
                        <p className="text-gray-400 text-sm">Review and edit the extracted components</p>
                      </div>
                      <button
                        onClick={() => setCurrentStep('dfd_review')}
                        className="px-4 py-2 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2"
                      >
                        <ArrowRight className="w-4 h-4" />
                        Continue to Review
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )

      case 'dfd_review':
        return <EnhancedDFDReview />

      case 'threat_generation':
        return (
          <div className="h-full flex flex-col">
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2">Threat Generation</h2>
              <p className="text-gray-400">
                Identifying potential security threats using RAG-powered AI analysis
              </p>
            </div>

            {/* Check prerequisites */}
            {stepStates.dfd_review.status !== 'complete' && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center p-8 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
                  <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
                  <p className="text-lg font-semibold mb-2">DFD Review Required</p>
                  <p className="text-gray-400 mb-4">
                    Please complete and review your DFD components before generating threats.
                  </p>
                  <button
                    onClick={() => setCurrentStep('dfd_review')}
                    className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all"
                  >
                    Go to DFD Review
                  </button>
                </div>
              </div>
            )}

            {/* Ready to start */}
            {stepStates.dfd_review.status === 'complete' && stepStates.threat_generation.status === 'pending' && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center p-8 bg-blue-500/10 border border-blue-500/30 rounded-xl max-w-md">
                  <div className="w-16 h-16 rounded-full gradient-purple-blue flex items-center justify-center mx-auto mb-4">
                    <Shield className="w-8 h-8 text-white" />
                  </div>
                  <p className="text-lg font-semibold mb-2">Ready for Threat Analysis</p>
                  <p className="text-gray-400 mb-6">
                    AI will analyze your DFD components using real threat intelligence to identify potential security risks.
                  </p>
                  <button
                    onClick={handleGenerateThreats}
                    disabled={isLoading}
                    className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2 mx-auto disabled:opacity-50"
                  >
                    <Target className="w-4 h-4" />
                    {isLoading ? 'Generating Threats...' : 'Generate Threats'}
                  </button>
                </div>
              </div>
            )}

            {/* In progress */}
            {stepStates.threat_generation.status === 'in_progress' && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-lg">Analyzing threats with AI...</p>
                  <p className="text-gray-400 mt-2">This may take a few moments</p>
                </div>
              </div>
            )}

            {/* Error state */}
            {threatGenerationError && (
              <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <p className="text-red-400">{threatGenerationError}</p>
                <button
                  onClick={handleGenerateThreats}
                  className="ml-auto px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all"
                >
                  Retry
                </button>
              </div>
            )}

            {/* Success - show threats */}
            {stepStates.threat_generation.status === 'complete' && threats.length > 0 && (
              <div className="flex-1 overflow-auto">
                <div className="mb-6 p-4 rounded-xl bg-green-500/10 border border-green-500/30 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    <p className="text-green-400">Found {threats.length} potential threats!</p>
                  </div>
                  <button
                    onClick={() => setCurrentStep('threat_refinement')}
                    className="px-4 py-2 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2"
                  >
                    <ArrowRight className="w-4 h-4" />
                    Refine Threats
                  </button>
                </div>

                {/* Threat Summary Cards */}
                <div className="grid gap-4">
                  {threats.map((threat, index) => {
                    const getCategoryColor = (category: string) => {
                      const colors: Record<string, string> = {
                        'Spoofing': 'border-red-500/30 bg-red-500/10 text-red-400',
                        'Tampering': 'border-orange-500/30 bg-orange-500/10 text-orange-400',
                        'Repudiation': 'border-yellow-500/30 bg-yellow-500/10 text-yellow-400',
                        'Information Disclosure': 'border-purple-500/30 bg-purple-500/10 text-purple-400',
                        'Denial of Service': 'border-blue-500/30 bg-blue-500/10 text-blue-400',
                        'Elevation of Privilege': 'border-green-500/30 bg-green-500/10 text-green-400',
                      }
                      return colors[category] || 'border-gray-500/30 bg-gray-500/10 text-gray-400'
                    }

                    const getImpactColor = (impact: string) => {
                      return impact === 'High' ? 'text-red-400' : 
                             impact === 'Medium' ? 'text-yellow-400' : 'text-green-400'
                    }

                    return (
                      <div key={index} className="card-bg rounded-xl p-6 border border-[#2a2a4a]">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getCategoryColor(threat['Threat Category'])}`}>
                                {threat['Threat Category']}
                              </span>
                              <span className={`text-sm font-medium ${getImpactColor(threat['Potential Impact'])}`}>
                                {threat['Potential Impact']} Impact
                              </span>
                            </div>
                            <h3 className="text-lg font-semibold text-white mb-1">{threat['Threat Name']}</h3>
                            <p className="text-sm text-gray-400">Component: {threat.component_name}</p>
                          </div>
                        </div>
                        
                        <div className="space-y-3">
                          <div>
                            <p className="text-sm font-medium text-gray-300 mb-1">Description:</p>
                            <p className="text-gray-400">{threat['Description']}</p>
                          </div>
                          
                          <div className="flex items-center gap-6 text-sm">
                            <div>
                              <span className="text-gray-300">Likelihood: </span>
                              <span className={getImpactColor(threat['Likelihood'])}>{threat['Likelihood']}</span>
                            </div>
                          </div>
                          
                          <div>
                            <p className="text-sm font-medium text-gray-300 mb-1">Suggested Mitigation:</p>
                            <p className="text-gray-400">{threat['Suggested Mitigation']}</p>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )

      case 'threat_refinement':
        return (
          <div className="h-full flex flex-col">
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2">AI-Powered Threat Refinement</h2>
              <p className="text-gray-400">
                Enhance threats with contextual risk analysis, business impact assessment, and intelligent prioritization
              </p>
            </div>

            {/* Check prerequisites */}
            {stepStates.threat_generation.status !== 'complete' && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center p-8 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
                  <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
                  <p className="text-lg font-semibold mb-2">Threat Generation Required</p>
                  <p className="text-gray-400 mb-4">
                    Please complete threat generation before refining threats.
                  </p>
                  <button
                    onClick={() => setCurrentStep('threat_generation')}
                    className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all"
                  >
                    Go to Threat Generation
                  </button>
                </div>
              </div>
            )}

            {/* Ready to start */}
            {stepStates.threat_generation.status === 'complete' && stepStates.threat_refinement.status === 'pending' && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center p-8 bg-blue-500/10 border border-blue-500/30 rounded-xl max-w-lg">
                  <div className="w-16 h-16 rounded-full gradient-purple-blue flex items-center justify-center mx-auto mb-4">
                    <Brain className="w-8 h-8 text-white" />
                  </div>
                  <p className="text-lg font-semibold mb-2">Ready for AI Enhancement</p>
                  <p className="text-gray-400 mb-6">
                    Our AI will analyze your {threats.length} threats to provide:
                    <br />• Contextual risk scoring
                    <br />• Business impact analysis  
                    <br />• Enhanced mitigation strategies
                    <br />• Intelligent prioritization
                  </p>
                  <div className="flex flex-col gap-3">
                    <button
                      onClick={handleRefineThreats}
                      disabled={isLoading}
                      className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2 mx-auto disabled:opacity-50"
                    >
                      <Brain className="w-4 h-4" />
                      {isLoading ? 'Refining Threats...' : 'Refine with AI'}
                    </button>
                    
                    {process.env.NODE_ENV === 'development' && (
                      <button
                        onClick={handleQuickRefineThreats}
                        disabled={isLoading}
                        className="px-4 py-2 bg-yellow-600/80 hover:bg-yellow-600 text-yellow-100 rounded-lg transition-all flex items-center gap-2 mx-auto text-sm disabled:opacity-50"
                        title="Debug mode: instant refinement with sample data"
                      >
                        ⚡ Quick Test (Debug)
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* In progress */}
            {stepStates.threat_refinement.status === 'in_progress' && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-lg">AI is analyzing threats...</p>
                  <p className="text-gray-400 mt-2">Applying contextual risk assessment and business impact analysis</p>
                </div>
              </div>
            )}

            {/* Error state */}
            {threatRefinementError && (
              <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <p className="text-red-400">{threatRefinementError}</p>
                <button
                  onClick={handleRefineThreats}
                  className="ml-auto px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all"
                >
                  Retry
                </button>
              </div>
            )}

            {/* Success - show refined threats */}
            {stepStates.threat_refinement.status === 'complete' && refinedThreats.length > 0 && (
              <div className="flex-1 overflow-auto">
                <div className="mb-6 p-4 rounded-xl bg-green-500/10 border border-green-500/30 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    <p className="text-green-400">Successfully refined {refinedThreats.length} threats with AI!</p>
                  </div>
                  <button
                    onClick={() => setCurrentStep('attack_path_analysis')}
                    className="px-4 py-2 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2"
                  >
                    <ArrowRight className="w-4 h-4" />
                    Attack Analysis
                  </button>
                </div>

                {/* Refined Threat Cards */}
                <div className="grid gap-4">
                  {refinedThreats.map((threat, index) => {
                    const getRiskColor = (risk: string) => {
                      const colors: Record<string, string> = {
                        'Critical': 'border-red-600/50 bg-red-600/10 text-red-400',
                        'High': 'border-orange-500/50 bg-orange-500/10 text-orange-400',
                        'Medium': 'border-yellow-500/50 bg-yellow-500/10 text-yellow-400',
                        'Low': 'border-green-500/50 bg-green-500/10 text-green-400',
                      }
                      return colors[risk] || 'border-gray-500/50 bg-gray-500/10 text-gray-400'
                    }

                    const getPriorityIcon = (priority: string) => {
                      if (priority === 'Immediate') return '🚨'
                      if (priority === 'High') return '⚡'
                      if (priority === 'Medium') return '📋'
                      return '📌'
                    }

                    return (
                      <div key={index} className="card-bg rounded-xl p-6 border border-[#2a2a4a] hover:border-purple-500/30 transition-all">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getRiskColor(threat.risk_score || threat['Potential Impact'])}`}>
                                {threat.risk_score || threat['Potential Impact']} Risk
                              </span>
                              {threat.priority_rank && (
                                <span className="flex items-center gap-1 text-sm font-medium text-purple-400">
                                  <Star className="w-3 h-3" />
                                  #{threat.priority_rank}
                                </span>
                              )}
                              <span className="text-xs bg-purple-600/20 text-purple-300 px-2 py-1 rounded-full">
                                {getPriorityIcon(threat.implementation_priority || 'Medium')} {threat.implementation_priority || 'Medium'} Priority
                              </span>
                            </div>
                            <h3 className="text-lg font-semibold text-white mb-1">{threat['Threat Name']}</h3>
                            <p className="text-sm text-gray-400">Component: {threat.component_name}</p>
                          </div>
                        </div>
                        
                        <div className="space-y-4">
                          <div>
                            <p className="text-sm font-medium text-gray-300 mb-1">Description:</p>
                            <p className="text-gray-400">{threat['Description']}</p>
                          </div>

                          {/* AI-Enhanced Business Risk */}
                          {threat.business_risk_statement && (
                            <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                              <p className="text-sm font-medium text-blue-300 mb-1">🎯 Business Impact:</p>
                              <p className="text-blue-100 text-sm">{threat.business_risk_statement}</p>
                            </div>
                          )}

                          {/* Enhanced Mitigation */}
                          {threat.primary_mitigation ? (
                            <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
                              <p className="text-sm font-medium text-green-300 mb-1">🛡️ Enhanced Mitigation:</p>
                              <p className="text-green-100 text-sm">{threat.primary_mitigation}</p>
                            </div>
                          ) : (
                            <div>
                              <p className="text-sm font-medium text-gray-300 mb-1">Suggested Mitigation:</p>
                              <p className="text-gray-400">{threat['Suggested Mitigation']}</p>
                            </div>
                          )}

                          {/* Risk Assessment Details */}
                          <div className="flex flex-wrap items-center gap-4 text-sm">
                            {threat.exploitability && (
                              <div className="flex items-center gap-1">
                                <span className="text-gray-300">Exploitability:</span>
                                <span className={threat.exploitability === 'High' ? 'text-red-400' : 
                                              threat.exploitability === 'Medium' ? 'text-yellow-400' : 'text-green-400'}>
                                  {threat.exploitability}
                                </span>
                              </div>
                            )}
                            {threat.estimated_effort && (
                              <div className="flex items-center gap-1">
                                <span className="text-gray-300">Effort:</span>
                                <span className="text-purple-400">{threat.estimated_effort}</span>
                              </div>
                            )}
                            <div className="flex items-center gap-1">
                              <span className="text-gray-300">Likelihood:</span>
                              <span className={threat['Likelihood'] === 'High' ? 'text-red-400' : 
                                            threat['Likelihood'] === 'Medium' ? 'text-yellow-400' : 'text-green-400'}>
                                {threat['Likelihood']}
                              </span>
                            </div>
                          </div>

                          {/* AI Assessment Reasoning */}
                          {threat.assessment_reasoning && (
                            <div className="text-xs text-gray-500 mt-2 p-2 bg-gray-800/30 rounded border-l-2 border-purple-500/50">
                              <span className="font-medium text-purple-300">AI Analysis:</span> {threat.assessment_reasoning}
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
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
      
      {/* Debug Panel - only in development */}
      {process.env.NODE_ENV === 'development' && (
        <DebugPanel 
          setThreats={setThreats}
          setRefinedThreats={setRefinedThreats}
        />
      )}
    </div>
  )
}