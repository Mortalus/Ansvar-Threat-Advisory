cd /Users/jeffreyvonrotz/SynologyDrive/Projects/ThreatModelingPipeline/apps/web

# Check if directories exist
ls -la components/
ls -la lib/

# If not, create them
mkdir -p components/pipeline
mkdir -p components/ui
mkdir -p lib
mkdir -p hooks

# Let's create a script to create all files at once
cat > create-files.sh << 'SCRIPT'
#!/bin/bash

# Create directories
mkdir -p components/pipeline
mkdir -p components/ui
mkdir -p lib
mkdir -p hooks

# Create lib/store.ts
cat > lib/store.ts << 'EOF'
import { create } from 'zustand'

export type PipelineStep = 
  | 'document_upload'
  | 'dfd_extraction' 
  | 'threat_generation'
  | 'threat_refinement'
  | 'attack_path_analysis'

export type StepStatus = 'pending' | 'running' | 'completed' | 'failed'
export type PipelineStatus = 'idle' | 'running' | 'completed' | 'failed' | 'paused'

interface StepData {
  status: StepStatus
  data: any
}

interface PipelineStore {
  pipelineId: string | null
  currentStep: PipelineStep
  status: PipelineStatus
  steps: Record<PipelineStep, StepData>
  uploadedFile: File | null
  
  setPipelineId: (id: string) => void
  setCurrentStep: (step: PipelineStep) => void
  setStatus: (status: PipelineStatus) => void
  setStepStatus: (step: PipelineStep, status: StepStatus) => void
  setStepData: (step: PipelineStep, data: any) => void
  setUploadedFile: (file: File | null) => void
  reset: () => void
}

const initialSteps: Record<PipelineStep, StepData> = {
  document_upload: { status: 'pending', data: null },
  dfd_extraction: { status: 'pending', data: null },
  threat_generation: { status: 'pending', data: null },
  threat_refinement: { status: 'pending', data: null },
  attack_path_analysis: { status: 'pending', data: null },
}

export const usePipelineStore = create<PipelineStore>((set) => ({
  pipelineId: null,
  currentStep: 'document_upload',
  status: 'idle',
  steps: initialSteps,
  uploadedFile: null,
  
  setPipelineId: (id) => set({ pipelineId: id }),
  setCurrentStep: (step) => set({ currentStep: step }),
  setStatus: (status) => set({ status }),
  setStepStatus: (step, status) =>
    set((state) => ({
      steps: {
        ...state.steps,
        [step]: { ...state.steps[step], status },
      },
    })),
  setStepData: (step, data) =>
    set((state) => ({
      steps: {
        ...state.steps,
        [step]: { ...state.steps[step], data },
      },
    })),
  setUploadedFile: (file) => set({ uploadedFile: file }),
  reset: () =>
    set({
      pipelineId: null,
      currentStep: 'document_upload',
      status: 'idle',
      steps: initialSteps,
      uploadedFile: null,
    }),
}))
EOF

echo "Created lib/store.ts"
SCRIPT

# Make the script executable and run it
chmod +x create-files.sh
./create-files.sh

# Now verify the files were created
ls -la lib/
ls -la components/