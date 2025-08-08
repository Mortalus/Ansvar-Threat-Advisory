'use client'

import { useState, useCallback, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useStore } from '@/lib/store'
import { api, Threat, RefinedThreat, ThreatRefinementResponse } from '@/lib/api'
import { pipelineIdManager } from '@/lib/pipeline-id-manager'
import { Upload, FileText, X, AlertCircle, CheckCircle, Play, ArrowRight, Eye, Shield, Target, Brain, Star, Settings, FolderOpen } from 'lucide-react'
import { EnhancedDFDReview } from '@/components/pipeline/steps/enhanced-dfd-review'
import { AgentConfigurationStep } from '@/components/pipeline/steps/agent-configuration-step'
import { ThreatGenerationStep } from '@/components/pipeline/steps/threat-generation-step'
import { DebugPanel } from '@/components/debug/debug-panel'
import { PromptManager } from '@/components/ai-customization/prompt-manager'

function HomePageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  const [isDragging, setIsDragging] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [strideError, setStrideError] = useState<string | null>(null)
  const [dfdExtractionError, setDfdExtractionError] = useState<string | null>(null)
  const [threats, setThreats] = useState<Threat[]>([])
  const [threatGenerationError, setThreatGenerationError] = useState<string | null>(null)
  const [refinedThreats, setRefinedThreats] = useState<RefinedThreat[]>([])
  const [threatRefinementError, setThreatRefinementError] = useState<string | null>(null)
  
  // Session management state
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null)
  const [sessionInfo, setSessionInfo] = useState<{
    sessionName?: string;
    projectName?: string;
    isLoaded?: boolean;
  }>({})
  
  const {
    currentStep,
    setCurrentStep,
    currentPipelineId,
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

  // Session loading from URL parameters
  useEffect(() => {
    const sessionId = searchParams.get('session')
    const projectId = searchParams.get('project')
    
    if (sessionId && projectId) {
      loadSession(sessionId, projectId)
    }
  }, [searchParams])

  // ULTIMATE Pipeline ID Guardian - Multi-layer defensive recovery system
  useEffect(() => {
    const pipelineIdGuardian = () => {
      // Always check manager first
      const managerId = pipelineIdManager.getPipelineId()
      
      console.log('🛡️ Pipeline ID Guardian Check:', {
        managerPipelineId: managerId,
        storePipelineId: useStore.getState().currentPipelineId,
        uploadStatus: stepStates.document_upload.status,
        uploadResult: stepStates.document_upload.result,
        allStepStates: stepStates
      })
      
      // Sync manager to store if needed
      if (managerId && !currentPipelineId) {
        console.log('🔧 Guardian: Syncing pipeline ID from manager to store:', managerId)
        setPipelineId(managerId)
        return // Pipeline recovered successfully
      }
      
      // Sync store to manager if needed
      if (currentPipelineId && !managerId) {
        console.log('🔧 Guardian: Syncing pipeline ID from store to manager:', currentPipelineId)
        pipelineIdManager.setPipelineId(currentPipelineId)
        return // Pipeline synced successfully
      }
      
      // LAYER 1: Check if we need recovery (document uploaded but no pipeline ID)
      if (stepStates.document_upload.status === 'complete' && !currentPipelineId) {
        console.warn('🚨 PIPELINE ID LOST - INITIATING RECOVERY PROTOCOL')
        
        // LAYER 2: Try multiple recovery sources
        let recoveredId = null
        
        // Source 1: Upload result
        if (stepStates.document_upload.result?.pipeline_id) {
          recoveredId = stepStates.document_upload.result.pipeline_id
          console.log('✅ Recovery Source 1: Found in upload result:', recoveredId)
        }
        
        // Source 2: DFD extraction result
        if (!recoveredId && stepStates.dfd_extraction.result?.pipeline_id) {
          recoveredId = stepStates.dfd_extraction.result.pipeline_id
          console.log('✅ Recovery Source 2: Found in DFD result:', recoveredId)
        }
        
        // Source 3: Data extraction result
        if (!recoveredId && stepStates.data_extraction.result?.pipeline_id) {
          recoveredId = stepStates.data_extraction.result.pipeline_id
          console.log('✅ Recovery Source 3: Found in data extraction result:', recoveredId)
        }
        
        // Source 4: Check localStorage directly
        if (!recoveredId) {
          try {
            const storedState = localStorage.getItem('threat-modeling-store')
            if (storedState) {
              const parsed = JSON.parse(storedState)
              recoveredId = parsed?.state?.currentPipelineId || parsed?.state?.backupPipelineId
              if (recoveredId) {
                console.log('✅ Recovery Source 4: Found in localStorage:', recoveredId)
              }
            }
          } catch (e) {
            console.error('Failed to check localStorage:', e)
          }
        }
        
        // Source 5: Check sessionStorage as last resort
        if (!recoveredId) {
          try {
            const sessionPipeline = sessionStorage.getItem('currentPipelineId')
            if (sessionPipeline) {
              recoveredId = sessionPipeline
              console.log('✅ Recovery Source 5: Found in sessionStorage:', recoveredId)
            }
          } catch (e) {
            console.error('Failed to check sessionStorage:', e)
          }
        }
        
        // LAYER 3: Apply recovery or reset
        if (recoveredId) {
          console.log('🎉 PIPELINE ID RECOVERED:', recoveredId)
          // Save to BOTH manager and store
          pipelineIdManager.setPipelineId(recoveredId)
          setPipelineId(recoveredId)
          // Manager already handles all storage backups
        } else {
          console.error('❌ PIPELINE ID UNRECOVERABLE - Resetting to allow re-upload')
          setStepStatus('document_upload', 'pending')
          alert('Pipeline connection lost. Please re-upload your documents.')
        }
      }
      
      // LAYER 4: Proactive backup - save pipeline ID to multiple locations
      if (currentPipelineId) {
        try {
          sessionStorage.setItem('currentPipelineId', currentPipelineId)
          // Also ensure it's in the step result
          if (stepStates.document_upload.status === 'complete' && 
              stepStates.document_upload.result && 
              !stepStates.document_upload.result.pipeline_id) {
            console.log('🔧 Adding pipeline ID to upload result for future recovery')
            setStepResult('document_upload', {
              ...stepStates.document_upload.result,
              pipeline_id: currentPipelineId
            })
          }
        } catch (e) {
          console.error('Failed to backup pipeline ID:', e)
        }
      }
    }
    
    // Run guardian check
    pipelineIdGuardian()
    
    // Also run on visibility change (tab switching)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        console.log('🔍 Tab became visible - checking pipeline ID')
        pipelineIdGuardian()
      }
    }
    
    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [currentPipelineId, stepStates.document_upload.status, stepStates.document_upload.result])

  const loadSession = async (sessionId: string, projectId: string) => {
    try {
      console.log('📂 Loading session:', sessionId, 'in project:', projectId)
      setLoading(true)
      
      // Load session details from backend API
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || ''
      const sessionResponse = await fetch(`${apiBaseUrl}/api/projects/sessions/${sessionId}`)
      if (!sessionResponse.ok) {
        throw new Error('Failed to load session')
      }
      
      const sessionData = await sessionResponse.json()
      console.log('✅ Session loaded:', sessionData)
      
      setCurrentSessionId(sessionId)
      setCurrentProjectId(projectId)
      setSessionInfo({
        sessionName: sessionData.name,
        projectName: sessionData.project_name,
        isLoaded: true
      })
      
      // If session has a pipeline, load its state
      if (sessionData.pipeline_id) {
        console.log('🔄 Loading pipeline state:', sessionData.pipeline_id)
        
        // Set the pipeline ID in the store
        setPipelineId(sessionData.pipeline_id)
        
        // Load the pipeline status from the backend
        try {
          const pipelineResponse = await fetch(`${apiBaseUrl}/api/documents/${sessionData.pipeline_id}/status`)
          if (pipelineResponse.ok) {
            const pipelineData = await pipelineResponse.json()
            console.log('✅ Pipeline status loaded:', pipelineData)
            
            // Update the UI with the pipeline state
            updateFromPipelineStatus(pipelineData)
            
            // If there's uploaded content, set it
            if (pipelineData.document_text) {
              setDocumentText(pipelineData.document_text)
            }
            
            // Show that we're resuming a session
            setUploadError(null)
            console.log('✅ Session resumed successfully')
          }
        } catch (error) {
          console.error('⚠️ Could not load pipeline state:', error)
        }
      }
      
    } catch (error) {
      console.error('❌ Failed to load session:', error)
      setUploadError(`Failed to load session: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

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
    setStepStatus('data_extraction', 'pending')
    setStepStatus('data_extraction_review', 'pending')
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
      console.log('Checking pipeline_id in response:', response.pipeline_id)
      if (response.pipeline_id) {
        console.log('Setting pipeline ID:', response.pipeline_id)
        
        // BULLETPROOF: Set in both store AND manager
        setPipelineId(response.pipeline_id)
        pipelineIdManager.setPipelineId(response.pipeline_id)
        
        // Verify it was set
        const verifyStore = useStore.getState().currentPipelineId
        const verifyManager = pipelineIdManager.getPipelineId()
        console.log('Pipeline ID verification - Store:', verifyStore, 'Manager:', verifyManager)
        
        if (!verifyStore || !verifyManager) {
          console.error('❌ CRITICAL: Pipeline ID failed to set properly!')
          // Force set again
          useStore.setState({ currentPipelineId: response.pipeline_id })
          pipelineIdManager.setPipelineId(response.pipeline_id)
        }
      } else {
        console.error('No pipeline_id in upload response!')
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
      setStepResult('document_upload', { 
        files: response.files,
        pipeline_id: response.pipeline_id,  // Store pipeline ID in step result for recovery
        text_length: response.text_length,
        token_estimate: response.token_estimate
      })

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

  const handleExtractStrideData = async () => {
    console.log('🚀 STRIDE button clicked!')
    const storeState = useStore.getState()
    const pipelineId = storeState.currentPipelineId
    console.log('STRIDE extraction - Full store state:', storeState)
    console.log('STRIDE extraction - Pipeline ID:', pipelineId)
    console.log('STRIDE extraction - Document upload status:', storeState.stepStates.document_upload.status)
    
    if (!pipelineId) {
      console.error('No pipeline ID available')
      alert('Please upload documents first before starting STRIDE extraction')
      return
    }

    setLoading(true)
    setStepStatus('data_extraction', 'in_progress')

    try {
      const result = await api.extractStrideData(pipelineId, {
        enable_quality_validation: true
      })
      
      // Update state with extracted security data
      setStepStatus('data_extraction', 'complete')
      setStepResult('data_extraction', result)
      
    } catch (error) {
      console.error('STRIDE data extraction failed:', error)
      const errorMessage = error instanceof Error ? error.message : 'STRIDE data extraction failed'
      setStepStatus('data_extraction', 'error', errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleExtractDFD = async () => {
    // BULLETPROOF: Use manager as primary source
    let currentPipelineId = pipelineIdManager.getPipelineId()
    
    // If manager has it, ensure store is synced
    if (currentPipelineId && !useStore.getState().currentPipelineId) {
      console.log('🔧 Syncing pipeline ID from manager to store:', currentPipelineId)
      setPipelineId(currentPipelineId)
    }
    
    // If manager doesn't have it, try store
    if (!currentPipelineId) {
      currentPipelineId = useStore.getState().currentPipelineId
      if (currentPipelineId) {
        console.log('🔧 Syncing pipeline ID from store to manager:', currentPipelineId)
        pipelineIdManager.setPipelineId(currentPipelineId)
      }
    }
    
    // Fallback 2: Check upload result
    if (!currentPipelineId && stepStates.document_upload.result?.pipeline_id) {
      currentPipelineId = stepStates.document_upload.result.pipeline_id
      console.log('🔧 DFD: Recovered pipeline ID from upload result:', currentPipelineId)
      setPipelineId(currentPipelineId) // Restore to store
    }
    
    // Fallback 3: Check localStorage directly
    if (!currentPipelineId) {
      try {
        const stored = localStorage.getItem('threat-modeling-store')
        if (stored) {
          const parsed = JSON.parse(stored)
          currentPipelineId = parsed?.state?.currentPipelineId || parsed?.state?.backupPipelineId
          if (currentPipelineId) {
            console.log('🔧 DFD: Recovered pipeline ID from localStorage:', currentPipelineId)
            setPipelineId(currentPipelineId) // Restore to store
          }
        }
      } catch (e) {
        console.error('Failed to check localStorage:', e)
      }
    }
    
    console.log('DFD extraction - Final Pipeline ID:', currentPipelineId)
    console.log('DFD extraction - Full store state:', useStore.getState())
    
    if (!currentPipelineId) {
      console.error('❌ No pipeline ID available for DFD extraction after all recovery attempts')
      alert('Pipeline ID is missing. Please upload documents first to create a new pipeline.')
      return
    }

    setLoading(true)
    setStepStatus('dfd_extraction', 'in_progress')
    setDfdExtractionError(null)

    try {
      console.log('Starting DFD extraction for pipeline:', currentPipelineId)
      const result = await api.extractDFDComponents(currentPipelineId)
      
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
    const storeState = useStore.getState()
    const pipelineId = storeState.currentPipelineId
    const selectedAgents = storeState.selectedAgents
    
    if (!pipelineId) {
      console.error('No pipeline ID available')
      return
    }

    setLoading(true)
    setStepStatus('threat_generation', 'in_progress')
    setThreatGenerationError(null)

    try {
      const result = await api.generateThreats(pipelineId, selectedAgents)
      
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
              <div className="flex items-center gap-3 mb-4">
                <img src="/ansvar-logo.svg" alt="Ansvar" className="w-8 h-8" />
                <div>
                  <h2 className="text-2xl font-bold">Upload Documents</h2>
                  <p className="text-sm text-purple-400">Ansvar Threat Advisory</p>
                </div>
              </div>
              <p className="text-gray-400">
                Upload your system architecture documents to begin AI-powered threat modeling
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
                      <div>
                        <p className="text-green-400">Documents uploaded successfully!</p>
                        <p className="text-xs text-gray-500">Ansvar AI is ready to analyze your architecture</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between p-4 rounded-xl bg-purple-500/10 border border-purple-500/30">
                      <div>
                        <p className="text-white font-medium">🛡️ STRIDE Security Analysis Required</p>
                        <p className="text-gray-400 text-sm">High-quality threat modeling with STRIDE methodology</p>
                      </div>
                      <button
                        onClick={() => setCurrentStep('data_extraction')}
                        className="px-4 py-2 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2"
                      >
                        <ArrowRight className="w-4 h-4" />
                        Start STRIDE Analysis
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

      case 'data_extraction':
        return (
          <div className="h-full flex flex-col">
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-2">
                <Shield className="w-8 h-8 text-purple-500" />
                <div>
                  <h2 className="text-2xl font-bold">STRIDE Data Extraction</h2>
                  <p className="text-sm text-purple-400">Security-Focused Analysis</p>
                </div>
              </div>
              <p className="text-gray-400">
                Extract security-relevant information using STRIDE methodology with two-pass AI analysis
              </p>
            </div>

            {stepStates.document_upload.status !== 'complete' && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center p-8 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
                  <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
                  <p className="text-lg font-semibold mb-2">Documents Required</p>
                  <p className="text-gray-400 mb-4">
                    Please upload documents first before STRIDE data extraction.
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

            {stepStates.document_upload.status === 'complete' && 
             stepStates.data_extraction.status !== 'complete' && 
             stepStates.data_extraction.status !== 'in_progress' && 
             stepStates.data_extraction.status !== 'error' && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center p-8 bg-blue-500/10 border border-blue-500/30 rounded-xl max-w-lg">
                  <div className="w-16 h-16 rounded-full gradient-purple-blue flex items-center justify-center mx-auto mb-4">
                    <Shield className="w-8 h-8 text-white" />
                  </div>
                  <p className="text-lg font-semibold mb-2">Ready for STRIDE Analysis</p>
                  <p className="text-gray-400 mb-6">
                    Perform comprehensive security data extraction using STRIDE methodology:
                    <br />• STRIDE Expert Analysis
                    <br />• Quality Validation Pass
                    <br />• Security-focused component identification
                    <br />• Trust boundary analysis
                  </p>
                  <button
                    type="button"
                    onClick={(e) => {
                      console.log('🖱️ Button clicked - event received!', e)
                      handleExtractStrideData()
                    }}
                    disabled={isLoading}
                    className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2 mx-auto cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{ pointerEvents: 'auto', zIndex: 10 }}
                  >
                    <Shield className="w-4 h-4" />
                    {isLoading ? 'Extracting Security Data...' : 'Start STRIDE Extraction'}
                  </button>
                </div>
              </div>
            )}

            {stepStates.data_extraction.status === 'in_progress' && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-lg">Running STRIDE analysis...</p>
                  <p className="text-gray-400 mt-2">Performing two-pass security extraction</p>
                </div>
              </div>
            )}

            {stepStates.data_extraction.status === 'error' && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center p-8 bg-red-500/10 border border-red-500/30 rounded-xl max-w-lg">
                  <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
                    <AlertCircle className="w-8 h-8 text-red-500" />
                  </div>
                  <p className="text-lg font-semibold mb-2 text-red-400">STRIDE Extraction Failed</p>
                  <p className="text-gray-400 mb-4">
                    {stepStates.data_extraction.error || 'An error occurred during STRIDE data extraction. Please try again.'}
                  </p>
                  <button
                    type="button"
                    onClick={handleExtractStrideData}
                    disabled={isLoading}
                    className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2 mx-auto cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Shield className="w-4 h-4" />
                    {isLoading ? 'Retrying...' : 'Retry STRIDE Extraction'}
                  </button>
                </div>
              </div>
            )}

            {stepStates.document_upload.status === 'complete' && 
             !stepStates.data_extraction.status && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center p-8 bg-blue-500/10 border border-blue-500/30 rounded-xl max-w-lg">
                  <div className="w-16 h-16 rounded-full gradient-purple-blue flex items-center justify-center mx-auto mb-4">
                    <Shield className="w-8 h-8 text-white" />
                  </div>
                  <p className="text-lg font-semibold mb-2">Start STRIDE Analysis</p>
                  <p className="text-gray-400 mb-6">
                    Begin security-focused data extraction using STRIDE methodology
                  </p>
                  <button
                    type="button"
                    onClick={handleExtractStrideData}
                    disabled={isLoading}
                    className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2 mx-auto cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Shield className="w-4 h-4" />
                    {isLoading ? 'Starting...' : 'Start STRIDE Extraction'}
                  </button>
                </div>
              </div>
            )}

            {stepStates.data_extraction.status === 'complete' && (
              <div className="flex-1 overflow-auto">
                <div className="mb-6 p-4 rounded-xl bg-green-500/10 border border-green-500/30 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    <div>
                      <p className="text-green-400">STRIDE data extraction completed!</p>
                      {stepStates.data_extraction.result?.quality_score && (
                        <p className="text-xs text-gray-500 mt-1">
                          Quality Score: {(stepStates.data_extraction.result.quality_score * 100).toFixed(1)}%
                        </p>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => setCurrentStep('data_extraction_review')}
                    className="px-4 py-2 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2"
                  >
                    <ArrowRight className="w-4 h-4" />
                    Review & Edit
                  </button>
                </div>

                {stepStates.data_extraction.result && (
                  <div className="space-y-6">
                    <div className="card-bg rounded-xl p-6">
                      <h3 className="text-lg font-semibold mb-4">Extraction Summary</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-purple-400">
                            {stepStates.data_extraction.result.extracted_security_data?.security_assets?.length || 0}
                          </div>
                          <div className="text-sm text-gray-400">Security Assets</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-blue-400">
                            {stepStates.data_extraction.result.extracted_security_data?.trust_zones?.length || 0}
                          </div>
                          <div className="text-sm text-gray-400">Trust Zones</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-400">
                            {stepStates.data_extraction.result.extracted_security_data?.security_data_flows?.length || 0}
                          </div>
                          <div className="text-sm text-gray-400">Data Flows</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-yellow-400">
                            {stepStates.data_extraction.result.extracted_security_data?.access_patterns?.length || 0}
                          </div>
                          <div className="text-sm text-gray-400">Access Patterns</div>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between p-4 bg-purple-500/10 border border-purple-500/30 rounded-xl">
                        <div>
                          <p className="text-purple-400 font-medium">STRIDE Analysis Complete</p>
                          <p className="text-gray-400 text-sm">Review and edit the extracted security data</p>
                        </div>
                        <button
                          onClick={() => setCurrentStep('data_extraction_review')}
                          className="px-4 py-2 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2"
                        >
                          <ArrowRight className="w-4 h-4" />
                          Continue to Review
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )

      case 'data_extraction_review':
        return (
          <div className="h-full flex flex-col">
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2">Review STRIDE Data</h2>
              <p className="text-gray-400">
                Review and edit the extracted security data before proceeding to DFD generation
              </p>
            </div>

            {stepStates.data_extraction.status !== 'complete' && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center p-8 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
                  <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
                  <p className="text-lg font-semibold mb-2">Data Extraction Required</p>
                  <p className="text-gray-400 mb-4">
                    Please complete STRIDE data extraction before reviewing.
                  </p>
                  <button
                    onClick={() => setCurrentStep('data_extraction')}
                    className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all"
                  >
                    Go to Data Extraction
                  </button>
                </div>
              </div>
            )}

            {stepStates.data_extraction.status === 'complete' && (
              <div className="flex-1 overflow-auto">
                <div className="space-y-6">
                  {stepStates.data_extraction.result && (
                    <>
                      {/* Quality Metrics */}
                      <div className="card-bg rounded-xl p-6">
                        <h3 className="text-lg font-semibold mb-4">Extraction Quality</h3>
                        <div className="grid grid-cols-2 gap-4 mb-4">
                          <div>
                            <div className="text-2xl font-bold text-green-400">
                              {stepStates.data_extraction.result.quality_score ? 
                                (stepStates.data_extraction.result.quality_score * 100).toFixed(1) + '%' : 
                                'N/A'}
                            </div>
                            <div className="text-sm text-gray-400">Quality Score</div>
                          </div>
                          <div>
                            <div className="text-2xl font-bold text-blue-400">
                              {stepStates.data_extraction.result.extraction_metadata?.passes_performed?.length || 0}
                            </div>
                            <div className="text-sm text-gray-400">Analysis Passes</div>
                          </div>
                        </div>
                      </div>

                      {/* Assets */}
                      {stepStates.data_extraction.result.extracted_security_data?.security_assets && (
                        <div className="card-bg rounded-xl p-6">
                          <h3 className="text-lg font-semibold mb-4">Security Assets ({stepStates.data_extraction.result.extracted_security_data.security_assets.length})</h3>
                          <div className="space-y-3">
                            {stepStates.data_extraction.result.extracted_security_data.security_assets.slice(0, 5).map((asset: any, index: number) => (
                              <div key={index} className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <span className="font-medium text-purple-300">{asset.name}</span>
                                    <span className="ml-2 text-sm text-gray-400">({asset.type})</span>
                                  </div>
                                  <span className={`px-2 py-1 text-xs rounded ${
                                    asset.sensitivity === 'Restricted' ? 'bg-red-500/20 text-red-300' :
                                    asset.sensitivity === 'Confidential' ? 'bg-orange-500/20 text-orange-300' :
                                    asset.sensitivity === 'Internal' ? 'bg-yellow-500/20 text-yellow-300' :
                                    'bg-green-500/20 text-green-300'
                                  }`}>
                                    {asset.sensitivity}
                                  </span>
                                </div>
                                {asset.data_types && asset.data_types.length > 0 && (
                                  <div className="mt-2 text-sm text-gray-400">
                                    Data: {asset.data_types.join(', ')}
                                  </div>
                                )}
                              </div>
                            ))}
                            {stepStates.data_extraction.result.extracted_security_data.security_assets.length > 5 && (
                              <div className="text-center text-sm text-gray-400">
                                ... and {stepStates.data_extraction.result.extracted_security_data.security_assets.length - 5} more
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Data Flows */}
                      {stepStates.data_extraction.result.extracted_security_data?.security_data_flows && (
                        <div className="card-bg rounded-xl p-6">
                          <h3 className="text-lg font-semibold mb-4">Security Data Flows ({stepStates.data_extraction.result.extracted_security_data.security_data_flows.length})</h3>
                          <div className="space-y-3">
                            {stepStates.data_extraction.result.extracted_security_data.security_data_flows.slice(0, 5).map((flow: any, index: number) => (
                              <div key={index} className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="font-medium text-blue-300">{flow.source}</span>
                                  <ArrowRight className="w-4 h-4 text-gray-400" />
                                  <span className="font-medium text-blue-300">{flow.destination}</span>
                                </div>
                                <div className="text-sm text-gray-400">
                                  {flow.data_description} • {flow.protocol}
                                </div>
                                {flow.stride_threats && flow.stride_threats.length > 0 && (
                                  <div className="mt-2 text-xs text-red-300">
                                    Threats: {flow.stride_threats.slice(0, 2).join(', ')}
                                    {flow.stride_threats.length > 2 && ` (+${flow.stride_threats.length - 2} more)`}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Trust Zones */}
                      {stepStates.data_extraction.result.extracted_security_data?.trust_zones && (
                        <div className="card-bg rounded-xl p-6">
                          <h3 className="text-lg font-semibold mb-4">Trust Zones ({stepStates.data_extraction.result.extracted_security_data.trust_zones.length})</h3>
                          <div className="space-y-3">
                            {stepStates.data_extraction.result.extracted_security_data.trust_zones.map((zone: any, index: number) => (
                              <div key={index} className="p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-lg">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="font-medium text-indigo-300">{zone.name}</span>
                                  <span className={`px-2 py-1 text-xs rounded ${
                                    zone.security_level === 'Restricted' ? 'bg-red-500/20 text-red-300' :
                                    zone.security_level === 'Internal' ? 'bg-yellow-500/20 text-yellow-300' :
                                    zone.security_level === 'DMZ' ? 'bg-orange-500/20 text-orange-300' :
                                    'bg-green-500/20 text-green-300'
                                  }`}>
                                    {zone.security_level}
                                  </span>
                                </div>
                                {zone.components && zone.components.length > 0 && (
                                  <div className="text-sm text-gray-400">
                                    Components: {zone.components.join(', ')}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}

                  <div className="flex items-center justify-between p-4 rounded-xl bg-green-500/10 border border-green-500/30">
                    <div>
                      <p className="text-green-400 font-medium">Ready for DFD Extraction</p>
                      <p className="text-gray-400 text-sm">Use the extracted security data for DFD generation</p>
                    </div>
                    <button
                      onClick={() => {
                        setStepStatus('data_extraction_review', 'complete')
                        setCurrentStep('dfd_extraction')
                      }}
                      className="px-4 py-2 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2"
                    >
                      <ArrowRight className="w-4 h-4" />
                      Continue to DFD
                    </button>
                  </div>
                </div>
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

            {(stepStates.document_upload.status !== 'complete' || 
              stepStates.data_extraction.status !== 'complete' || 
              stepStates.data_extraction_review.status !== 'complete') && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center p-8 bg-yellow-500/10 border border-yellow-500/30 rounded-xl max-w-lg">
                  <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
                  <p className="text-lg font-semibold mb-2">Prerequisites Required</p>
                  <p className="text-gray-400 mb-4">
                    Complete document upload and STRIDE security analysis before DFD extraction.
                  </p>
                  <div className="space-y-2">
                    {stepStates.document_upload.status !== 'complete' && (
                      <button
                        onClick={() => setCurrentStep('document_upload')}
                        className="w-full px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all"
                      >
                        Go to Document Upload
                      </button>
                    )}
                    {stepStates.document_upload.status === 'complete' && stepStates.data_extraction.status !== 'complete' && (
                      <button
                        onClick={() => setCurrentStep('data_extraction')}
                        className="w-full px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all"
                      >
                        Start STRIDE Analysis
                      </button>
                    )}
                    {stepStates.data_extraction.status === 'complete' && stepStates.data_extraction_review.status !== 'complete' && (
                      <button
                        onClick={() => setCurrentStep('data_extraction_review')}
                        className="w-full px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all"
                      >
                        Review STRIDE Data
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}

            {stepStates.document_upload.status === 'complete' && 
             stepStates.dfd_extraction.status === 'pending' && 
             currentPipelineId && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center p-8 bg-blue-500/10 border border-blue-500/30 rounded-xl max-w-md">
                  <div className="w-16 h-16 rounded-full gradient-purple-blue flex items-center justify-center mx-auto mb-4">
                    <Play className="w-8 h-8 text-white" />
                  </div>
                  <p className="text-lg font-semibold mb-2">Ready to Extract DFD</p>
                  
                  {/* Debug info for pipeline ID */}
                  <div className="mb-4 p-2 bg-gray-800 rounded text-xs text-left">
                    <div className="text-green-400">Pipeline ID: {currentPipelineId || 'Not set'}</div>
                    <div className="text-blue-400">Upload Status: {stepStates.document_upload.status}</div>
                    <div className="text-yellow-400">DFD Status: {stepStates.dfd_extraction.status}</div>
                  </div>
                  
                  <p className="text-gray-400 mb-4">
                    Extract system components from your documents. You can use the standard extraction or enhance it with STRIDE security analysis.
                  </p>
                  
                  <div className="space-y-3 mb-6">
                    <div className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                      <p className="text-sm text-purple-300 mb-1">💡 <strong>Recommended:</strong> Enhanced Security Analysis</p>
                      <p className="text-xs text-gray-400">
                        Use STRIDE data extraction for security-focused analysis before DFD generation
                      </p>
                      <button
                        onClick={() => setCurrentStep('data_extraction')}
                        className="mt-2 px-3 py-1 text-xs bg-purple-600/20 text-purple-300 rounded border border-purple-500/30 hover:bg-purple-600/30 transition-colors"
                      >
                        Try STRIDE Analysis
                      </button>
                    </div>
                  </div>
                  
                  <button
                    onClick={handleExtractDFD}
                    disabled={isLoading}
                    className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2 mx-auto cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Play className="w-4 h-4" />
                    {isLoading ? 'Extracting...' : 'Start Standard DFD Extraction'}
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

      case 'agent_config':
        return <AgentConfigurationStep />

      case 'threat_generation':
        return <ThreatGenerationStep />

      case 'threat_refinement':
        return (
          <div className="h-full flex flex-col">
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-2">
                <Shield className="w-8 h-8 text-purple-500" />
                <div>
                  <h2 className="text-2xl font-bold">Threat Generation</h2>
                  <p className="text-sm text-purple-400">Powered by Ansvar AI</p>
                </div>
              </div>
              <p className="text-gray-400">
                Identifying potential security threats using advanced AI analysis with CWE knowledge base
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
                    className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2 mx-auto cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
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
              <div className="flex items-center gap-3 mb-2">
                <Brain className="w-8 h-8 text-purple-500" />
                <div>
                  <h2 className="text-2xl font-bold">AI-Powered Threat Refinement</h2>
                  <p className="text-sm text-purple-400">Ansvar Intelligence Engine</p>
                </div>
              </div>
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
                      className="px-6 py-3 gradient-purple-blue text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2 mx-auto cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
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

      case 'ai_customization':
        return <PromptManager />

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* Session Header */}
      {sessionInfo.isLoaded && (
        <div className="bg-blue-900/20 border-b border-blue-500/30 px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <FolderOpen className="h-5 w-5 text-blue-400" />
              <div className="flex items-center space-x-2 text-sm">
                <span className="text-blue-300">Project:</span>
                <span className="font-medium text-white">{sessionInfo.projectName}</span>
                <span className="text-gray-400">→</span>
                <span className="text-blue-300">Session:</span>
                <span className="font-medium text-white">{sessionInfo.sessionName}</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => router.push('/projects')}
                className="text-sm bg-blue-600/20 text-blue-300 hover:bg-blue-600/30 px-3 py-1 rounded border border-blue-500/30 transition-colors"
              >
                View All Sessions
              </button>
            </div>
          </div>
        </div>
      )}
      
      <div className="flex h-screen">
        {/* Sidebar */}
        <div className="w-80 bg-[#151520] border-r border-[#2a2a4a] p-6">
          <div className="flex items-center gap-3 mb-8">
            <img src="/ansvar-logo.svg" alt="Ansvar Logo" className="w-8 h-8" />
            <div>
              <h1 className="text-xl font-bold">Ansvar</h1>
              <p className="text-sm text-gray-400">Threat Advisory</p>
            </div>
          </div>
          
          {/* Project Management */}
          <div className="mb-6">
            <button
              onClick={() => router.push('/projects')}
              className="w-full flex items-center space-x-3 p-3 rounded-lg bg-blue-600/20 text-blue-300 hover:bg-blue-600/30 border border-blue-500/30 transition-colors"
            >
              <FolderOpen className="h-5 w-5" />
              <span className="font-medium">Manage Projects</span>
            </button>
          </div>

          <div className="space-y-4">
            {[
              { id: 'document_upload', name: 'Document Upload' },
              { id: 'data_extraction', name: 'STRIDE Extraction' },
              { id: 'data_extraction_review', name: 'Data Review' },
              { id: 'dfd_extraction', name: 'DFD Extraction' },
              { id: 'dfd_review', name: 'DFD Review' },
              { id: 'agent_config', name: 'Agent Configuration' },
              { id: 'threat_generation', name: 'Threat Generation' },
              { id: 'threat_refinement', name: 'Threat Refinement' },
              { id: 'attack_path_analysis', name: 'Attack Path Analysis' },
              { id: 'ai_customization', name: 'AI Customization' },
            ].map((step) => {
              const status = stepStates[step.id as keyof typeof stepStates].status
              const isActive = currentStep === step.id
              const isComplete = status === 'complete'
              const isError = status === 'error'
              const isInProgress = status === 'in_progress'
              
              // Check if step is accessible based on previous steps
              const steps = ['document_upload', 'data_extraction', 'data_extraction_review', 'dfd_extraction', 'dfd_review', 'agent_config', 'threat_generation', 'threat_refinement', 'attack_path_analysis']
              const stepIndex = steps.indexOf(step.id)
              
              // AI Customization is always accessible (it's a settings page)
              const canAccess = step.id === 'ai_customization' || 
                                stepIndex === 0 || 
                                steps.slice(0, stepIndex).every(prevStep => 
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
                       step.id === 'ai_customization' ? <Settings className="w-4 h-4" /> :
                       ['1', '2', '3', '4', '5', '6', '7', '8', '9'][['document_upload', 'data_extraction', 'data_extraction_review', 'dfd_extraction', 'dfd_review', 'agent_config', 'threat_generation', 'threat_refinement', 'attack_path_analysis'].indexOf(step.id)]}
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

// Main component with Suspense wrapper for useSearchParams
export default function HomePage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Loading...</div>}>
      <HomePageContent />
    </Suspense>
  )
}