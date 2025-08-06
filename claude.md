Current Project State & Development Guide
Project Overview
A **Semi-Automated** Threat Modeling Pipeline application with a modern web interface for processing security documents through an AI-powered analysis pipeline with human review and quality control at each step.

⚠️ **IMPORTANT: This is NOT a fully automated pipeline**
- Each step requires human review and validation
- Users can edit, add, or remove extracted data before proceeding
- Quality control is provided by the user at each stage
- The AI assists but doesn't make final decisions
Current Architecture
Directory Structure
ThreatModelingPipeline/
├── apps/
│   ├── api/                  # FastAPI backend (Python 3.11)
│   │   ├── app/
│   │   │   ├── api/endpoints/ # API routes
│   │   │   ├── core/         # Business logic
│   │   │   │   ├── llm/      # LLM providers (Ollama, Azure, Scaleway)
│   │   │   │   └── pipeline/ # Pipeline management
│   │   │   │       └── steps/ # Individual pipeline steps
│   │   │   ├── models/       # Data models
│   │   │   ├── services/     # Service layer
│   │   │   └── config.py     # Settings management
│   │   ├── venv/             # Python virtual environment
│   │   ├── requirements.txt  # Python dependencies
│   │   └── .env              # Environment variables
│   │
│   └── web/                  # Next.js frontend
│       ├── app/              # Next.js app router
│       ├── components/       # React components
│       │   ├── pipeline/steps/ # Step-specific components
│       │   └── ui/           # Reusable UI components
│       ├── lib/              # Utilities, API client, store
│       └── hooks/            # Custom React hooks
│
├── inputs/                   # Input documents for testing
├── outputs/                  # Generated outputs
│   ├── exports/
│   ├── reports/
│   └── temp/
├── docker-compose.yml        # Docker configuration
└── package.json             # Root monorepo config
Tech Stack
Backend (FastAPI)

Python 3.11 with FastAPI
LLM Integration: Supports Ollama (local), Azure OpenAI, and Scaleway
Dependencies: Pydantic for validation, HTTPX for async requests
CORS configured for localhost:3000, 3001, 3002

Frontend (Next.js)

Next.js 14 with TypeScript
Styling: Tailwind CSS with custom dark theme
State Management: Zustand (lightweight alternative to Redux)
Icons: Lucide React
Running on port 3001 (3000 was occupied)

Infrastructure

Redis: Running in Docker for caching (optional)
Monorepo: Managed with npm workspaces

Pipeline Process Flow
1. **Document Upload** → User uploads system documentation
2. **DFD Extraction** → AI extracts components (requires manual trigger)
3. **DFD Review** → User reviews/edits extracted data with:
   - JSON view for raw data inspection
   - Mermaid diagram view for visualization
   - Full editing capabilities for all components
4. **Threat Generation** → AI generates threats (user reviews)
5. **Threat Refinement** → User refines and validates threats
6. **Attack Path Analysis** → AI analyzes attack paths (user validates)

Current Features
Working
✅ Modern dark UI with purple/blue gradients
✅ 6-step pipeline sidebar navigation (including DFD Review)
✅ File upload interface with drag-and-drop
✅ State management with Zustand including persistence
✅ API structure with all endpoints implemented
✅ Responsive layout with status panel
✅ CORS configuration with dynamic origins
✅ LLM provider factory with Scaleway, Azure, and Ollama support
✅ DFD extraction with comprehensive prompting
✅ Pipeline state management with in-memory storage
✅ WebSocket endpoint structure
✅ DFD visualization with JSON and Mermaid diagram tabs
✅ Complete DFD editing interface with add/remove capabilities
✅ Manual step progression (no automatic advancement)
Partially Working
⚠️ Threat generation logic (placeholder implementation)
⚠️ Document parsing for PDFs (basic) and DOCX (not implemented)
⚠️ Redis caching integration
Not Implemented Yet
❌ Threat refinement algorithm
❌ Attack path analysis
❌ WebSocket real-time updates (structure only)
❌ Database persistence (using in-memory storage)
❌ Authentication and user sessions
❌ Export functionality for reports
How to Add New Features
Method 1: Adding a New Pipeline Step

