'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Plus, 
  Settings, 
  Play, 
  Save, 
  Trash2, 
  Bot, 
  ArrowUp, 
  ArrowDown,
  AlertCircle,
  CheckCircle2,
  Clock
} from 'lucide-react';

interface Agent {
  name: string;
  version: string;
  description: string;
  category: string;
  priority: number;
  requires_document: boolean;
  requires_components: boolean;
  estimated_tokens: number;
  enabled_by_default: boolean;
}

interface WorkflowStep {
  id: string;
  name: string;
  description: string;
  agent_type: string;
  automation_enabled: boolean;
  confidence_threshold: number;
  review_required: boolean;
  timeout_minutes: number;
}

interface WorkflowTemplate {
  id?: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  automation_settings: {
    enabled: boolean;
    confidence_threshold: number;
    max_auto_approvals_per_day: number;
    business_hours_only: boolean;
    notification_level: string;
  };
  client_access_rules: {
    authentication_method: string;
    token_expiry_days: number;
    allowed_actions: string[];
    data_retention_days: number;
  };
}

export function WorkflowBuilder() {
  const [template, setTemplate] = useState<WorkflowTemplate>({
    name: '',
    description: '',
    steps: [],
    automation_settings: {
      enabled: true,
      confidence_threshold: 0.85,
      max_auto_approvals_per_day: 50,
      business_hours_only: false,
      notification_level: 'summary'
    },
    client_access_rules: {
      authentication_method: 'token',
      token_expiry_days: 30,
      allowed_actions: ['view', 'edit', 'export'],
      data_retention_days: 90
    }
  });

  const [availableAgents, setAvailableAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  // Load available agents on component mount
  useEffect(() => {
    loadAvailableAgents();
  }, []);

  const loadAvailableAgents = async () => {
    try {
      const response = await fetch('/api/workflows/agents');
      const data = await response.json();
      setAvailableAgents(data.agents);
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };

  const addStep = () => {
    if (!selectedAgent) return;
    
    const agent = availableAgents.find(a => a.name === selectedAgent);
    if (!agent) return;

    const newStep: WorkflowStep = {
      id: `step_${Date.now()}`,
      name: `${agent.description} Step`,
      description: agent.description,
      agent_type: agent.name,
      automation_enabled: agent.enabled_by_default,
      confidence_threshold: 0.8,
      review_required: false,
      timeout_minutes: 30
    };

    setTemplate(prev => ({
      ...prev,
      steps: [...prev.steps, newStep]
    }));

    setSelectedAgent('');
  };

  const removeStep = (stepId: string) => {
    setTemplate(prev => ({
      ...prev,
      steps: prev.steps.filter(step => step.id !== stepId)
    }));
  };

  const moveStep = (stepId: string, direction: 'up' | 'down') => {
    const steps = [...template.steps];
    const index = steps.findIndex(step => step.id === stepId);
    
    if (index === -1) return;
    
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= steps.length) return;
    
    [steps[index], steps[newIndex]] = [steps[newIndex], steps[index]];
    
    setTemplate(prev => ({ ...prev, steps }));
  };

  const updateStep = (stepId: string, updates: Partial<WorkflowStep>) => {
    setTemplate(prev => ({
      ...prev,
      steps: prev.steps.map(step => 
        step.id === stepId ? { ...step, ...updates } : step
      )
    }));
  };

  const saveTemplate = async () => {
    setIsLoading(true);
    setSaveStatus('saving');
    
    try {
      const response = await fetch('/api/workflows/templates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: template.name,
          description: template.description,
          steps: template.steps.map(step => ({
            id: step.id,
            name: step.name,
            description: step.description,
            agent_type: step.agent_type,
            automation_enabled: step.automation_enabled,
            confidence_threshold: step.confidence_threshold,
            review_required: step.review_required,
            timeout_minutes: step.timeout_minutes,
            required_inputs: [],
            optional_parameters: {},
            retry_limit: 3
          })),
          automation_settings: template.automation_settings,
          client_access_rules: template.client_access_rules
        })
      });

      if (response.ok) {
        setSaveStatus('saved');
        setTimeout(() => setSaveStatus('idle'), 2000);
      } else {
        throw new Error('Failed to save template');
      }
    } catch (error) {
      console.error('Failed to save template:', error);
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } finally {
      setIsLoading(false);
    }
  };

  const testWorkflow = async () => {
    if (template.steps.length === 0) {
      alert('Please add at least one step to test the workflow');
      return;
    }

    setIsLoading(true);
    
    try {
      // First save the template if not saved
      if (saveStatus !== 'saved') {
        await saveTemplate();
      }
      
      // Then start a test execution
      const response = await fetch('/api/workflows/executions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          template_id: template.id || 'test',
          client_id: 'test_client',
          client_email: 'test@example.com',
          initial_data: {
            document_content: 'Test document content for workflow validation'
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Test workflow started! Execution ID: ${data.execution_id}`);
      }
    } catch (error) {
      console.error('Failed to test workflow:', error);
      alert('Failed to start test workflow');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Workflow Builder</h1>
          <p className="text-gray-600 mt-1">Create and configure agent-based threat modeling workflows</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            onClick={testWorkflow}
            disabled={isLoading || template.steps.length === 0}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Play className="w-4 h-4 mr-2" />
            Test Workflow
          </Button>
          
          <Button
            onClick={saveTemplate}
            disabled={isLoading || !template.name}
            variant={saveStatus === 'saved' ? 'default' : 'outline'}
            className={saveStatus === 'saved' ? 'bg-green-600 hover:bg-green-700 text-white' : ''}
          >
            {saveStatus === 'saving' && <Clock className="w-4 h-4 mr-2 animate-spin" />}
            {saveStatus === 'saved' && <CheckCircle2 className="w-4 h-4 mr-2" />}
            {saveStatus === 'error' && <AlertCircle className="w-4 h-4 mr-2" />}
            {saveStatus === 'idle' && <Save className="w-4 h-4 mr-2" />}
            {saveStatus === 'saving' ? 'Saving...' : 
             saveStatus === 'saved' ? 'Saved!' : 
             saveStatus === 'error' ? 'Error!' : 'Save Template'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Template Configuration */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>Template Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template Name *
                </label>
                <input
                  type="text"
                  value={template.name}
                  onChange={(e) => setTemplate(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Standard Threat Assessment"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={template.description}
                  onChange={(e) => setTemplate(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Describe the purpose and scope of this workflow..."
                />
              </div>
            </CardContent>
          </Card>

          {/* Workflow Steps */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Bot className="w-5 h-5 mr-2" />
                Workflow Steps ({template.steps.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {template.steps.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Bot className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>No steps added yet. Select an agent below to get started.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {template.steps.map((step, index) => (
                    <div key={step.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <Badge variant="outline" className="text-xs">
                              Step {index + 1}
                            </Badge>
                            <span className="font-medium text-gray-900">{step.name}</span>
                          </div>
                          
                          <p className="text-sm text-gray-600 mb-3">{step.description}</p>
                          
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <label className="block text-gray-700 mb-1">Agent Type</label>
                              <Badge variant="secondary">{step.agent_type}</Badge>
                            </div>
                            
                            <div>
                              <label className="block text-gray-700 mb-1">Confidence Threshold</label>
                              <input
                                type="range"
                                min="0.1"
                                max="1.0"
                                step="0.1"
                                value={step.confidence_threshold}
                                onChange={(e) => updateStep(step.id, { 
                                  confidence_threshold: parseFloat(e.target.value) 
                                })}
                                className="w-full"
                              />
                              <span className="text-xs text-gray-500">
                                {(step.confidence_threshold * 100).toFixed(0)}%
                              </span>
                            </div>
                            
                            <div className="flex items-center space-x-2">
                              <input
                                type="checkbox"
                                checked={step.automation_enabled}
                                onChange={(e) => updateStep(step.id, { 
                                  automation_enabled: e.target.checked 
                                })}
                                className="rounded"
                              />
                              <span>Enable Automation</span>
                            </div>
                            
                            <div className="flex items-center space-x-2">
                              <input
                                type="checkbox"
                                checked={step.review_required}
                                onChange={(e) => updateStep(step.id, { 
                                  review_required: e.target.checked 
                                })}
                                className="rounded"
                              />
                              <span>Require Review</span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex flex-col space-y-1 ml-4">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => moveStep(step.id, 'up')}
                            disabled={index === 0}
                          >
                            <ArrowUp className="w-3 h-3" />
                          </Button>
                          
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => moveStep(step.id, 'down')}
                            disabled={index === template.steps.length - 1}
                          >
                            <ArrowDown className="w-3 h-3" />
                          </Button>
                          
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => removeStep(step.id)}
                            className="text-red-600 hover:bg-red-50"
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Agent Selection & Settings */}
        <div className="space-y-6">
          {/* Add Agent */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Plus className="w-5 h-5 mr-2" />
                Add Step
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <select
                  value={selectedAgent}
                  onChange={(e) => setSelectedAgent(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select an agent...</option>
                  {availableAgents.map((agent) => (
                    <option key={agent.name} value={agent.name}>
                      {agent.description} ({agent.category})
                    </option>
                  ))}
                </select>
                
                <Button
                  onClick={addStep}
                  disabled={!selectedAgent}
                  className="w-full"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Step
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Automation Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="w-5 h-5 mr-2" />
                Automation Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700">Enable Automation</span>
                <input
                  type="checkbox"
                  checked={template.automation_settings.enabled}
                  onChange={(e) => setTemplate(prev => ({
                    ...prev,
                    automation_settings: {
                      ...prev.automation_settings,
                      enabled: e.target.checked
                    }
                  }))}
                  className="rounded"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  Global Confidence Threshold
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.05"
                  value={template.automation_settings.confidence_threshold}
                  onChange={(e) => setTemplate(prev => ({
                    ...prev,
                    automation_settings: {
                      ...prev.automation_settings,
                      confidence_threshold: parseFloat(e.target.value)
                    }
                  }))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Conservative</span>
                  <span>{(template.automation_settings.confidence_threshold * 100).toFixed(0)}%</span>
                  <span>Aggressive</span>
                </div>
              </div>
              
              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  Max Auto-approvals per Day
                </label>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={template.automation_settings.max_auto_approvals_per_day}
                  onChange={(e) => setTemplate(prev => ({
                    ...prev,
                    automation_settings: {
                      ...prev.automation_settings,
                      max_auto_approvals_per_day: parseInt(e.target.value) || 50
                    }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
            </CardContent>
          </Card>

          {/* Progress Indicator */}
          {template.steps.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Template Progress</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span>Steps configured</span>
                    <span>{template.steps.length}</span>
                  </div>
                  
                  <Progress value={template.name ? 50 + (template.steps.length * 10) : 0} />
                  
                  <div className="text-xs text-gray-500">
                    {!template.name && "❌ Template name required"}
                    {template.name && template.steps.length === 0 && "❌ At least one step required"}
                    {template.name && template.steps.length > 0 && "✅ Ready to save and test"}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}