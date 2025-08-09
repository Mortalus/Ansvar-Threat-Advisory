# Modular Workflow Implementation Plan

## 🎯 **Objective**
Create a fully modular, agent-based workflow system that modernizes the existing threat modeling pipeline while maintaining backward compatibility and adding enterprise features.

## 🏗️ **Architecture Overview**

### **Phase 1: Modular Agent Foundation**
Convert existing pipeline steps to modular agents that can be configured, reused, and combined flexibly.

#### **Agent Types to Implement**
1. **Document Processing Agents**
   - `DocumentUploadAgent`: Handle multiple file formats (PDF, DOCX, TXT)
   - `DocumentAnalysisAgent`: Extract and categorize content
   - `DataValidationAgent`: Ensure document quality and completeness

2. **DFD (Data Flow Diagram) Agents**
   - `DFDGenerationAgent`: Create initial DFD from document analysis
   - `DFDEnhancementAgent`: Add missing components and connections
   - `DFDValidationAgent`: Ensure logical consistency

3. **Threat Analysis Agents**
   - `ThreatIdentificationAgent`: Discover potential threats using STRIDE
   - `ThreatPriorizationAgent`: Risk assessment and severity scoring
   - `MitigationAgent`: Generate security recommendations

4. **Report Generation Agents**
   - `ReportComposerAgent`: Combine all analysis into coherent report
   - `ExecutiveSummaryAgent`: Generate C-level summaries
   - `ComplianceReportAgent`: Format for regulatory requirements

### **Phase 2: Workflow Template System**
Admin-configurable workflow templates that define step sequences, agent selections, and automation rules.

#### **Workflow Configuration Schema**
```python
class WorkflowTemplate:
    name: str
    description: str
    steps: List[WorkflowStep]
    client_access_rules: ClientAccessConfig
    automation_settings: AutomationConfig
    
class WorkflowStep:
    id: str
    name: str
    agent_type: str
    required_inputs: List[str]
    optional_parameters: Dict[str, Any]
    automation_enabled: bool
    confidence_threshold: float
    review_required: bool
```

### **Phase 3: Client Portal Interface**
User-friendly interface for clients to execute workflows with step-by-step guidance and data review.

#### **Key Features**
- **Progress Tracking**: Visual progress bars and step indicators
- **Data Review Points**: Manual validation checkpoints with approval/edit options
- **Real-time Updates**: WebSocket integration for live status updates
- **Result Visualization**: Interactive charts and diagrams
- **Export Options**: Multiple format support (PDF, DOCX, JSON)

## 🔧 **Implementation Details**

### **Database Schema Extensions**
```sql
-- Workflow Templates
CREATE TABLE workflow_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    steps JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Workflow Executions
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY,
    template_id UUID REFERENCES workflow_templates(id),
    client_id VARCHAR(255),
    current_step INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    data JSONB DEFAULT '{}',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

### **API Endpoints**
```python
# Admin Workflow Management
POST /api/admin/workflows - Create workflow template
GET /api/admin/workflows - List all templates
PUT /api/admin/workflows/{id} - Update template
DELETE /api/admin/workflows/{id} - Archive template

