import React, { useState } from 'react';
import { ArrowLeft, Play, Clock, CheckCircle, XCircle, AlertCircle, Eye, Download } from 'lucide-react';
import { WorkflowExecution, WorkflowExecutionStep } from '../types';

const mockExecutions: WorkflowExecution[] = [
  {
    id: '1',
    workflowId: '1',
    workflowName: 'Threat Modeling Pipeline',
    status: 'completed',
    startedAt: '2024-01-22T14:30:00Z',
    completedAt: '2024-01-22T15:45:00Z',
    totalSteps: 7,
    completedSteps: 7,
    steps: [
      {
        id: 'e1-s1',
        stepId: 's1',
        name: 'Document Upload',
        status: 'completed',
        startedAt: '2024-01-22T14:30:00Z',
        completedAt: '2024-01-22T14:31:00Z',
        input: { documents: ['system_architecture.pdf', 'requirements.docx'] },
        output: { processedDocuments: 2, totalPages: 45 }
      },
      {
        id: 'e1-s2',
        stepId: 's2',
        name: 'DFD Generation',
        status: 'completed',
        startedAt: '2024-01-22T14:31:00Z',
        completedAt: '2024-01-22T14:38:00Z',
        agentId: '1',
        input: { documents: ['system_architecture.pdf', 'requirements.docx'] },
        output: {
          dfd: {
            processes: [
              { id: 'P1', name: 'User Authentication', type: 'process' },
              { id: 'P2', name: 'Data Processing', type: 'process' }
            ],
            dataStores: [
              { id: 'DS1', name: 'User Database', type: 'datastore' }
            ],
            externalEntities: [
              { id: 'E1', name: 'End User', type: 'external' }
            ],
            dataFlows: [
              { from: 'E1', to: 'P1', data: 'Login Credentials' }
            ]
          }
        },
        tokenUsage: {
          promptTokens: 1250,
          completionTokens: 890,
          totalTokens: 2140,
          cost: 0.0428
        },
        confidence: 0.92
      },
      {
        id: 'e1-s3',
        stepId: 's3',
        name: 'DFD Quality Check',
        status: 'completed',
        startedAt: '2024-01-22T14:38:00Z',
        completedAt: '2024-01-22T14:42:00Z',
        agentId: '2',
        input: { dfd: '...', originalDocuments: '...' },
        output: { validatedDfd: '...', qualityScore: 0.92, improvements: 3 },
        tokenUsage: {
          promptTokens: 980,
          completionTokens: 450,
          totalTokens: 1430,
          cost: 0.0286
        },
        confidence: 0.88
      }
    ]
  },
  {
    id: '2',
    workflowId: '2',
    workflowName: 'Content Creation Pipeline',
    status: 'failed',
    startedAt: '2024-01-22T10:15:00Z',
    totalSteps: 4,
    completedSteps: 2,
    steps: [
      {
        id: 'e2-s1',
        stepId: 's1',
        name: 'Topic Input',
        status: 'completed',
        startedAt: '2024-01-22T10:15:00Z',
        completedAt: '2024-01-22T10:15:30Z',
        input: { topic: 'AI in Healthcare' },
        output: { processedTopic: 'AI in Healthcare', keywords: ['AI', 'Healthcare', 'Machine Learning'] }
      },
      {
        id: 'e2-s2',
        stepId: 's2',
        name: 'Research Phase',
        status: 'failed',
        startedAt: '2024-01-22T10:15:30Z',
        agentId: '7',
        input: { topic: 'AI in Healthcare' },
        error: 'API rate limit exceeded'
      }
    ]
  }
];

interface ExecutionHistoryProps {
  onAgentClick?: (agentId: string) => void;
}

