# Changelog

All notable changes to this project will be documented in this file.

## 2025-08-08

### Documentation
- README.md
  - Updated to 7-step pipeline (adds DFD Review and Agent Configuration steps)
  - Corrected ports (Frontend http://localhost:3001)
  - Switched Docker quick start to `./docker-start.sh`
  - Added “Pipeline-first integration” section with core endpoints and WebSocket path
- DOCKER.md
  - Corrected service count to 8 and clarified Ollama is optional
- AGENT-FLOW-TEST-RESULTS.md
  - Corrected frontend URL to http://localhost:3001
- FLOW.md
  - Prepended note about pipeline-first flow and WebSocket usage; confirmed frontend port
- CLAUDE2.md
  - Added note that frontend now uses pipeline-first APIs with WebSockets; frontend port is 3001
- PROJECTS_STATUS_REPORT.md
  - Clarified wording on intermittent pooling issue for `/api/projects/*`

### Impact
- Aligns docs with actual application behavior (pipeline-first, background tasks, WebSockets)
- Reduces setup friction with accurate ports and startup commands
- Provides a single source of truth for recent changes




