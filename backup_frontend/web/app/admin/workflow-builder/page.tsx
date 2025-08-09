"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Trash2, Plus, MoveUp, MoveDown, Settings, Play } from 'lucide-react';

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
  confidence_threshold: number;
  automation_enabled: boolean;
  review_required: boolean;
  timeout_minutes: number;
}

interface AutomationSettings {
  enabled: boolean;
  confidence_threshold: number;
  max_auto_approvals_per_day: number;
  business_hours_only: boolean;
  notification_level: string;
  fallback_to_manual: boolean;
}

export default function WorkflowBuilderPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [template, setTemplate] = useState({
    name: '',
    description: '',
    steps: [] as WorkflowStep[],
    automation_settings: {
      enabled: true,
      confidence_threshold: 0.85,
      max_auto_approvals_per_day: 50,
      business_hours_only: false,
      notification_level: 'summary',
      fallback_to_manual: true,
    } as AutomationSettings,
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  // Load available agents
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const response = await fetch('/api/workflows/agents');
        const data = await response.json();
        setAgents(data.agents || []);
      } catch (error) {
        console.error('Failed to load agents:', error);
        setMessage({type: 'error', text: 'Failed to load available agents'});
      }
    };
    loadAgents();
  }, []);

  const addStep = () => {
    const newStep: WorkflowStep = {
      id: `step_${Date.now()}`,
      name: `Step ${template.steps.length + 1}`,
      description: '',
      agent_type: '',
      confidence_threshold: 0.8,
      automation_enabled: true,
      review_required: false,
      timeout_minutes: 30,
    };
    setTemplate(prev => ({
      ...prev,
      steps: [...prev.steps, newStep]
    }));
  };

  const updateStep = (index: number, field: keyof WorkflowStep, value: any) => {
    setTemplate(prev => ({
      ...prev,
      steps: prev.steps.map((step, i) => 
        i === index ? { ...step, [field]: value } : step
      )
    }));
  };

  const removeStep = (index: number) => {
    setTemplate(prev => ({
      ...prev,
      steps: prev.steps.filter((_, i) => i !== index)
    }));
  };

  const moveStep = (index: number, direction: 'up' | 'down') => {
    const newSteps = [...template.steps];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (targetIndex >= 0 && targetIndex < newSteps.length) {
      [newSteps[index], newSteps[targetIndex]] = [newSteps[targetIndex], newSteps[index]];
      setTemplate(prev => ({ ...prev, steps: newSteps }));
    }
  };

  const createTemplate = async () => {
    if (!template.name.trim()) {
      setMessage({type: 'error', text: 'Template name is required'});
      return;
    }
    
    if (template.steps.length === 0) {
      setMessage({type: 'error', text: 'At least one workflow step is required'});
      return;
    }

    // Validate all steps have agents selected
    for (const step of template.steps) {
      if (!step.agent_type) {
        setMessage({type: 'error', text: `Agent selection is required for step: ${step.name}`});
        return;
      }
    }

    setLoading(true);
    setMessage(null);

    try {
      const response = await fetch('/api/workflows/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(template),
      });

      const result = await response.json();

      if (response.ok) {
        setMessage({type: 'success', text: `Template "${template.name}" created successfully!`});
        // Reset form
        setTemplate({
          name: '',
          description: '',
          steps: [],
          automation_settings: {
            enabled: true,
            confidence_threshold: 0.85,
            max_auto_approvals_per_day: 50,
            business_hours_only: false,
            notification_level: 'summary',
            fallback_to_manual: true,
          },
        });
      } else {
        setMessage({type: 'error', text: result.detail || 'Failed to create template'});
      }
    } catch (error) {
      console.error('Create template error:', error);
      setMessage({type: 'error', text: 'Network error creating template'});
    } finally {
      setLoading(false);
    }
  };

  const testWorkflow = async () => {
    if (template.steps.length === 0) {
      setMessage({type: 'error', text: 'Add workflow steps before testing'});
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      // Create a temporary template and execute it
      const testTemplate = {
        ...template,
        name: `Test_${template.name || 'Workflow'}_${Date.now()}`,
      };

      const templateResponse = await fetch('/api/workflows/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testTemplate),
      });

      if (!templateResponse.ok) {
        const error = await templateResponse.json();
        setMessage({type: 'error', text: `Template creation failed: ${error.detail}`});
        return;
      }

      const templateResult = await templateResponse.json();
      
      // Start execution with sample data
      const executionResponse = await fetch('/api/workflows/executions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: templateResult.id,
          client_id: 'test_client',
          initial_data: {
            document_content: 'Sample application architecture for testing workflow execution.',
            components: ['Web Frontend', 'API Gateway', 'Database']
          }
        }),
      });

      if (executionResponse.ok) {
        const executionResult = await executionResponse.json();
        setMessage({
          type: 'success', 
          text: `Workflow test started! Execution ID: ${executionResult.execution_id.substring(0, 8)}...`
        });
      } else {
        const error = await executionResponse.json();
        setMessage({type: 'error', text: `Execution failed: ${error.detail}`});
      }
    } catch (error) {
      console.error('Test workflow error:', error);
      setMessage({type: 'error', text: 'Network error testing workflow'});
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Workflow Builder</h1>
          <p className="text-muted-foreground mt-1">
            Create modular threat modeling workflows with agent-based execution
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={testWorkflow} disabled={loading} variant="outline">
            <Play className="mr-2 h-4 w-4" />
            Test Workflow
          </Button>
          <Button onClick={createTemplate} disabled={loading}>
            {loading ? 'Creating...' : 'Create Template'}
          </Button>
        </div>
      </div>

      {message && (
        <div className={`p-4 rounded-lg ${
          message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 
          'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message.text}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Template Configuration */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Template Configuration</CardTitle>
              <CardDescription>Define the workflow name and description</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="template-name">Template Name</Label>
                <Input
                  id="template-name"
                  value={template.name}
                  onChange={(e) => setTemplate(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Complete Threat Analysis"
                />
              </div>
              <div>
                <Label htmlFor="template-description">Description</Label>
                <Textarea
                  id="template-description"
                  value={template.description}
                  onChange={(e) => setTemplate(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe the purpose and scope of this workflow..."
                />
              </div>
            </CardContent>
          </Card>

          {/* Workflow Steps */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Workflow Steps</CardTitle>
                  <CardDescription>Configure the sequence of agent executions</CardDescription>
                </div>
                <Button onClick={addStep} variant="outline" size="sm">
                  <Plus className="mr-2 h-4 w-4" />
                  Add Step
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {template.steps.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No steps configured. Click "Add Step" to begin building your workflow.
                </div>
              ) : (
                <div className="space-y-4">
                  {template.steps.map((step, index) => (
                    <div key={step.id} className="border rounded-lg p-4 space-y-4">
                      <div className="flex justify-between items-start">
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline">Step {index + 1}</Badge>
                          <div className="flex space-x-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => moveStep(index, 'up')}
                              disabled={index === 0}
                            >
                              <MoveUp className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => moveStep(index, 'down')}
                              disabled={index === template.steps.length - 1}
                            >
                              <MoveDown className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => removeStep(index)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>

                      <div className="grid gap-4 md:grid-cols-2">
                        <div>
                          <Label>Step Name</Label>
                          <Input
                            value={step.name}
                            onChange={(e) => updateStep(index, 'name', e.target.value)}
                            placeholder="e.g., Document Analysis"
                          />
                        </div>
                        <div>
                          <Label>Agent</Label>
                          <Select
                            value={step.agent_type}
                            onValueChange={(value) => updateStep(index, 'agent_type', value)}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select agent" />
                            </SelectTrigger>
                            <SelectContent>
                              {agents.map((agent) => (
                                <SelectItem key={agent.name} value={agent.name}>
                                  <div className="flex items-center justify-between w-full">
                                    <span>{agent.name}</span>
                                    <Badge variant="secondary" className="ml-2">
                                      {agent.category}
                                    </Badge>
                                  </div>
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      <div>
                        <Label>Description</Label>
                        <Textarea
                          value={step.description}
                          onChange={(e) => updateStep(index, 'description', e.target.value)}
                          placeholder="Describe what this step accomplishes..."
                        />
                      </div>

                      <div className="grid gap-4 md:grid-cols-3">
                        <div>
                          <Label>Confidence Threshold</Label>
                          <Input
                            type="number"
                            min="0"
                            max="1"
                            step="0.05"
                            value={step.confidence_threshold}
                            onChange={(e) => updateStep(index, 'confidence_threshold', parseFloat(e.target.value))}
                          />
                        </div>
                        <div className="flex items-center space-x-2 pt-6">
                          <Switch
                            checked={step.automation_enabled}
                            onCheckedChange={(checked) => updateStep(index, 'automation_enabled', checked)}
                          />
                          <Label>Enable Automation</Label>
                        </div>
                        <div className="flex items-center space-x-2 pt-6">
                          <Switch
                            checked={step.review_required}
                            onCheckedChange={(checked) => updateStep(index, 'review_required', checked)}
                          />
                          <Label>Require Review</Label>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Automation Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="mr-2 h-4 w-4" />
                Automation Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch
                  checked={template.automation_settings.enabled}
                  onCheckedChange={(checked) =>
                    setTemplate(prev => ({
                      ...prev,
                      automation_settings: { ...prev.automation_settings, enabled: checked }
                    }))
                  }
                />
                <Label>Enable Global Automation</Label>
              </div>

              <div>
                <Label>Global Confidence Threshold</Label>
                <Input
                  type="number"
                  min="0"
                  max="1"
                  step="0.05"
                  value={template.automation_settings.confidence_threshold}
                  onChange={(e) =>
                    setTemplate(prev => ({
                      ...prev,
                      automation_settings: {
                        ...prev.automation_settings,
                        confidence_threshold: parseFloat(e.target.value)
                      }
                    }))
                  }
                />
              </div>

              <div>
                <Label>Max Auto-Approvals/Day</Label>
                <Input
                  type="number"
                  min="1"
                  value={template.automation_settings.max_auto_approvals_per_day}
                  onChange={(e) =>
                    setTemplate(prev => ({
                      ...prev,
                      automation_settings: {
                        ...prev.automation_settings,
                        max_auto_approvals_per_day: parseInt(e.target.value)
                      }
                    }))
                  }
                />
              </div>

              <div>
                <Label>Notification Level</Label>
                <Select
                  value={template.automation_settings.notification_level}
                  onValueChange={(value) =>
                    setTemplate(prev => ({
                      ...prev,
                      automation_settings: { ...prev.automation_settings, notification_level: value }
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    <SelectItem value="summary">Summary</SelectItem>
                    <SelectItem value="detailed">Detailed</SelectItem>
                    <SelectItem value="realtime">Real-time</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Available Agents */}
          <Card>
            <CardHeader>
              <CardTitle>Available Agents</CardTitle>
              <CardDescription>{agents.length} agents registered</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {agents.map((agent) => (
                  <div
                    key={agent.name}
                    className="p-2 border rounded text-sm space-y-1 hover:bg-gray-50"
                  >
                    <div className="font-medium flex items-center justify-between">
                      {agent.name}
                      <Badge variant="secondary">{agent.category}</Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {agent.description}
                    </div>
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>~{agent.estimated_tokens} tokens</span>
                      <span>v{agent.version}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}