export function ExecutionHistory({ onAgentClick }: ExecutionHistoryProps) {
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null);
  const [selectedStep, setSelectedStep] = useState<WorkflowExecutionStep | null>(null);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed': return <XCircle className="w-5 h-5 text-red-500" />;
      case 'in_progress': return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'running': return <Play className="w-5 h-5 text-blue-500" />;
      case 'paused': return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      default: return <div className="w-5 h-5 rounded-full bg-gray-300" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-700';
      case 'failed': return 'bg-red-100 text-red-700';
      case 'in_progress': return 'bg-blue-100 text-blue-700';
      case 'running': return 'bg-blue-100 text-blue-700';
      case 'paused': return 'bg-yellow-100 text-yellow-700';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  const formatDuration = (start: string, end?: string) => {
    const startTime = new Date(start);
    const endTime = end ? new Date(end) : new Date();
    const duration = Math.round((endTime.getTime() - startTime.getTime()) / 1000 / 60);
    return `${duration}m`;
  };

  if (selectedExecution) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setSelectedExecution(null)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Execution Details</h1>
              <p className="text-gray-600 mt-1">{selectedExecution.workflowName}</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            {getStatusIcon(selectedExecution.status)}
            <span className={`px-3 py-1 rounded-lg text-sm font-medium ${getStatusColor(selectedExecution.status)}`}>
              {selectedExecution.status}
            </span>
          </div>
        </div>

        {/* Execution Info */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-600">Started</h3>
            <p className="text-lg font-semibold text-gray-900 mt-1">
              {new Date(selectedExecution.startedAt).toLocaleString()}
            </p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-600">Duration</h3>
            <p className="text-lg font-semibold text-gray-900 mt-1">
              {formatDuration(selectedExecution.startedAt, selectedExecution.completedAt)}
            </p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-600">Progress</h3>
            <p className="text-lg font-semibold text-gray-900 mt-1">
              {selectedExecution.completedSteps}/{selectedExecution.totalSteps}
            </p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-600">Status</h3>
            <p className="text-lg font-semibold text-gray-900 mt-1 capitalize">
              {selectedExecution.status}
            </p>
          </div>
        </div>

        {/* Steps Timeline */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Execution Steps</h2>
          <div className="space-y-4">
            {selectedExecution.steps.map((step, index) => (
              <div key={step.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(step.status)}
                    <div>
                      <h3 className="font-medium text-gray-900">{step.name}</h3>
                      <p className="text-sm text-gray-600">
                        {step.startedAt && `Started: ${new Date(step.startedAt).toLocaleTimeString()}`}
                        {step.completedAt && ` • Completed: ${new Date(step.completedAt).toLocaleTimeString()}`}
                        {step.startedAt && (step.completedAt || step.status === 'in_progress') && 
                          ` • Duration: ${formatDuration(step.startedAt, step.completedAt)}`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`text-xs px-2 py-1 rounded ${getStatusColor(step.status)}`}>
                      {step.status.replace('_', ' ')}
                    </span>
                    <button
                      onClick={() => setSelectedStep(step)}
                      className="p-1 rounded hover:bg-gray-100 text-gray-600"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {step.error && (
                  <div className="mt-3 p-3 bg-red-50 rounded-lg">
                    <p className="text-sm text-red-700 font-medium">Error:</p>
                    <p className="text-sm text-red-600">{step.error}</p>
                  </div>
                )}

                {/* Token Usage and Confidence */}
                {(step.tokenUsage || step.confidence) && (
                  <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4">
                    {step.tokenUsage && (
                      <div className="p-3 bg-blue-50 rounded-lg">
                        <h4 className="text-sm font-medium text-blue-700 mb-2">Token Usage</h4>
                        <div className="text-xs text-blue-600 space-y-1">
                          <div className="flex justify-between">
                            <span>Prompt:</span>
                            <span>{step.tokenUsage.promptTokens.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Completion:</span>
                            <span>{step.tokenUsage.completionTokens.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between font-medium">
                            <span>Total:</span>
                            <span>{step.tokenUsage.totalTokens.toLocaleString()}</span>
                          </div>
                          {step.tokenUsage.cost && (
                            <div className="flex justify-between font-medium text-blue-700">
                              <span>Cost:</span>
                              <span>${step.tokenUsage.cost.toFixed(4)}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                    {step.confidence && (
                      <div className="p-3 bg-green-50 rounded-lg">
                        <h4 className="text-sm font-medium text-green-700 mb-2">Confidence Score</h4>
                        <div className="flex items-center space-x-2">
                          <div className="flex-1 bg-green-200 rounded-full h-2">
                            <div 
                              className="bg-green-600 h-2 rounded-full" 
                              style={{ width: `${step.confidence * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-medium text-green-700">
                            {(step.confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {(step.input || step.output) && (
                  <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4">
                    {step.input && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Input</h4>
                        <pre className="text-xs bg-gray-50 p-2 rounded border overflow-x-auto">
                          {JSON.stringify(step.input, null, 2)}
                        </pre>
                      </div>
                    )}
                    {step.output && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Output</h4>
                        <pre className="text-xs bg-gray-50 p-2 rounded border overflow-x-auto">
                          {JSON.stringify(step.output, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step Detail Modal */}
        {selectedStep && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
              <div className="flex items-center justify-between p-6 border-b border-gray-200">
                <h2 className="text-xl font-bold text-gray-900">{selectedStep.name} - Details</h2>
                <button
                  onClick={() => setSelectedStep(null)}
                  className="p-2 rounded-lg hover:bg-gray-100"
                >
                  ×
                </button>
              </div>
              <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Input Data</h3>
                    <pre className="text-sm bg-gray-50 p-4 rounded-lg border overflow-x-auto">
                      {selectedStep.input ? JSON.stringify(selectedStep.input, null, 2) : 'No input data'}
                    </pre>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Output Data</h3>
                    <pre className="text-sm bg-gray-50 p-4 rounded-lg border overflow-x-auto">
                      {selectedStep.output ? JSON.stringify(selectedStep.output, null, 2) : 'No output data'}
                    </pre>
                  </div>
                </div>
                {selectedStep.error && (
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold text-red-700 mb-3">Error Details</h3>
                    <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                      <p className="text-red-700">{selectedStep.error}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Workflow Execution History</h1>
          <p className="text-gray-600 mt-2">View detailed execution history and results from your automated AI workflows</p>
        </div>
      </div>

      {/* Executions List */}
      <div className="space-y-4">
        {mockExecutions.map(execution => (
          <div
            key={execution.id}
            onClick={() => setSelectedExecution(execution)}
            className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg hover:border-purple-300 transition-all duration-200 cursor-pointer"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                {getStatusIcon(execution.status)}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{execution.workflowName}</h3>
                  <p className="text-sm text-gray-600">
                    Started: {new Date(execution.startedAt).toLocaleString()}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-sm text-gray-900">
                    {execution.completedSteps}/{execution.totalSteps} steps
                  </p>
                  <p className="text-xs text-gray-500">
                    Duration: {formatDuration(execution.startedAt, execution.completedAt)}
                  </p>
                </div>
                <span className={`px-3 py-1 rounded-lg text-sm font-medium ${getStatusColor(execution.status)}`}>
                  {execution.status}
                </span>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  execution.status === 'completed' ? 'bg-green-500' :
                  execution.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'
                }`}
                style={{ width: `${(execution.completedSteps / execution.totalSteps) * 100}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}