'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import ArtifactViewer from '@/components/workflows/artifact-viewer';
import { useWorkflowRunWebSocket } from '@/hooks/use-workflow-websocket';
import { 
  PlayCircle, 
  CheckCircle2,
  Activity,
  AlertCircle,
  Clock,
  RefreshCw,
  Wifi,
  WifiOff,
  Zap,
  Package,
  GitBranch,
  Monitor,
  ChevronRight,
  ArrowLeft
} from 'lucide-react';

interface DemoWorkflowRun {
  id: string;
  run_id: string;
  status: string;
  progress: number;
  total_steps: number;
  completed_steps: number;
  started_at?: string;
  steps: Array<{
    step_id: string;
    status: string;
    agent_type: string;
    execution_time_ms?: number;
  }>;
}

export default function Phase3Demo() {
  const [run, setRun] = useState<DemoWorkflowRun | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [wsConnected, setWsConnected] = useState(false);

  // WebSocket connection for real-time updates
  const { isConnected } = useWorkflowRunWebSocket(
    run?.run_id || '',
    (event) => {
      const timestamp = new Date().toLocaleTimeString();
      
      switch (event.type) {
        case 'run_status':
          setLogs(prev => [...prev, `[${timestamp}] Run status: ${event.data.status} (${event.data.progress}%)`]);
          if (run) {
            setRun(prev => prev ? { ...prev, status: event.data.status, progress: event.data.progress } : null);
          }
          break;
        case 'step_status':
          setLogs(prev => [...prev, `[${timestamp}] Step ${event.data.step_id}: ${event.data.status}`]);
          if (run) {
            setRun(prev => {
              if (!prev) return null;
              const updatedSteps = prev.steps.map(step => 
                step.step_id === event.data.step_id 
                  ? { ...step, status: event.data.status, execution_time_ms: event.data.execution_time_ms }
                  : step
              );
              return { ...prev, steps: updatedSteps };
            });
          }
          break;
        case 'artifact_created':
          setLogs(prev => [...prev, `[${timestamp}] Artifact created: ${event.data.artifact_name}`]);
          break;
        case 'error':
          setLogs(prev => [...prev, `[${timestamp}] ERROR: ${event.data.error_message}`]);
          break;
      }
    }
  );

  useEffect(() => {
    setWsConnected(isConnected);
  }, [isConnected]);

  const createDemoWorkflow = async () => {
    setIsCreating(true);
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Creating demo workflow...`]);
    
    try {
      // First, create a demo template
      const templateResponse = await fetch('/api/phase2/workflow/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'Phase 3 Demo Workflow',
          description: 'Demonstration workflow for Phase 3 UI testing',
          category: 'demo',
          definition: {
            steps: {
              'document_analysis': {
                agent_type: 'document_analysis',
                config: { mode: 'demo' },
                depends_on: []
              },
              'risk_assessment': {
                agent_type: 'architectural_risk',
                config: { threshold: 0.5 },
                depends_on: ['document_analysis']
              },
              'compliance_check': {
                agent_type: 'compliance_governance',
                config: { framework: 'demo' },
                depends_on: ['risk_assessment']
              }
            }
          }
        })
      });

      if (!templateResponse.ok) {
        throw new Error('Failed to create template');
      }

      const template = await templateResponse.json();
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Template created: ${template.name}`]);

      // Then start a workflow run
      const runResponse = await fetch('/api/phase2/workflow/runs/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: template.id,
          initial_context: { demo: true, ui_version: 'phase3' },
          auto_execute: false
        })
      });

      if (!runResponse.ok) {
        throw new Error('Failed to start workflow');
      }

      const newRun = await runResponse.json();
      setRun({
        ...newRun,
        steps: [
          { step_id: 'document_analysis', status: 'pending', agent_type: 'document_analysis' },
          { step_id: 'risk_assessment', status: 'pending', agent_type: 'architectural_risk' },
          { step_id: 'compliance_check', status: 'pending', agent_type: 'compliance_governance' }
        ]
      });
      
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Workflow run created: ${newRun.run_id}`]);

    } catch (error) {
      console.error('Error creating demo:', error);
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ERROR: ${error.message}`]);
    } finally {
      setIsCreating(false);
    }
  };

  const executeWorkflow = async () => {
    if (!run) return;
    
    setIsExecuting(true);
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Starting async execution...`]);
    
    try {
      const response = await fetch(`/api/phase2/workflow/runs/${run.id}/execute-async`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error('Failed to execute workflow');
      }

      const result = await response.json();
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Execution started: ${result.task_id}`]);

    } catch (error) {
      console.error('Error executing workflow:', error);
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ERROR: ${error.message}`]);
    } finally {
      setIsExecuting(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'running':
        return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const clearLogs = () => setLogs([]);

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Breadcrumb Navigation */}
      <nav aria-label="Breadcrumb" className="flex items-center space-x-2 text-sm text-gray-600">
        <Link href="/workflows" className="hover:text-blue-600 transition-colors">
          Workflows
        </Link>
        <ChevronRight className="h-4 w-4" />
        <Link href="/workflows/phase3" className="hover:text-blue-600 transition-colors">
          Phase 3 Portal
        </Link>
        <ChevronRight className="h-4 w-4" />
        <span className="text-gray-900">Live Demo</span>
      </nav>

      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Link href="/workflows/phase3">
            <Button variant="outline" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Portal
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Phase 3: Real-time Demo</h1>
            <p className="text-gray-600 mt-1">Live demonstration of workflow execution with WebSocket updates</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
            wsConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {wsConnected ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />}
            {wsConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>
      </div>

      {/* Demo Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            Demo Controls
          </CardTitle>
          <CardDescription>Create and execute a demo workflow to test Phase 3 features</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Button 
              onClick={createDemoWorkflow}
              disabled={isCreating || !!run}
            >
              <PlayCircle className="mr-2 h-4 w-4" />
              {isCreating ? 'Creating...' : 'Create Demo Workflow'}
            </Button>
            
            {run && run.status === 'created' && (
              <Button 
                onClick={executeWorkflow}
                disabled={isExecuting}
              >
                <Zap className="mr-2 h-4 w-4" />
                {isExecuting ? 'Starting...' : 'Execute Workflow'}
              </Button>
            )}
            
            <Button variant="outline" onClick={clearLogs}>
              Clear Logs
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Workflow Status */}
      {run && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitBranch className="h-5 w-5" />
              Workflow Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div>
                <span className="text-sm text-gray-500">Run ID</span>
                <p className="font-mono text-sm">{run.run_id.substring(0, 8)}...</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Status</span>
                <div className="flex items-center gap-2">
                  {getStatusIcon(run.status)}
                  <Badge>{run.status}</Badge>
                </div>
              </div>
              <div>
                <span className="text-sm text-gray-500">Progress</span>
                <p className="font-medium">{run.completed_steps}/{run.total_steps}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Started</span>
                <p className="text-sm">{run.started_at ? new Date(run.started_at).toLocaleTimeString() : 'Not started'}</p>
              </div>
            </div>
            
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Overall Progress</span>
                <span>{Math.round(run.progress)}%</span>
              </div>
              <Progress value={run.progress} className="h-2" />
            </div>

            {/* Step Status */}
            <div className="space-y-2">
              <h4 className="font-medium text-sm">Step Progress</h4>
              {run.steps.map((step, index) => (
                <div key={step.step_id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium w-4">{index + 1}.</span>
                    {getStatusIcon(step.status)}
                    <span className="text-sm">{step.step_id}</span>
                    <Badge variant="outline" className="text-xs">{step.agent_type}</Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={`text-xs ${
                      step.status === 'completed' ? 'bg-green-100 text-green-800' :
                      step.status === 'running' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {step.status}
                    </Badge>
                    {step.execution_time_ms && (
                      <span className="text-xs text-gray-500">{step.execution_time_ms}ms</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Real-time Logs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Real-time Event Log
            {wsConnected && <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />}
          </CardTitle>
          <CardDescription>Live updates from WebSocket connection</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-black text-green-400 p-4 rounded-lg font-mono text-sm h-64 overflow-y-auto">
            {logs.length === 0 ? (
              <p className="text-gray-500">No events yet. Create a workflow to see real-time updates.</p>
            ) : (
              logs.map((log, index) => (
                <div key={index} className="mb-1">{log}</div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Artifact Viewer */}
      {run && (
        <ArtifactViewer runId={run.run_id} />
      )}
    </div>
  );
}