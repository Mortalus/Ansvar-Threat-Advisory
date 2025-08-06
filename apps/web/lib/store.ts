import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import type { DFDComponents, PipelineStatus } from './api'

export type PipelineStep = 
  | 'document_upload'
  | 'dfd_extraction' 
  | 'threat_generation'
  | 'threat_refinement'
  | 'attack_path_analysis'

export type StepStatus = 'pending' | 'in_progress' | 'complete' | 'error'

export interface PipelineStepState {
  status: StepStatus
  error?: string
  result?: any
  startedAt?: string
  completedAt?: string
}

interface StoreState {
  // Pipeline state
  currentPipelineId: string | null
  currentStep: PipelineStep
  stepStates: Record<PipelineStep, PipelineStepState>
  
  // Document state
  uploadedFiles: File[]
  documentText: string
  
  // DFD state
  dfdComponents: DFDComponents | null
  dfdValidation: {
    is_valid: boolean
    warnings: string[]
    quality_score: number
  } | null
  
  // Threats state
  threats: any[]
  refinedThreats: any[]
  attackPaths: any[]
  
  // UI state
  isLoading: boolean
  error: string | null
  sidebarOpen: boolean
  
  // Actions
  setPipelineId: (id: string) => void
  setCurrentStep: (step: PipelineStep) => void
  setStepStatus: (step: PipelineStep, status: StepStatus, error?: string) => void
  setStepResult: (step: PipelineStep, result: any) => void
  
  setUploadedFiles: (files: File[]) => void
  setDocumentText: (text: string) => void
  
  setDfdComponents: (components: DFDComponents | null) => void
  setDfdValidation: (validation: any) => void
  
  setThreats: (threats: any[]) => void
  setRefinedThreats: (threats: any[]) => void
  setAttackPaths: (paths: any[]) => void
  
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  toggleSidebar: () => void
  
  // Complex actions
  updateFromPipelineStatus: (status: PipelineStatus) => void
  resetPipeline: () => void
  
  // Computed getters
  getStepStatus: (step: PipelineStep) => StepStatus
  isStepComplete: (step: PipelineStep) => boolean
  canProceedToStep: (step: PipelineStep) => boolean
}

const initialStepState: PipelineStepState = {
  status: 'pending',
  error: undefined,
  result: undefined,
  startedAt: undefined,
  completedAt: undefined,
}

const initialStepStates: Record<PipelineStep, PipelineStepState> = {
  document_upload: { ...initialStepState },
  dfd_extraction: { ...initialStepState },
  threat_generation: { ...initialStepState },
  threat_refinement: { ...initialStepState },
  attack_path_analysis: { ...initialStepState },
}

export const useStore = create<StoreState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        currentPipelineId: null,
        currentStep: 'document_upload',
        stepStates: initialStepStates,
        
        uploadedFiles: [],
        documentText: '',
        
        dfdComponents: null,
        dfdValidation: null,
        
        threats: [],
        refinedThreats: [],
        attackPaths: [],
        
        isLoading: false,
        error: null,
        sidebarOpen: true,
        
        // Actions
        setPipelineId: (id) => set({ currentPipelineId: id }),
        
        setCurrentStep: (step) => set({ currentStep: step }),
        
        setStepStatus: (step, status, error) => set((state) => ({
          stepStates: {
            ...state.stepStates,
            [step]: {
              ...state.stepStates[step],
              status,
              error,
              startedAt: status === 'in_progress' ? new Date().toISOString() : state.stepStates[step].startedAt,
              completedAt: status === 'complete' ? new Date().toISOString() : state.stepStates[step].completedAt,
            }
          }
        })),
        
        setStepResult: (step, result) => set((state) => ({
          stepStates: {
            ...state.stepStates,
            [step]: {
              ...state.stepStates[step],
              result,
            }
          }
        })),
        
        setUploadedFiles: (files) => set({ uploadedFiles: files }),
        
        setDocumentText: (text) => set({ documentText: text }),
        
        setDfdComponents: (components) => set({ dfdComponents: components }),
        
        setDfdValidation: (validation) => set({ dfdValidation: validation }),
        
        setThreats: (threats) => set({ threats }),
        
        setRefinedThreats: (threats) => set({ refinedThreats: threats }),
        
        setAttackPaths: (paths) => set({ attackPaths: paths }),
        
        setLoading: (loading) => set({ isLoading: loading }),
        
        setError: (error) => set({ error }),
        
        toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
        
        // Complex actions
        updateFromPipelineStatus: (status) => {
          const updates: Partial<StoreState> = {
            currentPipelineId: status.id,
          }
          
          // Update step states from pipeline status
          const newStepStates = { ...get().stepStates }
          
          Object.entries(status.steps).forEach(([stepKey, stepData]) => {
            const step = stepKey as PipelineStep
            if (newStepStates[step]) {
              newStepStates[step] = {
                status: stepData.status === 'completed' ? 'complete' : 
                        stepData.status === 'in_progress' ? 'in_progress' :
                        stepData.status === 'failed' ? 'error' : 'pending',
                error: stepData.error || undefined,
                result: stepData.result,
                startedAt: stepData.started_at || undefined,
                completedAt: stepData.completed_at || undefined,
              }
              
              // Update specific state based on step results
              if (step === 'dfd_extraction' && stepData.result) {
                updates.dfdComponents = stepData.result.dfd_components
                updates.dfdValidation = stepData.result.validation
              }
            }
          })
          
          updates.stepStates = newStepStates
          
          set(updates)
        },
        
        resetPipeline: () => set({
          currentPipelineId: null,
          currentStep: 'document_upload',
          stepStates: initialStepStates,
          uploadedFiles: [],
          documentText: '',
          dfdComponents: null,
          dfdValidation: null,
          threats: [],
          refinedThreats: [],
          attackPaths: [],
          isLoading: false,
          error: null,
        }),
        
        // Computed getters
        getStepStatus: (step) => get().stepStates[step]?.status || 'pending',
        
        isStepComplete: (step) => get().stepStates[step]?.status === 'complete',
        
        canProceedToStep: (step) => {
          const steps: PipelineStep[] = [
            'document_upload',
            'dfd_extraction',
            'threat_generation',
            'threat_refinement',
            'attack_path_analysis'
          ]
          
          const stepIndex = steps.indexOf(step)
          if (stepIndex <= 0) return true
          
          // Check if all previous steps are complete
          for (let i = 0; i < stepIndex; i++) {
            if (!get().isStepComplete(steps[i])) {
              return false
            }
          }
          
          return true
        },
      }),
      {
        name: 'threat-modeling-store',
        partialize: (state) => ({
          // Only persist essential data
          currentPipelineId: state.currentPipelineId,
          dfdComponents: state.dfdComponents,
          threats: state.threats,
        }),
      }
    )
  )
)