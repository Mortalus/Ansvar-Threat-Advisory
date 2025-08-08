# Threat Modeling Pipeline Platform

A robust AI-powered threat modeling pipeline that processes security documents through multiple analysis stages using configurable LLM providers.

## Features

- 📄 **Document Processing**: Support for PDF, DOCX, and TXT files
- 🤖 **Multi-LLM Support**: Ollama (local), Azure OpenAI, and Scaleway
- 🔄 **7-Step Pipeline**:
  1. Document Upload
  2. DFD Extraction
  3. DFD Review (interactive)
  4. Agent Configuration (select agents)
  5. Threat Generation (multi-agent)
  6. Threat Refinement
  7. Attack Path Analysis (optional)
- ⚡ **Real-time Updates**: WebSocket support for live pipeline status
- 🎨 **Modern UI**: Dark theme with gradient accents
- 🔧 **Flexible Configuration**: Different LLM providers per step

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose (optional)
- Redis (or use Docker)

### Installation

1. Clone the repository:
\`\`\`bash
git clone <your-repo-url>
cd threat-modeling-platform
\`\`\`

2. Install dependencies:
\`\`\`bash
# Install root dependencies
npm install

# Install frontend dependencies
cd apps/web
npm install
cd ../..

# Install backend dependencies
cd apps/api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ../..
\`\`\`

3. Configure environment variables:
\`\`\`bash
# Backend configuration
cp apps/api/.env.example apps/api/.env
# Edit apps/api/.env with your LLM provider credentials

# Frontend configuration
cp apps/web/.env.local.example apps/web/.env.local
\`\`\`

### Running the Application

#### Option 1: Using Docker (Recommended)
```bash
./docker-start.sh
```

#### Option 2: Manual Setup

Start each service in a separate terminal:

\`\`\`bash
# Terminal 1: Redis
redis-server

# Terminal 2: Backend API
cd apps/api
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Frontend
cd apps/web
npm run dev

# Terminal 4: Ollama (if using local LLMs)
ollama serve
\`\`\`

#### Option 3: Using npm scripts
\`\`\`bash
# Start Redis in Docker
docker run -d -p 6379:6379 redis:alpine

# Start both frontend and backend
npm run dev
\`\`\`

### Access the Application

- **Web UI**: http://localhost:3001
- **API Documentation**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws/{pipeline_id}

### Pipeline-first integration

The UI and API use a pipeline-first flow with background execution:
- Create: `POST /api/pipeline/create`
- Execute step (background): `POST /api/tasks/execute-step`
- Execute step (sync): `POST /api/pipeline/{id}/step/{step}`
- Status: `GET /api/pipeline/{id}/status`
- WebSocket: `/ws/{pipeline_id}`

## Configuration

### LLM Providers

Configure your LLM providers in `apps/api/.env`:

#### Ollama (Local)
\`\`\`env
OLLAMA_BASE_URL=http://localhost:11434
STEP1_OLLAMA_MODEL=llama2
\`\`\`

#### Azure OpenAI
\`\`\`env
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview
STEP1_AZURE_MODEL=gpt-4
\`\`\`

#### Scaleway
\`\`\`env
SCALEWAY_API_KEY=your-api-key
SCALEWAY_ENDPOINT=https://api.scaleway.ai/v1
STEP1_SCALEWAY_MODEL=llama-3.1-70b
\`\`\`

### Step-specific Configuration

Each pipeline step can use a different LLM provider:

\`\`\`env
STEP1_LLM_PROVIDER=ollama
STEP2_LLM_PROVIDER=ollama
STEP3_LLM_PROVIDER=azure
STEP4_LLM_PROVIDER=azure
STEP5_LLM_PROVIDER=scaleway
\`\`\`

## Architecture

\`\`\`
threat-modeling-platform/
├── apps/
│   ├── api/          # FastAPI backend
│   └── web/          # Next.js frontend
├── packages/         # Shared packages (future)
├── docker-compose.yml
└── package.json
\`\`\`

## Development
### Default Workflow Template

At startup, the system seeds a default template named "Threat Modeling (Standard)" with a modular multi-agent flow:

- Document Analysis (`document_analysis`)
- DFD Extraction (`data_flow_analysis`)
- Architectural Risk (`architectural_risk`)
- Business & Financial (`business_financial`)
- Compliance & Governance (`compliance_governance`)
- Threat Refinement (`threat_refinement`)
- Attack Path Analysis (optional) (`attack_path_analyzer`)

Prompt-level chaining is controlled via step `optional_parameters` (e.g., `existing_threats_limit`) so each agent consumes a bounded subset of prior outputs.


### Backend Development
\`\`\`bash
cd apps/api
source venv/bin/activate
uvicorn app.main:app --reload
\`\`\`

### Frontend Development
\`\`\`bash
cd apps/web
npm run dev
\`\`\`

### Testing
\`\`\`bash
# Backend tests
cd apps/api
pytest

# Frontend tests
cd apps/web
npm test
\`\`\`

## Deployment

### Using Docker Compose
\`\`\`bash
docker-compose up -d
\`\`\`

### Manual Deployment
See deployment guides for:
- [Kubernetes deployment](./docs/k8s-deployment.md)
- [AWS deployment](./docs/aws-deployment.md)
- [Azure deployment](./docs/azure-deployment.md)

## License

MIT

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.