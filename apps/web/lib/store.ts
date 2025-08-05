// apps/web/lib/store.ts
import { create } from 'zustand'

export type PipelineStep = 
  | 'document_upload'
  | 'dfd_extraction' 
  | 'threat_generation'
  | 'threat_refinement'
  | 'attack_path_analysis'

export type StepStatus = 'pending' | 'running' | 'completed' | 'failed'

interface StepData {
  status: StepStatus
  data: any
  error?: string
}

interface PipelineStore {
  // Current state
  currentStep: PipelineStep
  pipelineId: string | null
  uploadedFile: File | null
  
  // Step statuses
  steps: Record<PipelineStep, StepData>
  
  // Actions
  setCurrentStep: (step: PipelineStep) => void
  setPipelineId: (id: string) => void
  setUploadedFile: (file: File | null) => void
  setStepStatus: (step: PipelineStep, status: StepStatus) => void
  setStepData: (step: PipelineStep, data: any) => void
  setStepError: (step: PipelineStep, error: string) => void
  resetPipeline: () => void
}

const initialStepData: StepData = {
  status: 'pending',
  data: null
}

export const usePipelineStore = create<PipelineStore>((set) => ({
  // Initial state
  currentStep: 'document_upload',
  pipelineId: null,
  uploadedFile: null,
  
  steps: {
    document_upload: { ...initialStepData },
    dfd_extraction: { ...initialStepData },
    threat_generation: { ...initialStepData },
    threat_refinement: { ...initialStepData },
    attack_path_analysis: { ...initialStepData },
  },
  
  // Actions
  setCurrentStep: (step) => set({ currentStep: step }),
  
  setPipelineId: (id) => set({ pipelineId: id }),
  
  setUploadedFile: (file) => set({ uploadedFile: file }),
  
  setStepStatus: (step, status) =>
    set((state) => ({
      steps: {
        ...state.steps,
        [step]: {
          ...state.steps[step],
          status,
        },
      },
    })),
  
  setStepData: (step, data) =>
    set((state) => ({
      steps: {
        ...state.steps,
        [step]: {
          ...state.steps[step],
          data,
        },
      },
    })),
  
  setStepError: (step, error) =>
    set((state) => ({
      steps: {
        ...state.steps,
        [step]: {
          ...state.steps[step],
          error,
          status: 'failed',
        },
      },
    })),
  
  resetPipeline: () =>
    set({
      currentStep: 'document_upload',
      pipelineId: null,
      uploadedFile: null,
      steps: {
        document_upload: { ...initialStepData },
        dfd_extraction: { ...initialStepData },
        threat_generation: { ...initialStepData },
        threat_refinement: { ...initialStepData },
        attack_path_analysis: { ...initialStepData },
      },
    }),
}))