# Client Workflow Execution
POST /api/workflows/{template_id}/start - Initialize workflow
GET /api/workflows/{execution_id}/status - Get current status
POST /api/workflows/{execution_id}/step/{step_id}/submit - Submit step data
POST /api/workflows/{execution_id}/step/{step_id}/approve - Approve step results
```

## 🔒 **Security & Compliance**

### **Data Sovereignty**
- **Regional Data Storage**: EU/US/Local options
- **Encryption**: AES-256 for data at rest, TLS 1.3 for transit
- **Access Controls**: Role-based permissions with audit trails
- **Data Retention**: Configurable retention policies

### **Authentication Integration**
- **Primary**: Azure AD with SAML/OIDC
- **Fallback**: Local authentication with bcrypt
- **Session Management**: JWT with refresh tokens
- **Multi-factor**: TOTP support for high-security environments

## 📊 **Automation & Intelligence**

### **Confidence-Based Automation**
- **High Confidence (>90%)**: Auto-approve with notification
- **Medium Confidence (70-90%)**: Flag for quick review
- **Low Confidence (<70%)**: Require manual validation
- **Learning System**: Track approval patterns to improve thresholds

### **Quality Metrics**
- **Agent Performance**: Success rates and execution times
- **User Satisfaction**: Feedback collection and analysis
- **Accuracy Tracking**: Compare automated vs. manual results
- **Continuous Improvement**: Regular model retraining

## 🚀 **Implementation Status**

### **✅ Phase 1: Foundation - COMPLETED**
1. ✅ Implement base agent classes and registry
2. ✅ Convert existing pipeline steps to modular agents  
3. ✅ Create workflow template schema
4. ✅ Build admin interface for workflow management

**Key Deliverables:**
- Modular agent registry with 6 core agents (document_analysis, architectural_risk, business_financial, compliance_governance, data_flow_analysis, attack_path_analyzer)
- Database schema for WorkflowTemplate, WorkflowRun, WorkflowStepExecution, WorkflowArtifact
- Admin interfaces at `/admin/agents` and `/admin/workflow-builder`

### **✅ Phase 2: Workflow Engine - COMPLETED**
1. ✅ Implement core workflow execution engine with DAG validation
2. ✅ Add sequential execution with artifact management
3. ✅ Create Celery integration for async processing
4. ✅ Build comprehensive API endpoints for workflow management

**Key Deliverables:**
- `WorkflowService` with DAG validation and sequential execution
- `/api/phase2/workflow/*` endpoints for templates and runs
- Celery task integration for async workflow execution
- Artifact management and versioning system

### **✅ Phase 3: Client Portal Interface - COMPLETED**
1. ✅ Design and implement client portal UI
2. ✅ Add real-time progress tracking with WebSocket integration
3. ✅ Implement comprehensive navigation structure
4. ✅ Create demo capabilities and testing interfaces

**Key Deliverables:**
- Complete UX navigation: `/workflow-demo`, `/workflows`, `/workflows/templates`, `/workflows/history`, `/workflows/phase3`
- Real-time WebSocket integration for live workflow updates
- Template management with search, filtering, and DAG preview
- Execution history with detailed analytics
- Mobile-responsive design with Tailwind CSS
- Interactive demo capabilities

### **🔄 Phase 4: Advanced Features - IN PROGRESS**
**Next Phase Implementation:**
1. **Parallel Execution**: Multi-step concurrent processing
2. **Conditional Logic**: Branch-based workflow decisions
3. **Error Handlers**: Retry mechanisms and failure recovery
4. **Performance Optimization**: Caching and load balancing

### **📋 Phase 5: Intelligence & Automation - PLANNED**
1. Implement confidence scoring systems
2. Add automation rules and toggles  
3. Create performance monitoring dashboards
4. Add feedback loops for continuous improvement

### **🚀 Phase 6: Production Hardening - PLANNED**  
1. Security hardening and penetration testing
2. Performance optimization and load testing
3. Documentation and user training materials
4. Gradual rollout with monitoring and support

## 🎯 **Success Metrics**
- **Efficiency**: 50% reduction in manual review time
- **Quality**: Maintain >95% accuracy while increasing automation
- **User Satisfaction**: >90% user approval ratings
- **Scalability**: Support 10x current workflow volume
- **Security**: Zero data breaches with full audit compliance

## Default Template: Threat Modeling (Standard)

The system seeds a default workflow template at startup named "Threat Modeling (Standard)" with a minimum of three modular agents and optional steps:

```
Steps:
1) Document Upload → agent: document_analysis (automation on)
2) DFD Extraction (Enhanced) → agent: data_flow_analysis (review gate)
3) Architectural Risk Agent → agent: architectural_risk (review gate)
4) Business & Financial Risk Agent → agent: business_financial (review gate)
5) Compliance & Governance Agent → agent: compliance_governance (review gate)
6) Threat Refinement → agent: threat_refinement (review gate)
7) Attack Path Analysis (Optional) → agent: attack_path_analyzer (automation on)
```

Prompt-level input/output control:
- Each step may specify `optional_parameters`, e.g. `existing_threats_limit` to cap how many prior threats are fed into the next agent's prompt, keeping chaining controlled at the prompt level.
- The workflow engine merges `parameters` and `optional_parameters` and enforces reasonable defaults defensively.

Automation policy:
- Global `automation_settings.enabled` defaults to false (review-by-default). Steps can opt-in to auto-run based on confidence thresholds.