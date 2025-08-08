# Workflow UI Access Guide

## How to Access the Workflow Builder

### 1. Login to the Application
- Navigate to: **http://localhost:3001** (or http://localhost:80)
- Login with:
  - Username: `admin`
  - Password: `admin123!`

### 2. Access Admin Workflow Builder
After login, navigate directly to:
- **http://localhost:3001/admin/workflow-builder**

### 3. Available Admin Pages

#### Workflow Management
- **Workflow Builder**: http://localhost:3001/admin/workflow-builder
  - Create and configure workflow templates
  - Add agents to workflows
  - Set automation rules and confidence thresholds
  
- **Workflow Executions**: http://localhost:3001/admin/workflow-executions
  - View running and completed workflow executions
  - Monitor workflow status

#### Agent Management
- **Agent Catalog**: http://localhost:3001/admin/agents
  - View available agents
  - Check agent health and metrics
  - Configure agent settings

#### Other Admin Tools
- **Prompt Editor**: http://localhost:3001/admin/prompt-editor
  - Manage and version prompt templates
  
- **System Monitor**: http://localhost:3001/admin/system-monitor
  - View system health
  - Monitor queue status

## Current UI Limitations

⚠️ **Note**: The workflow builder UI is partially implemented:
- Template creation UI exists but may not be fully wired to backend
- Some features are scaffolded but not complete
- The main pipeline interface (at `/`) is the primary working interface

## Alternative: Use the Main Pipeline Interface

For immediate threat modeling work, use the main pipeline at:
- **http://localhost:3001/** (after login)

This provides:
1. Document upload
2. DFD extraction and review
3. Agent configuration
4. Threat generation
5. Threat refinement
6. Export capabilities

## Testing Workflow via API

If the UI is not fully functional, you can test workflows via API:

```bash
# Create a workflow template
curl -X POST http://localhost/api/workflows/templates \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Workflow",
    "description": "Testing workflow",
    "steps": [...]
  }'

# Execute a workflow
curl -X POST http://localhost/api/workflows/templates/{template_id}/execute \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Execution",
    "inputs": {...}
  }'
```

## Project Management

For project and session management:
- **http://localhost:3001/projects**
  - Create and manage projects
  - Load previous sessions
  - Resume incomplete pipelines