Update the type definitions in apps/web/lib/store.ts:

typescriptexport type PipelineStep = 
  | 'document_upload'
  | 'dfd_extraction' 
  | 'dfd_review'        // User review/edit of extracted DFD
  | 'threat_generation'
  | 'threat_refinement'
  | 'attack_path_analysis'
  | 'your_new_step'  // Add here

Add to backend pipeline manager in apps/api/app/core/pipeline/manager.py:

pythonclass PipelineStep(str, Enum):
    # ... existing steps
    YOUR_NEW_STEP = "your_new_step"

# Add handler in execute_step method
elif step == PipelineStep.YOUR_NEW_STEP:
    result = await self._handle_your_step(pipeline_id, step_num)

Update frontend UI in apps/web/app/page.tsx or component files:

typescriptconst steps = [
  // ... existing steps
  { id: 'your_new_step', name: 'Your Step', icon: YourIcon },
]
Method 2: Adding a New LLM Provider

Create provider class in apps/api/app/core/llm/your_provider.py:

pythonfrom app.core.llm.base import BaseLLMProvider, LLMResponse

class YourProvider(BaseLLMProvider):
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        # Implementation
        pass
    
    async def validate_connection(self) -> bool:
        # Check if provider is accessible
        pass

Update config in apps/api/app/config.py:

python# Add configuration fields
your_provider_api_key: Optional[str] = None
your_provider_endpoint: str = "https://api.your-provider.com"

Register in pipeline manager in apps/api/app/core/pipeline/manager.py:

pythonelif config["provider"] == "your_provider":
    return YourProvider(config)
Method 3: Adding UI Components

Create component file in apps/web/components/:

bashcat > components/your-component.tsx << 'EOF'
'use client'

export function YourComponent() {
  return (
    <div className="card-bg rounded-2xl p-6">
      {/* Component content */}
    </div>
  )
}
EOF

Import and use in pages:

typescriptimport { YourComponent } from '@/components/your-component'
Common Development Patterns
File Creation Pattern
Always use cat > filename << 'EOF' for creating files to avoid quote escaping issues:
bashcat > path/to/file.tsx << 'EOF'
// File content here
EOF
Styling Pattern
Use CSS variables defined in globals.css:

var(--bg-dark) - Main background
var(--bg-card) - Card backgrounds
var(--border-color) - Borders
.gradient-purple-blue - Gradient backgrounds
.card-bg - Card styling class

