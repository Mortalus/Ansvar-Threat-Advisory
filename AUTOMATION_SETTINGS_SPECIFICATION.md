# Automation Settings Specification

## 🎯 **Overview**
Provide clients with granular control over workflow automation, allowing them to balance efficiency with oversight based on their risk tolerance and operational preferences.

## 🔧 **Automation Toggle System**

### **Per-Step Automation Controls**
Each workflow step can be configured with:

```typescript
interface AutomationSettings {
  enabled: boolean;                    // Master automation toggle
  confidence_threshold: number;       // 0-100, minimum confidence for auto-approval
  max_auto_approvals: number;         // Daily limit on automatic approvals
  require_review_after: number;       // Hours after which manual review is required
  notification_level: NotificationLevel; // 'none' | 'summary' | 'detailed' | 'realtime'
  fallback_to_manual: boolean;        // Fallback when automation fails
  business_hours_only: boolean;       // Restrict automation to business hours
  approval_rules: ApprovalRule[];     // Custom conditions for automation
}

interface ApprovalRule {
  condition: string;                   // "confidence > 85 AND data_quality > 90"
  action: 'auto_approve' | 'flag_review' | 'require_manual';
  description: string;
}
```

### **Automation Categories**

#### **1. Document Processing Automation**
- **Auto-Extract**: Automatically extract data from common document formats
- **Auto-Classify**: Categorize documents by type and sensitivity
- **Auto-Validate**: Check for completeness and format compliance

```yaml
document_automation:
  auto_extract:
    enabled: true
    confidence_threshold: 80
    supported_formats: ["pdf", "docx", "txt"]
  auto_classify:
    enabled: true
    confidence_threshold: 85
    categories: ["architecture", "requirements", "policies"]
  auto_validate:
    enabled: true
    checks: ["completeness", "format", "readability"]
```

#### **2. DFD Generation Automation**
- **Auto-Generate**: Create initial DFD from document analysis
- **Auto-Enhance**: Add missing components and connections
- **Auto-Validate**: Check logical consistency and completeness

```yaml
dfd_automation:
  auto_generate:
    enabled: true
    confidence_threshold: 75
    max_components: 50
  auto_enhance:
    enabled: false  # Usually requires human oversight
    confidence_threshold: 90
  auto_validate:
    enabled: true
    checks: ["connectivity", "data_flows", "trust_boundaries"]
```

#### **3. Threat Analysis Automation**
- **Auto-Identify**: Discover threats using STRIDE methodology
- **Auto-Prioritize**: Rank threats by severity and likelihood
- **Auto-Suggest**: Generate initial mitigation recommendations

```yaml
threat_automation:
  auto_identify:
    enabled: true
    confidence_threshold: 70
    methodologies: ["STRIDE", "PASTA", "OCTAVE"]
  auto_prioritize:
    enabled: true
    confidence_threshold: 85
    factors: ["impact", "likelihood", "exploitability"]
  auto_suggest:
    enabled: false  # Usually requires domain expertise
    confidence_threshold: 95
```

## 📊 **Confidence Scoring System**

### **Confidence Calculation**
```python
def calculate_confidence(step_data: dict) -> float:
    """Calculate confidence score for automation decision"""
    factors = {
        'data_quality': assess_data_quality(step_data),
        'model_certainty': get_model_confidence(step_data),
        'historical_accuracy': get_historical_performance(),
        'input_completeness': check_input_completeness(step_data),
        'domain_complexity': assess_domain_complexity(step_data)
    }
    
    # Weighted average based on step type
    weights = get_step_weights(step_data['step_type'])
    confidence = sum(factors[k] * weights[k] for k in factors.keys())
    
    return min(100, max(0, confidence))
```

### **Quality Indicators**
- **Data Quality** (0-100): Completeness, consistency, and format validation
- **Model Certainty** (0-100): AI model confidence in its predictions
- **Historical Accuracy** (0-100): Past performance on similar inputs
- **Input Completeness** (0-100): Percentage of required fields populated
- **Domain Complexity** (0-100): Inverse of problem complexity

## 🎛️ **User Interface Controls**

### **Admin Configuration Interface**
```typescript
interface AutomationInsights {
  current_automation_rate: number;    // Percentage of steps automated
  accuracy_trend: TimeSeries;         // Historical accuracy over time
  efficiency_gains: EfficiencyMetrics; // Time and cost savings
  error_patterns: ErrorAnalysis;      // Common failure modes
  client_satisfaction: SatisfactionMetrics; // User feedback scores
}

function AutomationSettings({ workflowId }: { workflowId: string }) {
  return (
    <div className="automation-dashboard">
      <AutomationInsights insights={insights} />
      
      <div className="step-controls">
        {workflow.steps.map(step => (
          <StepAutomationControl
            key={step.id}
            step={step}
            settings={step.automation_settings}
            onUpdate={updateAutomationSettings}
          />
        ))}
      </div>
      
      <div className="global-controls">
        <BusinessHoursToggle />
        <EmergencyOverride />
        <BulkConfigurationTools />
      </div>
    </div>
  );
}
```

