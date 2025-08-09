'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  PlayCircle, 
  PauseCircle,
  StopCircle,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Activity,
  ChevronRight,
  Download,
  Eye,
  FileJson,
  FileText,
  ArrowLeft,
  Zap,
  GitBranch,
  Package
} from 'lucide-react';

interface WorkflowStep {
  step_id: string;
  agent_type: string;
  status: string;
  position: number;
  retry_count: number;
  execution_time_ms?: number;
}

interface WorkflowRunDetails {
  run_id: string;
  status: string;
  progress: number;
  total_steps: number;
  completed_steps: number;
  started_at?: string;
  completed_at?: string;
  steps: WorkflowStep[];
  artifacts_count: number;
  can_retry: boolean;
  is_terminal: boolean;
}

interface WorkflowArtifact {
  id: string;
  name: string;
  artifact_type: string;
  version: number;
  size_bytes?: number;
  created_at: string;
  content_json?: any;
  content_text?: string;
}

export default function WorkflowExecutionDetail() {
  const params = useParams();
  const router = useRouter();
  const runId = params.runId as string;
  
  const [runDetails, setRunDetails] = useState<WorkflowRunDetails | null>(null);
  const [artifacts, setArtifacts] = useState<WorkflowArtifact[]>([]);
  const [selectedStep, setSelectedStep] = useState<WorkflowStep | null>(null);
  const [loading, setLoading] = useState(true);
  const [artifactJson, setArtifactJson] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  // Fetch run details
  const fetchRunDetails = useCallback(async () => {
    try {
      const response = await fetch(`/api/phase2/workflow/runs/${runId}/status`);
      if (response.ok) {
        const data = await response.json();
        setRunDetails(data);
        
        // Auto-refresh if still running
        if (data.status === 'running' || data.status === 'created') {
          setTimeout(fetchRunDetails, 2000); // Poll every 2 seconds
        }
      } else {
        setError('Failed to fetch workflow details');
      }
    } catch (err) {
      setError('Error connecting to server');
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    fetchRunDetails();
  }, [fetchRunDetails]);

  useEffect(() => {
    const loadArtifacts = async () => {
      try {
        const res = await fetch(`/api/phase2/workflow/runs/${runId}/artifacts?include_content=true`);
        if (!res.ok) return;
        const data = await res.json();
        setArtifacts(data.artifacts || []);
        const primary = (data.artifacts || []).find((a: any) => a.name?.endsWith('_output'));
        if (primary?.content_json?.dfd_components) {
          setArtifactJson(primary.content_json.dfd_components);
        } else if (primary?.content_json) {
          setArtifactJson(primary.content_json);
        }
      } catch {}
    };
    loadArtifacts();
  }, [runId, runDetails?.status]);

  const executeNextStep = async () => {
    try {
      setIsExecuting(true);
      const response = await fetch(`/api/phase2/workflow/runs/${runId}/execute-next`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });

      if (response.ok) {
        await fetchRunDetails();
      } else {
        setError('Failed to execute next step');
      }
    } catch (err) {
      setError('Error executing step');
    } finally {
      setIsExecuting(false);
    }
  };

  const executeAsync = async () => {
    try {
      setIsExecuting(true);
      const response = await fetch(`/api/phase2/workflow/runs/${runId}/execute-async`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        await fetchRunDetails();
      } else {
        setError('Failed to start async execution');
      }
    } catch (err) {
      setError('Error starting async execution');
    } finally {
      setIsExecuting(false);
    }
  };

  const cancelRun = async () => {
    try {
      const response = await fetch(`/api/phase2/workflow/runs/${runId}/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        await fetchRunDetails();
      } else {
        setError('Failed to cancel workflow');
      }
    } catch (err) {
      setError('Error cancelling workflow');
    }
  };

  const getStepStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'running':
        return <Activity className="h-5 w-5 text-blue-500 animate-pulse" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'pending':
        return <Clock className="h-5 w-5 text-gray-400" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStepStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800 animate-pulse';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      </div>
    );
  }

  if (!runDetails) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="text-center py-8">
            <AlertCircle className="h-12 w-12 mx-auto text-red-500" />
            <p className="mt-2 text-red-600">Workflow run not found</p>
            <Button 
              variant="outline" 
              className="mt-4"
              onClick={() => router.push('/workflows/phase3')}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Workflows
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => router.push('/workflows/phase3')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Workflow Execution</h1>
            <p className="text-gray-600 font-mono text-sm">{runDetails.run_id}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {runDetails.status === 'running' && (
            <Button variant="outline" onClick={cancelRun}>
              <StopCircle className="mr-2 h-4 w-4" />
              Cancel
            </Button>
          )}
          {runDetails.status === 'created' && (
            <>
              <Button variant="outline" onClick={executeNextStep} disabled={isExecuting}>
                <ChevronRight className="mr-2 h-4 w-4" />
                Execute Next
              </Button>
              <Button onClick={executeAsync} disabled={isExecuting}>
                <Zap className="mr-2 h-4 w-4" />
                Execute All
              </Button>
            </>
          )}
          {runDetails.can_retry && runDetails.is_terminal && (
            <Button variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry
            </Button>
          )}
          <Button onClick={fetchRunDetails}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Status Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Execution Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div>
              <span className="text-sm text-gray-500">Status</span>
              <div className="flex items-center gap-2 mt-1">
                {getStepStatusIcon(runDetails.status)}
                <Badge className={getStepStatusColor(runDetails.status)}>
                  {runDetails.status}
                </Badge>
              </div>
            </div>
            <div>
              <span className="text-sm text-gray-500">Progress</span>
              <p className="font-medium mt-1">
                {runDetails.completed_steps} / {runDetails.total_steps} steps
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Artifacts</span>
              <p className="font-medium mt-1 flex items-center gap-1">
                <Package className="h-4 w-4" />
                {runDetails.artifacts_count}
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Started</span>
              <p className="font-medium mt-1">
                {runDetails.started_at 
                  ? new Date(runDetails.started_at).toLocaleTimeString()
                  : 'Not started'}
              </p>
            </div>
          </div>
          
          <div>
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Overall Progress</span>
              <span>{Math.round(runDetails.progress)}%</span>
            </div>
            <Progress value={runDetails.progress} className="h-3" />
          </div>
        </CardContent>
      </Card>

      {/* Step Execution Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            Workflow Steps
          </CardTitle>
          <CardDescription>Step-by-step execution timeline</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {runDetails.steps.map((step, index) => (
              <div 
                key={step.step_id}
                className={`relative flex items-center gap-4 p-4 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
                  selectedStep?.step_id === step.step_id ? 'border-blue-500 bg-blue-50' : ''
                }`}
                onClick={() => setSelectedStep(step)}
              >
                {/* Connection Line */}
                {index < runDetails.steps.length - 1 && (
                  <div className="absolute left-7 top-12 w-0.5 h-12 bg-gray-300" />
                )}
                
                {/* Step Status Icon */}
                <div className="flex-shrink-0">
                  {getStepStatusIcon(step.status)}
                </div>
                
                {/* Step Info */}
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">{step.step_id}</h4>
                      <p className="text-sm text-gray-600">
                        Agent: {step.agent_type}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={getStepStatusColor(step.status)}>
                        {step.status}
                      </Badge>
                      {step.retry_count > 0 && (
                        <Badge variant="outline">
                          Retry {step.retry_count}
                        </Badge>
                      )}
                    </div>
                  </div>
                  
                  {step.execution_time_ms && (
                    <div className="mt-2 text-xs text-gray-500">
                      Execution time: {step.execution_time_ms}ms
                    </div>
                  )}
                </div>
                
                {/* Action Buttons */}
                <div className="flex-shrink-0 flex gap-2">
                  <Button size="sm" variant="outline">
                    <Eye className="h-4 w-4" />
                  </Button>
                  {step.status === 'completed' && (
                    <Button size="sm" variant="outline">
                      <Download className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Workflow Results */}
      {(runDetails.status === 'completed' || artifacts.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileJson className="h-5 w-5" />
              Workflow Results
            </CardTitle>
            <CardDescription>
              Output artifacts and results from workflow execution
            </CardDescription>
          </CardHeader>
          <CardContent>
            {artifacts.length > 0 ? (
              <div className="space-y-4">
                {artifacts.map((artifact: any, index: number) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        <span className="font-medium">{artifact.name}</span>
                        <Badge variant="outline">{artifact.artifact_type}</Badge>
                      </div>
                      <div className="text-sm text-gray-500">
                        v{artifact.version} • {artifact.size_bytes ? `${Math.round(artifact.size_bytes / 1024)}KB` : 'N/A'}
                      </div>
                    </div>
                    {artifact.content_json && (
                      <div className="mt-3">
                        <div className="text-sm font-medium text-gray-700 mb-2">Content:</div>
                        <pre className="text-xs bg-gray-50 text-gray-900 p-3 rounded overflow-auto max-h-60 border">
                          {JSON.stringify(artifact.content_json, null, 2)}
                        </pre>
                      </div>
                    )}
                    {artifact.content_text && (
                      <div className="mt-3">
                        <div className="text-sm font-medium text-gray-700 mb-2">Content:</div>
                        <div className="text-sm bg-gray-50 text-gray-900 p-3 rounded border max-h-60 overflow-auto">
                          {artifact.content_text}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Package className="h-12 w-12 mx-auto text-gray-300" />
                <p className="text-gray-500 mt-2">No results available yet</p>
                <p className="text-sm text-gray-400 mt-1">
                  Results will appear here when the workflow completes
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Selected Step Details */}
      {selectedStep && (
        <Card>
          <CardHeader>
            <CardTitle>Step Details: {selectedStep.step_id}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-500">Agent Type</span>
                <p className="font-medium">{selectedStep.agent_type}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Status</span>
                <Badge className={getStepStatusColor(selectedStep.status)}>
                  {selectedStep.status}
                </Badge>
              </div>
              <div>
                <span className="text-sm text-gray-500">Position</span>
                <p className="font-medium">{selectedStep.position + 1} of {runDetails.total_steps}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Retries</span>
                <p className="font-medium">{selectedStep.retry_count}</p>
              </div>
              {selectedStep.execution_time_ms && (
                <div>
                  <span className="text-sm text-gray-500">Execution Time</span>
                  <p className="font-medium">{selectedStep.execution_time_ms}ms</p>
                </div>
              )}
            </div>
            
            <div className="mt-4 pt-4 border-t">
              <h4 className="font-medium mb-2">Step Output</h4>
              {artifactJson ? (
                <pre className="text-xs bg-gray-50 text-gray-900 p-3 rounded overflow-auto max-h-80">{JSON.stringify(artifactJson, null, 2)}</pre>
              ) : (
                <div className="text-sm text-gray-600">No output JSON available for this step</div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}