API Pattern
All API calls go through apps/web/lib/api.ts:
typescriptexport const api = {
  yourNewEndpoint: async (param: string) => {
    const response = await fetch(`${API_URL}/api/your-endpoint/${param}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: 'value' })
    })
    return response.json()
  }
}
Running the Project
Development Mode
bash# Terminal 1 - Backend
cd apps/api
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend (runs on port 3001)
cd apps/web
npm run dev

# Terminal 3 - Redis (optional for caching)
docker run -d -p 6379:6379 redis:alpine

API Endpoints Available
- GET  /health - Health check
- GET  /docs - Interactive API documentation
- POST /api/documents/upload - Upload documents
- POST /api/pipeline/create - Create new pipeline
- POST /api/pipeline/{id}/execute/{step} - Execute specific step
- GET  /api/pipeline/{id}/status - Get pipeline status
- WS   /ws/{pipeline_id} - WebSocket for real-time updates
Common Issues & Fixes

Module not found errors: Check tsconfig.json has path aliases:

json"baseUrl": ".",
"paths": { "@/*": ["./*"] }

CORS errors: Ensure backend allows frontend origin in main.py
Styling not applying: Clear Next.js cache:

bashrm -rf .next
npm run dev
Next Steps for Completion

Implement document processing: Add actual file parsing in apps/api/app/api/endpoints/documents.py
Connect LLM providers: Add API keys to .env and test each provider
Add WebSocket updates: Implement real-time progress in apps/api/app/api/endpoints/websocket.py
Create result visualizations: Add components for displaying threats, DFDs, attack paths
Add authentication: Implement user sessions if needed
Deploy: Dockerize completely and deploy to cloud platform

Key Files Reference

Frontend entry: apps/web/app/page.tsx
API entry: apps/api/app/main.py
State management: apps/web/lib/store.ts
API client: apps/web/lib/api.ts
Pipeline logic: apps/api/app/core/pipeline/manager.py
DFD extraction: apps/api/app/core/pipeline/dfd_extraction_service.py
LLM providers: apps/api/app/core/llm/*.py
DFD Review UI: apps/web/components/pipeline/steps/dfd-review.tsx
Styling: apps/web/app/globals.css
Environment: apps/api/.env and apps/web/.env.local

This structure allows for modular development where features can be added incrementally without breaking existing functionality.

Recent Updates (Jan 2025):

✅ Added DFD Review step to the pipeline
✅ Implemented comprehensive DFD extraction service with LLM integration
✅ Created Scaleway LLM provider with proper authentication
✅ Fixed all Pydantic validation errors
✅ Established proper module structure with __init__.py files
✅ Updated pipeline manager with DFD review handler
✅ Added WebSocket connection management in frontend
✅ Implemented file upload validation and error handling
✅ **NEW: Added DFD visualization with JSON and Mermaid diagram tabs**
✅ **NEW: Implemented full DFD editing capabilities with add/remove functions**
✅ **NEW: Added manual review requirement at each pipeline step**
✅ **NEW: Created tabbed interface for viewing extracted data**

Previous Updates:

Perfect! I've fixed the Pydantic validation errors. The main issues were:
📝 What was fixed:

Updated config.py to include all the environment variables from your .env file
Added extra = "ignore" in the Config class to prevent validation errors for undefined fields
Updated the LLM provider factory to use settings object instead of os.getenv
Created all missing __init__.py files for proper Python module structure

🗂️ Required Directory Structure:
Make sure your directory structure looks like this:
apps/api/
├── app/
│   ├── __init__.py                    ✅ Created
│   ├── main.py
│   ├── config.py                      ✅ Fixed
│   ├── api/
│   │   ├── __init__.py                ✅ Created
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       ├── documents.py
│   │       ├── pipeline.py
│   │       ├── websocket.py
│   │       └── llm.py
│   ├── core/
│   │   ├── __init__.py                ✅ Created
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── ollama.py
│   │   │   ├── azure.py
│   │   │   └── scaleway.py
│   │   └── pipeline/
│   │       ├── __init__.py            ✅ Created
│   │       ├── manager.py
│   │       └── dfd_extraction_service.py
│   └── models/
│       ├── __init__.py                ✅ Created
│       └── dfd.py
├── requirements.txt
├── .env
└── venv/
🚀 Now try running the backend again:
bashcd apps/api
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
The server should now start successfully! You should see:

INFO: Uvicorn running on http://0.0.0.0:8000
The API docs at http://localhost:8000/docs
Health check at http://localhost:8000/health

If you still get errors, they might be related to missing dependencies. Make sure you've installed all requirements:
bashpip install -r requirements.txt
The configuration now properly handles all your environment variables and won't throw validation errors.

Environment Variables Configuration

The .env file includes:
- LLM provider settings for Ollama, Azure OpenAI, and Scaleway
- Step-specific model configurations (STEP1_MODEL, STEP2_MODEL, etc.)
- Default provider selection per pipeline step
- CORS origins configuration (currently set to * for development)
- Redis URL for optional caching
- File upload limits and allowed extensions

Note: The Scaleway API key in the .env file appears to be active. Ensure this is properly secured and rotated regularly.