### **Client Control Interface**
```typescript
function ClientAutomationControls({ executionId }: { executionId: string }) {
  return (
    <div className="client-automation">
      <div className="quick-toggles">
        <Toggle label="Trust DFD Generation" />
        <Toggle label="Auto-approve Low Risk Threats" />
        <Toggle label="Skip Review for High Confidence" />
      </div>
      
      <div className="advanced-settings">
        <ConfidenceSlider 
          label="Minimum Confidence for Auto-approval"
          value={confidenceThreshold}
          onChange={setConfidenceThreshold}
        />
        
        <NotificationPreferences />
        <BusinessHoursRestriction />
      </div>
    </div>
  );
}
```

## 🔍 **Monitoring & Learning**

### **Automation Analytics**
```python
class AutomationAnalytics:
    def __init__(self):
        self.metrics = {
            'automation_rate': 0.0,
            'accuracy_score': 0.0,
            'time_savings': timedelta(0),
            'client_satisfaction': 0.0,
            'error_rate': 0.0
        }
    
    def track_decision(self, step_id: str, automated: bool, 
                      confidence: float, outcome: str):
        """Track automation decisions for learning"""
        self.store_decision({
            'step_id': step_id,
            'automated': automated,
            'confidence': confidence,
            'outcome': outcome,  # 'correct', 'corrected', 'rejected'
            'timestamp': datetime.utcnow()
        })
    
    def update_thresholds(self) -> Dict[str, float]:
        """Dynamically adjust confidence thresholds based on performance"""
        performance_data = self.get_recent_performance()
        
        # Increase threshold if too many false positives
        # Decrease threshold if missing valid automation opportunities
        return self.optimize_thresholds(performance_data)
```

### **Learning System**
- **Performance Tracking**: Monitor accuracy of automated decisions
- **Pattern Recognition**: Identify successful automation patterns
- **Threshold Optimization**: Automatically adjust confidence thresholds
- **Client Feedback Integration**: Learn from user corrections and preferences
- **Model Retraining**: Periodically retrain models with new data

## ⚙️ **Advanced Automation Features**

### **Smart Defaults**
```python
def generate_smart_defaults(client_profile: ClientProfile) -> AutomationSettings:
    """Generate personalized automation settings based on client characteristics"""
    
    if client_profile.industry == "finance":
        return AutomationSettings(
            confidence_threshold=90,  # High confidence required
            max_auto_approvals=5,     # Conservative automation
            require_review_after=2,   # Quick manual review cycles
            business_hours_only=True  # Regulatory compliance
        )
    elif client_profile.risk_tolerance == "high":
        return AutomationSettings(
            confidence_threshold=70,  # Lower threshold for speed
            max_auto_approvals=50,    # High automation volume
            require_review_after=24,  # Longer review cycles
            business_hours_only=False # 24/7 automation
        )
    
    return get_default_settings()
```

### **Contextual Automation**
- **Document Type Awareness**: Different automation rules for different document types
- **Industry Compliance**: Automatically adjust settings based on regulatory requirements
- **Client History**: Learn from past client preferences and feedback
- **Threat Landscape**: Adjust automation based on current threat intelligence
- **Seasonal Patterns**: Account for business cycles and peak periods

### **Emergency Controls**
- **Manual Override**: Instantly disable all automation when needed
- **Step-by-Step Control**: Selectively enable/disable automation per step
- **Rollback Capability**: Undo automated decisions and restart manual process
- **Audit Trail**: Complete log of all automation decisions and overrides

## 📈 **Success Metrics**

### **Efficiency Metrics**
- **Time Savings**: Average reduction in workflow completion time
- **Resource Utilization**: Reduction in manual effort required
- **Throughput**: Increase in workflows processed per day
- **Cost Reduction**: Decrease in operational costs per workflow

### **Quality Metrics**
- **Accuracy Rate**: Percentage of automated decisions that are correct
- **Error Rate**: Frequency of automation errors requiring correction
- **Client Satisfaction**: User feedback on automation quality
- **Compliance Score**: Adherence to regulatory and security requirements

### **Learning Metrics**
- **Threshold Optimization**: Improvement in optimal confidence thresholds over time
- **Pattern Recognition**: Success rate in identifying automation opportunities
- **Adaptation Speed**: How quickly the system adapts to new patterns
- **Prediction Accuracy**: How well the system predicts automation success

## 🚨 **Risk Management**

### **Automation Safeguards**
- **Circuit Breakers**: Automatically disable automation if error rates spike
- **Gradual Rollout**: Slowly increase automation levels as confidence grows
- **Human in the Loop**: Always maintain human oversight capability
- **Audit Requirements**: Ensure all automated decisions are auditable
- **Compliance Checks**: Verify automation decisions meet regulatory requirements

### **Failure Modes**
- **False Positives**: Automation approves incorrect results
- **False Negatives**: Automation rejects valid results
- **System Failures**: Technical issues preventing automation
- **Model Drift**: Performance degradation over time
- **Edge Cases**: Unusual inputs that confuse automation logic

### **Recovery Procedures**
- **Immediate Fallback**: Automatic switch to manual mode on detection of issues
- **Error Analysis**: Systematic investigation of automation failures
- **Model Updates**: Rapid deployment of fixes and improvements
- **Client Communication**: Transparent reporting of automation issues
- **Continuous Monitoring**: Real-time tracking of automation performance