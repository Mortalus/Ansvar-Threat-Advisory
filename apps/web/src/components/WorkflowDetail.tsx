import React, { useState } from 'react';
import { ArrowLeft, Play, Edit, FileText, CheckCircle, AlertCircle, Clock, Settings, Database, XCircle } from 'lucide-react';
import { Workflow, Agent, ContextSource } from '../types';
import { StepDetailModal } from './StepDetailModal';
import { MermaidViewer } from './MermaidViewer';

interface WorkflowDetailProps {
  workflow: Workflow;
  agents: Agent[];
  contextSources: ContextSource[];
  onBack: () => void;
  onRunWorkflow: (workflowId: string) => void;
  onEditAgent: (agent: Agent) => void;
}

export function WorkflowDetail({ workflow, agents, contextSources, onBack, onRunWorkflow, onEditAgent }: WorkflowDetailProps) {
  const [selectedStep, setSelectedStep] = useState<string | null>(null);
  const [stepOutputs, setStepOutputs] = useState<Record<string, any>>({});
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState<string | null>(null);
  const [showStepDetail, setShowStepDetail] = useState(false);
  const [selectedStepForDetail, setSelectedStepForDetail] = useState<any>(null);
  const [showOutputEditor, setShowOutputEditor] = useState<{ step: any, output: any } | null>(null);
  const [showDocumentUpload, setShowDocumentUpload] = useState(false);

  const detectContentType = (content: string) => {
    // Check if content contains Mermaid diagram syntax
    if (typeof content === 'string' && (
      content.includes('graph') || 
      content.includes('flowchart') || 
      content.includes('sequenceDiagram') ||
      content.includes('classDiagram') ||
      content.includes('stateDiagram') ||
      content.includes('journey') ||
      content.includes('gantt')
    )) {
      return 'mermaid';
    }
    
    try {
      JSON.parse(content);
      return 'json';
    } catch {
      if (content.includes('# ') || content.includes('## ') || content.includes('**')) {
        return 'markdown';
      }
      return 'text';
    }
  };

  const getStepAgent = (agentId?: string) => {
    return agents.find(agent => agent.id === agentId);
  };

  const getStepStatus = (stepId: string) => {
    if (currentStep === stepId) return 'in_progress';
    if (stepOutputs[stepId]) return 'completed';
    return 'pending';
  };

  const getStepReviewStatus = (stepId: string) => {
    const output = stepOutputs[stepId];
    return output?.requiresReview === true;
  };

  const getStepIcon = (step: any) => {
    const status = getStepStatus(step.id);
    const needsReview = getStepReviewStatus(step.id);
    
    if (status === 'in_progress') return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
    if (status === 'completed') return <CheckCircle className="w-5 h-5 text-green-500" />;
    if (status === 'failed') return <XCircle className="w-5 h-5 text-red-500" />;
    if (needsReview) return <AlertCircle className="w-5 h-5 text-orange-500" />;
    return <div className="w-5 h-5 rounded-full bg-gray-300" />;
  };

  const handleRunWorkflow = () => {
    setIsRunning(true);
    onRunWorkflow(workflow.id);
    // Simulate workflow execution
    simulateWorkflowExecution();
  };

  const simulateWorkflowExecution = () => {
    const steps = workflow.steps;
    let currentStepIndex = 0;

    const executeNextStep = () => {
      if (currentStepIndex >= steps.length) {
        setIsRunning(false);
        setCurrentStep(null);
        return;
      }

      const step = steps[currentStepIndex];
      setCurrentStep(step.id);

      // Simulate step execution time
      setTimeout(() => {
        if (step.type === 'agent') {
          // Generate appropriate output based on agent
          let content = `Sample output from ${step.name}`;
          
          // Special case for Mermaid Diagram Generator
          if (step.agentId === '10') {
            content = `graph TD
    A[User] --> B[Authentication Service]
    B --> C[User Database]
    B --> D[Activity Logs]
    C --> E[Profile Data]
    D --> F[Security Monitoring]
    E --> G[Dashboard]
    F --> H[Alert System]`;
          } else if (step.agentId === '5') {
            // Attack Path Generator - basic attack path example
            content = `graph TD
    A[Attacker] --> B[Website]
    B --> C[SQL Injection]
    C --> D[Database]
    D --> E[Sensitive Data]
    
    style A fill:#ff6b6b
    style B fill:#ffd93d
    style C fill:#ff9f43
    style D fill:#ee5a24
    style E fill:#c44569`;
          }
          
          setStepOutputs(prev => ({
            ...prev,
            [step.id]: {
              type: step.agentId === '10' ? 'mermaid' : 'json',
              content: content,
              timestamp: new Date().toISOString(),
              requiresReview: true
            }
          }));
          // Don't continue automatically - wait for user approval
        } else {
          // For non-agent steps, continue automatically
          currentStepIndex++;
          executeNextStep();
        }
      }, 2000);
    };

    executeNextStep();
  };

  const approveStep = (stepId: string) => {
    setStepOutputs(prev => ({
      ...prev,
      [stepId]: {
        ...prev[stepId],
        requiresReview: false,
        approved: true
      }
    }));
    
    // Continue workflow execution after approval
    const stepIndex = workflow.steps.findIndex(s => s.id === stepId);
    const nextStepIndex = stepIndex + 1;
    
    if (nextStepIndex < workflow.steps.length) {
      // Continue with next step
      setTimeout(() => {
        const nextStep = workflow.steps[nextStepIndex];
        setCurrentStep(nextStep.id);
        
        setTimeout(() => {
          if (nextStep.type === 'agent') {
            // Generate appropriate output based on agent
            let content = `Sample output from ${nextStep.name}`;
            
            // Special case for Mermaid Diagram Generator
            if (nextStep.agentId === '10') {
              content = `graph TD
    A[User] --> B[Authentication Service]
    B --> C[User Database]
    B --> D[Activity Logs]
    C --> E[Profile Data]
    D --> F[Security Monitoring]
    E --> G[Dashboard]
    F --> H[Alert System]`;
            } else if (nextStep.agentId === '5') {
              // Attack Path Generator - basic attack path example
              content = `graph TD
    A[Attacker] --> B[Website]
    B --> C[SQL Injection]
    C --> D[Database]
    D --> E[Sensitive Data]
    
    style A fill:#ff6b6b
    style B fill:#ffd93d
    style C fill:#ff9f43
    style D fill:#ee5a24
    style E fill:#c44569`;
            }
            
            setStepOutputs(prev => ({
              ...prev,
              [nextStep.id]: {
                type: nextStep.agentId === '10' ? 'mermaid' : 'json',
                content: content,
                timestamp: new Date().toISOString(),
                requiresReview: true
              }
            }));
          } else if (nextStep.type === 'output') {
            // For final output step, compile all previous outputs
            const allOutputs = Object.entries(stepOutputs)
              .filter(([stepId, output]) => output?.approved)
              .map(([stepId, output]) => {
                const step = workflow.steps.find(s => s.id === stepId);
                return `=== ${step?.name || 'Unknown Step'} ===\n${
                  typeof output.content === 'string' ? output.content : JSON.stringify(output.content, null, 2)
                }`;
              })
              .join('\n\n');

            const finalContent = `THREAT MODEL REPORT
Generated: ${new Date().toLocaleString()}

${allOutputs}

=== Generated Files ===
report.pdf - Complete threat modeling report with diagrams and analysis
report.pptx - Executive presentation with key findings and recommendations`;

            setStepOutputs(prev => ({
              ...prev,
              [nextStep.id]: {
                type: 'text',
                content: finalContent,
                timestamp: new Date().toISOString(),
                requiresReview: false,
                approved: true,
                files: ['report.pdf', 'report.pptx']
              }
            }));
          } else {
            // For other non-agent steps, mark as completed and continue
            setStepOutputs(prev => ({
              ...prev,
              [nextStep.id]: {
                type: 'text',
                content: `${nextStep.name} completed`,
                timestamp: new Date().toISOString(),
                requiresReview: false,
                approved: true
              }
            }));
          }
        }, 2000);
      }, 500);
    } else {
      // Workflow completed
      setIsRunning(false);
      setCurrentStep(null);
    }
  };

  const handleStepClick = (step: any) => {
    // For input steps, show document upload instead of step details
    if (step.type === 'input') {
      setShowDocumentUpload(true);
    } else {
      setSelectedStepForDetail(step);
      setShowStepDetail(true);
    }
  };

  const handleUpdateStep = (updatedStep: any) => {
    // Update the step in the workflow
    console.log('Updating step:', updatedStep);
  };

  const handleDocumentUpload = (files: File[], urls: string[]) => {
    // Handle document upload for input step
    console.log('Uploaded files:', files);
    console.log('URLs:', urls);
    
    // Mark input step as completed
    const inputStep = workflow.steps.find(s => s.type === 'input');
    if (inputStep) {
      setStepOutputs(prev => ({
        ...prev,
        [inputStep.id]: {
          type: 'text',
          content: [
            ...files.map(f => f.name),
            ...urls.filter(u => u.trim() !== '')
          ].join('\n'),
          timestamp: new Date().toISOString(),
          requiresReview: false,
          approved: true
        }
      }));
    }
    setShowDocumentUpload(false);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={onBack}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{workflow.name}</h1>
            <p className="text-gray-600 mt-1">{workflow.description}</p>
          </div>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleRunWorkflow}
            disabled={isRunning}
            className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-3 rounded-lg hover:shadow-lg transition-all duration-200 flex items-center space-x-2 disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            <span>{isRunning ? 'Running...' : 'Run Workflow'}</span>
          </button>
          <button 
            onClick={() => {
              // Navigate to workflow builder with this workflow's context
              console.log('Edit workflow:', workflow.id);
              // This would typically navigate to workflow builder with pre-loaded data
            }}
            className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg hover:shadow-lg transition-all duration-200 flex items-center space-x-2"
          >
            <Edit className="w-4 h-4" />
            <span>Edit Workflow</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Workflow Steps</h2>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span>
                  {Object.keys(stepOutputs).filter(id => stepOutputs[id]?.approved).length} of {workflow.steps.length} completed
                </span>
                <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full transition-all duration-1000 ease-out"
                    style={{ 
                      width: `${Math.max(0, (Object.keys(stepOutputs).filter(id => stepOutputs[id]?.approved).length / workflow.steps.length) * 100)}%` 
                    }}
                  ></div>
                </div>
                <span className="font-medium">
                  {Math.round((Object.keys(stepOutputs).filter(id => stepOutputs[id]?.approved).length / workflow.steps.length) * 100)}%
                </span>
              </div>
            </div>
            
            <div className="space-y-4">
              {workflow.steps.map((step, index) => {
                const agent = getStepAgent(step.agentId);
                const status = getStepStatus(step.id);
                const output = stepOutputs[step.id];
                const needsReview = getStepReviewStatus(step.id);
                const isInputStep = step.type === 'input';
                
                return (
                  <div key={step.id} className={`border-2 rounded-lg p-4 transition-all duration-300 hover:shadow-lg ${
                    status === 'completed' ? 'border-green-300 bg-green-50/30' :
                   status === 'in_progress' ? 'border-orange-300 bg-orange-50/30 shadow-md' :
                    needsReview ? 'border-orange-300 bg-orange-50/30 shadow-md' :
                   'border-blue-200 bg-blue-50/20 hover:border-purple-300'
                  }`}>
                    {/* Interactive Progress Indicator */}
                    <div className="flex items-center mb-3">
                      <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center transition-all duration-300 ${
                        status === 'completed' ? 'bg-green-500 border-green-400 shadow-lg' :
                       status === 'in_progress' ? 'bg-orange-500 border-orange-400 shadow-lg animate-pulse' :
                        needsReview ? 'bg-orange-500 border-orange-400 shadow-lg' :
                       'bg-blue-300 border-blue-200'
                      }`}>
                        {status === 'completed' ? (
                          <CheckCircle className="w-4 h-4 text-white" />
                        ) : status === 'in_progress' ? (
                         <Clock className="w-4 h-4 text-white animate-spin" />
                        ) : needsReview ? (
                          <AlertCircle className="w-4 h-4 text-white" />
                        ) : (
                          <span className="text-white font-bold text-xs">{index + 1}</span>
                        )}
                      </div>
                      
                      {/* Connecting Line */}
                      {index < workflow.steps.length - 1 && (
                        <div className={`flex-1 h-0.5 mx-3 transition-all duration-500 ${
                          status === 'completed' ? 'bg-green-400' :
                         status === 'in_progress' ? 'bg-orange-400' :
                         'bg-blue-200'
                        }`}>
                         {status === 'in_progress' && (
                           <div className="h-full bg-gradient-to-r from-orange-400 to-transparent animate-pulse"></div>
                          )}
                        </div>
                      )}
                      
                      {/* Floating Status Indicator */}
                      {(status === 'in_progress' || needsReview) && (
                        <div className="relative">
                          <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full ${
                            needsReview ? 'bg-orange-500' : 'bg-blue-500'
                          } animate-ping`}></div>
                          <div className={`w-3 h-3 rounded-full ${
                            needsReview ? 'bg-orange-500' : 'bg-blue-500'
                          }`}></div>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3 flex-1">
                        <div>
                          <h3 className={`font-medium transition-colors ${
                            status === 'completed' ? 'text-green-800' :
                           status === 'in_progress' ? 'text-orange-800' :
                            needsReview ? 'text-orange-800' :
                           'text-blue-800'
                          }`}>{step.name}</h3>
                          <p className="text-sm text-gray-600">{step.description}</p>
                          {agent && (
                            <p className="text-xs text-purple-600 mt-1">
                              Agent: {agent.name} ({agent.provider} - {agent.settings.model})
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {isInputStep && status === 'pending' && (
                          <button
                            onClick={() => setShowDocumentUpload(true)}
                            className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-colors"
                          >
                            Upload Documents
                          </button>
                        )}
                        {isInputStep && status === 'completed' && (
                          <button
                            onClick={() => setShowDocumentUpload(true)}
                            className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700 transition-colors"
                          >
                            Add More Documents
                          </button>
                        )}
                        <button
                          onClick={() => handleStepClick(step)}
                          className="p-1 rounded hover:bg-purple-100 text-purple-600"
                          title="View Step Details"
                        >
                          <Settings className="w-4 h-4" />
                        </button>
                        <span className={`text-xs px-2 py-1 rounded ${
                          status === 'completed' ? 'bg-green-100 text-green-700' :
                         status === 'in_progress' ? 'bg-orange-100 text-orange-700' :
                          status === 'failed' ? 'bg-red-100 text-red-700' :
                          needsReview ? 'bg-orange-100 text-orange-700' :
                         'bg-blue-100 text-blue-700'
                        }`}>
                          {needsReview ? 'review' : status.replace('_', ' ')}
                        </span>
                        {step.contextSources && step.contextSources.length > 0 && (
                          <Database className="w-4 h-4 text-blue-500" title="Has Context Sources" />
                        )}
                      </div>
                    </div>

                    {/* Step Output */}
                    {output && (
                      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="text-sm font-medium text-gray-900">Output</h4>
                          <span className="text-xs text-gray-500">
                            {new Date(output.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        
                        {/* Generated Files Display */}
                        {output.files && output.files.length > 0 && (
                          <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                            <h5 className="text-sm font-medium text-blue-900 mb-2">Generated Files</h5>
                            <div className="space-y-1">
                              {output.files.map((file: string, index: number) => (
                                <div key={index} className="flex items-center space-x-2 text-sm">
                                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                                  <span className="text-blue-800 font-medium">{file}</span>
                                  <button className="text-blue-600 hover:text-blue-700 text-xs underline">
                                    Download
                                  </button>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {step.type === 'agent' && output.requiresReview ? (
                          <div className="space-y-3">
                          
                          {/* Mermaid Diagram Preview */}
                          {typeof output.content === 'string' && detectContentType(output.content) === 'mermaid' && (
                            <div className="mt-3">
                              <h5 className="text-sm font-medium text-gray-900 mb-2">Diagram Preview</h5>
                              <div className="border border-gray-200 rounded-lg p-4 bg-white">
                                <MermaidViewer chart={output.content} className="max-w-full overflow-x-auto" />
                              </div>
                            </div>
                          )}
                          
                            <p className="text-sm text-gray-600">Review the output before proceeding to the next step.</p>
                            <button
                              onClick={() => setShowOutputEditor({ step, output })}
                              className="w-full p-3 border border-gray-300 rounded-lg text-left hover:bg-gray-50 transition-colors"
                            >
                              <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-700">Click to edit output</span>
                                <Edit className="w-4 h-4 text-gray-400" />
                              </div>
                              <div className="text-xs text-gray-500 mt-1 font-mono truncate">
                                {typeof output.content === 'string' ? output.content.substring(0, 100) + '...' : JSON.stringify(output.content).substring(0, 100) + '...'}
                              </div>
                            </button>
                            <div className="flex space-x-2">
                              <button
                                onClick={() => approveStep(step.id)}
                                className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-700 transition-colors"
                              >
                                Save & Continue
                              </button>
                              <button 
                                onClick={() => {
                                  const agent = getStepAgent(step.agentId);
                                  if (agent) {
                                    onEditAgent(agent);
                                  }
                                }}
                                className="bg-purple-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-purple-700 transition-colors"
                              >
                                Edit Agent Settings
                              </button>
                            </div>
                          </div>
                        ) : output && (
                          <div className="space-y-2">
                            {/* Mermaid Diagram Display */}
                            {step.type === 'agent' && typeof output.content === 'string' && detectContentType(output.content) === 'mermaid' ? (
                              <div>
                                <h5 className="text-sm font-medium text-gray-900 mb-2">Generated Diagram</h5>
                                <div className="border border-gray-200 rounded-lg p-4 bg-white">
                                  <MermaidViewer chart={output.content} className="max-w-full overflow-x-auto" />
                                </div>
                                <details className="mt-2">
                                  <summary className="text-sm text-gray-600 cursor-pointer hover:text-gray-800">View Mermaid Code</summary>
                                  <pre className="text-xs text-gray-700 whitespace-pre-wrap bg-gray-50 p-2 rounded border mt-2 font-mono">
                                    {output.content}
                                  </pre>
                                </details>
                              </div>
                            ) : (
                            <pre className="text-sm text-gray-700 whitespace-pre-wrap bg-white p-2 rounded border">
                              {typeof output.content === 'string' ? output.content : JSON.stringify(output.content, null, 2)}
                            </pre>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Workflow Info */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Workflow Information</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Steps</span>
                <span className="text-sm text-gray-900">{workflow.steps.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Agent Steps</span>
                <span className="text-sm text-gray-900">
                  {workflow.steps.filter(s => s.type === 'agent').length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Review Steps</span>
                <span className="text-sm text-gray-900">
                  {workflow.steps.filter(s => s.type === 'condition').length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Created</span>
                <span className="text-sm text-gray-900">
                  {new Date(workflow.createdAt).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Status</span>
                <span className={`text-sm ${isRunning ? 'text-blue-600' : 'text-green-600'}`}>
                  {isRunning ? 'Running' : 'Ready'}
                </span>
              </div>
            </div>
          </div>

          {/* Agents Used */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Agents Used</h3>
            <div className="space-y-3">
              {workflow.steps
                .filter(step => step.type === 'agent')
                .map(step => {
                  const agent = getStepAgent(step.agentId);
                  if (!agent) return null;
                  
                  return (
                    <div key={step.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                      <button
                        onClick={() => onEditAgent(agent)}
                        className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center hover:shadow-lg transition-all duration-200"
                      >
                        <span className="text-xs text-white font-medium">
                          {agent.name.charAt(0)}
                        </span>
                      </button>
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-gray-900">{agent.name}</h4>
                        <p className="text-xs text-gray-600">
                          {agent.provider} - {agent.settings.model}
                        </p>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Execution History */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Executions</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">Successful Run</p>
                  <p className="text-xs text-gray-600">2 hours ago</p>
                </div>
                <CheckCircle className="w-5 h-5 text-green-500" />
              </div>
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">Successful Run</p>
                  <p className="text-xs text-gray-600">1 day ago</p>
                </div>
                <CheckCircle className="w-5 h-5 text-green-500" />
              </div>
              <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">Manual Review</p>
                  <p className="text-xs text-gray-600">3 days ago</p>
                </div>
                <AlertCircle className="w-5 h-5 text-yellow-500" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Step Detail Modal */}
      {selectedStepForDetail && (
        <StepDetailModal
          step={selectedStepForDetail}
          agent={getStepAgent(selectedStepForDetail.agentId)}
          contextSources={contextSources}
          isOpen={showStepDetail}
          onClose={() => {
            setShowStepDetail(false);
            setSelectedStepForDetail(null);
          }}
          onUpdateStep={handleUpdateStep}
          onEditAgent={onEditAgent}
        />
      )}

      {/* Output Editor Modal */}
      {showOutputEditor && (
        <OutputEditorModal
          step={showOutputEditor.step}
          output={showOutputEditor.output}
          onSave={(updatedOutput) => {
            // Update the output and continue workflow
            setStepOutputs(prev => ({
              ...prev,
              [showOutputEditor.step.id]: {
                ...showOutputEditor.output,
                content: updatedOutput,
                requiresReview: false,
                approved: true
              }
            }));
            setShowOutputEditor(null);
            approveStep(showOutputEditor.step.id);
          }}
          onClose={() => setShowOutputEditor(null)}
        />
      )}

      {/* Document Upload Modal */}
      {showDocumentUpload && (
        <DocumentUploadModal
          isOpen={showDocumentUpload}
          onClose={() => setShowDocumentUpload(false)}
          onUpload={handleDocumentUpload}
        />
      )}
    </div>
  );
}

interface OutputEditorModalProps {
  step: any;
  output: any;
  onSave: (content: any) => void;
  onClose: () => void;
}

function OutputEditorModal({ step, output, onSave, onClose }: OutputEditorModalProps) {
  const [content, setContent] = useState(
    typeof output.content === 'string' ? output.content : JSON.stringify(output.content, null, 2)
  );
  const [editorType, setEditorType] = useState<'json' | 'text' | 'markdown' | 'mermaid'>('json');
  const [error, setError] = useState<string | null>(null);

  const detectContentType = (content: string) => {
    // Check for Mermaid diagram syntax
    if (content.includes('graph') || content.includes('flowchart') || content.includes('sequenceDiagram') ||
        content.includes('classDiagram') || content.includes('stateDiagram') || content.includes('journey') ||
        content.includes('gantt')) {
      return 'mermaid';
    }
    
    try {
      JSON.parse(content);
      return 'json';
    } catch {
      if (content.includes('# ') || content.includes('## ') || content.includes('**')) {
        return 'markdown';
      }
      return 'text';
    }
  };

  React.useEffect(() => {
    setEditorType(detectContentType(content));
  }, []);

  const handleSave = () => {
    setError(null);
    
    if (editorType === 'json') {
      try {
        const parsed = JSON.parse(content);
        onSave(parsed);
      } catch (e) {
        setError('Invalid JSON format');
        return;
      }
    } else {
      onSave(content);
    }
  };

  const formatJSON = () => {
    if (editorType === 'json') {
      try {
        const parsed = JSON.parse(content);
        setContent(JSON.stringify(parsed, null, 2));
        setError(null);
      } catch (e) {
        setError('Invalid JSON format');
      }
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Edit Output - {step.name}</h2>
            <p className="text-sm text-gray-600 mt-1">Review and modify the agent output</p>
          </div>
          <div className="flex items-center space-x-3">
            <select
              value={editorType}
              onChange={(e) => setEditorType(e.target.value as any)}
              className="px-3 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="json">JSON</option>
              <option value="text">Text</option>
              <option value="markdown">Markdown</option>
              <option value="mermaid">Mermaid Diagram</option>
            </select>
            {editorType === 'json' && (
              <button
                onClick={formatJSON}
                className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200"
              >
                Format
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-100"
            >
              ×
            </button>
          </div>
        </div>
        
        <div className="flex-1 p-6 overflow-y-auto">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Content ({editorType.toUpperCase()})
              </label>
              <div className="border border-gray-300 rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-3 py-2 border-b border-gray-300 flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">{editorType.toUpperCase()} Editor</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">{content.length} characters</span>
                    {editorType === 'json' && (
                      <button
                        onClick={formatJSON}
                        className="text-xs text-blue-600 hover:text-blue-700"
                      >
                        Format JSON
                      </button>
                    )}
                  </div>
                </div>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  rows={16}
                  className={`w-full px-4 py-3 border-0 focus:ring-0 focus:outline-none resize-none ${
                    (editorType === 'json' || editorType === 'mermaid') ? 'font-mono text-sm' : ''
                  }`}
                  placeholder={
                    editorType === 'json' ? 'Enter valid JSON...' :
                    editorType === 'mermaid' ? 'Enter Mermaid diagram code...' :
                    editorType === 'markdown' ? 'Enter markdown content...' :
                    'Enter text content...'
                  }
                />
              </div>
            </div>
            
            {/* Mermaid Diagram Preview */}
            {editorType === 'mermaid' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Diagram Preview</label>
                <div className="border border-gray-300 rounded-lg bg-gray-50 overflow-hidden">
                  <div className="p-4 max-h-64 overflow-y-auto">
                    <MermaidViewer chart={content} className="max-w-full" />
                  </div>
                </div>
              </div>
            )}
            
            {editorType === 'markdown' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Preview</label>
                <div className="p-4 border border-gray-300 rounded-lg bg-gray-50 prose prose-sm max-w-none max-h-64 overflow-y-auto">
                  {content.split('\n').map((line, i) => {
                    if (line.startsWith('# ')) return <h1 key={i} className="text-xl font-bold">{line.substring(2)}</h1>;
                    if (line.startsWith('## ')) return <h2 key={i} className="text-lg font-semibold">{line.substring(3)}</h2>;
                    if (line.includes('**')) {
                      const parts = line.split('**');
                      return <p key={i}>{parts.map((part, j) => j % 2 === 1 ? <strong key={j}>{part}</strong> : part)}</p>;
                    }
                    return <p key={i}>{line || <br />}</p>;
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
        
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-2 rounded-lg hover:shadow-lg transition-all duration-200"
          >
            Save & Continue
          </button>
        </div>
      </div>
    </div>
  );
}

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (files: File[], urls: string[]) => void;
}

function DocumentUploadModal({ isOpen, onClose, onUpload }: DocumentUploadModalProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [urls, setUrls] = useState<string[]>(['']);
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };
  
  const handleUrlChange = (index: number, value: string) => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);
  };
  
  const addUrlField = () => {
    setUrls([...urls, '']);
  };
  
  const removeUrlField = (index: number) => {
    setUrls(urls.filter((_, i) => i !== index));
  };
  
  const handleSubmit = () => {
    onUpload(files, urls);
    setFiles([]);
    setUrls(['']);
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Upload Documents</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100"
          >
            ×
          </button>
        </div>
        
        <div className="p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload Files
            </label>
            <input
              type="file"
              multiple
              onChange={handleFileChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
            {files.length > 0 && (
              <div className="mt-2 space-y-1">
                {files.map((file, index) => (
                  <div key={index} className="text-sm text-gray-600">
                    {file.name} ({(file.size / 1024).toFixed(1)} KB)
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              URLs
            </label>
            <div className="space-y-2">
              {urls.map((url, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => handleUrlChange(index, e.target.value)}
                    placeholder="https://example.com/document.pdf"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                  {urls.length > 1 && (
                    <button
                      onClick={() => removeUrlField(index)}
                      className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      Remove
                    </button>
                  )}
                </div>
              ))}
              <button
                onClick={addUrlField}
                className="text-purple-600 hover:text-purple-700 text-sm"
              >
                + Add another URL
              </button>
            </div>
          </div>
        </div>
        
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-2 rounded-lg hover:shadow-lg transition-all duration-200"
          >
            Upload & Continue
          </button>
        </div>
      </div>
    </div>
  );
}