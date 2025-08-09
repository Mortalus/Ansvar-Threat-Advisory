'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  PlayCircle, 
  FileText, 
  Clock, 
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ArrowRight,
  Layers,
  GitBranch,
  Activity,
  ChevronRight,
  ArrowLeft
} from 'lucide-react';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';

interface WorkflowTemplate {
  id: number;
  name: string;
  description: string;
  category: string;
  version: string;
  is_active: boolean;
  steps_count: number;
}

interface WorkflowRun {
  id: number;
  run_id: string;
  template_id: number;
  status: string;
  progress: number;
  total_steps: number;
  completed_steps: number;
  started_at?: string;
  completed_at?: string;
  can_retry: boolean;
  is_terminal: boolean;
}

export default function Phase3WorkflowPortal() {
  const router = useRouter();
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<WorkflowTemplate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dfdText, setDfdText] = useState('');
  const [starting, setStarting] = useState(false);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<string | null>(null);
  const [runProgress, setRunProgress] = useState<number>(0);
  const [dfdOutput, setDfdOutput] = useState<any | null>(null);

  // Fetch templates on mount and set up polling
  useEffect(() => {
    fetchTemplates();
    fetchRuns();
    
    // Set up polling for runs every 3 seconds
    const pollInterval = setInterval(() => {
      fetchRuns();
    }, 3000);
    
    return () => clearInterval(pollInterval);
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/phase2/workflow/templates');
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      } else {
        setError('Failed to fetch workflow templates');
      }
    } catch (err) {
      setError('Error connecting to server');
    } finally {
      setLoading(false);
    }
  };

  const fetchRuns = async () => {
    try {
      const response = await fetch('/api/phase2/workflow/runs');
      if (response.ok) {
        const data = await response.json();
        setRuns(data);
      }
    } catch (err) {
      console.error('Error fetching runs:', err);
    }
  };

  const startWorkflow = async (templateId: number) => {
    try {
      setLoading(true);
      const token = (typeof window !== 'undefined') ? localStorage.getItem('session_token') : null;
      if (!token) {
        router.push('/login');
        return;
      }
      const response = await fetch('/api/phase2/workflow/runs/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          template_id: templateId,
          initial_context: { source: 'phase3_ui' },
          auto_execute: true
        })
      });

      if (response.ok) {
        const newRun = await response.json();
        setRuns([newRun, ...runs]);
        setSelectedTemplate(null);
        // Navigate to run details using the UUID run_id
        if (newRun.run_id) {
          router.push(`/workflows/phase3/${newRun.run_id}`);
        }
      } else {
        setError('Failed to start workflow');
      }
    } catch (err) {
      setError('Error starting workflow');
    } finally {
      setLoading(false);
    }
  };

  const startSingleStepRun = async () => {
    try {
      setStarting(true);
      // Fetch templates fresh so we don't rely on state timing
      const token = (typeof window !== 'undefined') ? localStorage.getItem('session_token') : null;
      if (!token) {
        router.push('/login');
        return;
      }

      const listResp = await fetch('/api/phase2/workflow/templates', { headers: { 'Authorization': `Bearer ${token}` } });
      let list: WorkflowTemplate[] = [];
      if (listResp.ok) list = await listResp.json();
      let template = list.find(t => t.name === 'DFD Extractor (Single-step)');
      if (!template) {
        // Try to seed and re-fetch once
        await fetch('/api/phase2/workflow/templates/seed-demo', { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } });
        const listResp2 = await fetch('/api/phase2/workflow/templates', { headers: { 'Authorization': `Bearer ${token}` } });
        if (listResp2.ok) list = await listResp2.json();
        template = list.find(t => t.name === 'DFD Extractor (Single-step)');
      }
      if (!template) {
        setError('DFD Extractor template not available');
        return;
      }

      const token2 = (typeof window !== 'undefined') ? localStorage.getItem('session_token') : null;
      if (!token2) {
        // Redirect to login if not authenticated
        router.push('/login');
        return;
      }

      const resp = await fetch('/api/phase2/workflow/runs/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token2}` },
        body: JSON.stringify({
          template_id: template.id,
          initial_context: { document_text: dfdText },
          auto_execute: true
        })
      });
      if (!resp.ok) {
        setError('Failed to start DFD extractor workflow');
        return;
      }
      const newRun = await resp.json();
      setDfdText('');
      if (newRun?.run_id) {
        setActiveRunId(newRun.run_id);
        setRunStatus(newRun.status || 'created');
        setRunProgress(newRun.progress || 0);
        // Begin polling until terminal
        pollRunUntilDone(newRun.run_id);
      }
    } catch (e) {
      setError('Error starting DFD extractor workflow');
    } finally {
      setStarting(false);
    }
  };

  const pollRunUntilDone = async (runId: string) => {
    const poll = async () => {
      try {
        const res = await fetch(`/api/phase2/workflow/runs/${runId}/status`);
        if (!res.ok) return;
        const data = await res.json();
        setRunStatus(data.status);
        setRunProgress(data.progress);
        if (data.status === 'completed' || data.is_terminal) {
          // fetch artifacts with content
          const art = await fetch(`/api/phase2/workflow/runs/${runId}/artifacts?include_content=true`);
          if (art.ok) {
            const j = await art.json();
            const primary = (j.artifacts || []).find((a: any) => a.name?.endsWith('_output'));
            if (primary?.content_json?.dfd_components) setDfdOutput(primary.content_json.dfd_components);
            else if (primary?.content_json) setDfdOutput(primary.content_json);
          }
          return; // stop
        }
        setTimeout(poll, 2000);
      } catch (e) {
        // stop silently
      }
    };
    poll();
  };

  const handleFileUpload = async (file: File) => {
    try {
      const text = await file.text();
      setDfdText(text);
    } catch (e) {
      setError('Failed to read file');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'running':
        return <Activity className="h-5 w-5 text-blue-500 animate-pulse" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'created':
      case 'pending':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Breadcrumb Navigation */}
      <nav aria-label="Breadcrumb" className="flex items-center space-x-2 text-sm text-gray-600">
        <Link href="/workflows" className="hover:text-blue-600 transition-colors">
          Workflows
        </Link>
        <ChevronRight className="h-4 w-4" />
        <span className="text-gray-900">Phase 3 Portal</span>
      </nav>

      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Link href="/workflows">
            <Button variant="outline" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Workflows
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Phase 3: Workflow Portal</h1>
            <p className="text-gray-600 mt-1">Client interface for workflow execution with real-time tracking</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => { fetchTemplates(); fetchRuns(); }}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
          </Button>
        </div>
      </div>
      {/* DFD Extractor Card (Input -> Agent -> Output) */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <CardTitle>dfd_extractor</CardTitle>
                <Badge variant="outline">architecture</Badge>
                <Badge className="bg-green-100 text-green-800">Enabled</Badge>
              </div>
              <div className="text-sm text-gray-500 mt-1">v1.0.0</div>
              <CardDescription className="mt-2">Extracts DFD components (entities, processes, assets, flows, boundaries) from document text</CardDescription>
            </div>
            <div className="text-sm text-gray-600 space-y-1 text-right">
              <div>
                Priority: <span className="text-red-500 font-medium">15</span>
              </div>
              <div>Est. Tokens: 3,000</div>
              <div className="flex items-center justify-end gap-1">Requirements: <span title="Text document">📄</span></div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid gap-3">
              <Label htmlFor="dfd-text">Input</Label>
              <Textarea id="dfd-text" rows={8} value={dfdText} onChange={(e) => setDfdText(e.target.value)} placeholder="Paste your system description here..." />
              <div className="flex items-center gap-3">
                <input id="dfd-file" type="file" accept=".txt" onChange={(e) => { const f=e.target.files?.[0]; if (f) handleFileUpload(f); }} />
                <span className="text-xs text-gray-500">Upload .txt to prefill</span>
              </div>
              <div className="flex justify-end">
                <Button disabled={!dfdText.trim() || starting} onClick={startSingleStepRun}>
                  {starting ? 'Starting...' : 'Run DFD Extractor'}
                </Button>
              </div>
            </div>

            {(activeRunId || runStatus) && (
              <div className="rounded border p-3">
                <div className="text-sm text-gray-600 mb-2">Execution</div>
                <div className="text-sm">Run ID: <span className="font-mono">{activeRunId}</span></div>
                <div className="text-sm">Status: <Badge className="ml-1">{runStatus || 'created'}</Badge></div>
                <div className="text-sm">Progress: {Math.round(runProgress)}%</div>
              </div>
            )}

            <div className="rounded border p-3">
              <div className="text-sm text-gray-600 mb-2">Output</div>
              {dfdOutput ? (
                <pre className="text-xs bg-gray-50 text-gray-900 p-3 rounded overflow-auto max-h-80">{JSON.stringify(dfdOutput, null, 2)}</pre>
              ) : (
                <div className="text-sm text-gray-500">No output yet. Run the agent to see JSON here.</div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>


      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Workflow Templates - Only show if no runs exist */}
      {runs.length === 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Layers className="h-5 w-5" />
              Available Workflow Templates
            </CardTitle>
            <CardDescription>Select a template to start your first workflow execution</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8">
                <RefreshCw className="h-8 w-8 animate-spin mx-auto text-gray-400" />
                <p className="text-gray-500 mt-2">Loading templates...</p>
              </div>
            ) : templates.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 mx-auto text-gray-300" />
                <p className="text-gray-500 mt-2">No workflow templates available</p>
                <p className="text-sm text-gray-400 mt-1">Create templates using the admin interface</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {templates.map((template) => (
                  <Card 
                    key={template.id} 
                    className="hover:shadow-lg transition-shadow cursor-pointer"
                    onClick={() => setSelectedTemplate(template)}
                  >
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="font-semibold">{template.name}</h3>
                          <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                        </div>
                        {template.is_active && (
                          <Badge className="bg-green-100 text-green-800">Active</Badge>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <GitBranch className="h-4 w-4" />
                            {template.steps_count} steps
                          </span>
                          <span>v{template.version}</span>
                        </div>
                        <Button 
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            startWorkflow(template.id);
                          }}
                        >
                          <PlayCircle className="mr-1 h-4 w-4" />
                          Start
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Recent Workflow Runs */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Recent Workflow Executions
              </CardTitle>
              <CardDescription>Monitor your latest workflow runs</CardDescription>
            </div>
            {runs.length > 0 && (
              <div className="flex gap-2">
                {runs.length > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open('/workflows/history', '_blank')}
                  >
                    View All Executions
                    <ArrowRight className="ml-1 h-4 w-4" />
                  </Button>
                )}
                <Button
                  size="sm"
                  onClick={() => setSelectedTemplate(templates[0])} // Quick start with first template
                  disabled={templates.length === 0}
                >
                  <PlayCircle className="mr-1 h-4 w-4" />
                  New Execution
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {runs.length === 0 ? (
            <div className="text-center py-8">
              <Clock className="h-12 w-12 mx-auto text-gray-300" />
              <p className="text-gray-500 mt-2">No workflow runs yet</p>
              <p className="text-sm text-gray-400 mt-1">Start your first workflow using the templates above</p>
            </div>
          ) : (
            <div className="space-y-4">
              {runs.slice(0, 3).map((run) => (
                <Card key={run.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        {getStatusIcon(run.status)}
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-sm text-gray-500">
                              {run.run_id.substring(0, 8)}...
                            </span>
                            <Badge className={getStatusColor(run.status)}>
                              {run.status}
                            </Badge>
                          </div>
                          <div className="text-sm text-gray-600 mt-1">
                            Progress: {run.completed_steps}/{run.total_steps} steps
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4">
                        <div className="w-32">
                          <div className="flex justify-between text-sm text-gray-600 mb-1">
                            <span>Progress</span>
                            <span>{Math.round(run.progress)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full transition-all"
                              style={{ width: `${run.progress}%` }}
                            />
                          </div>
                        </div>
                        
                        <div className="flex gap-2">
                          {run.can_retry && run.is_terminal && (
                            <Button size="sm" variant="outline">
                              <RefreshCw className="h-4 w-4" />
                            </Button>
                          )}
                          <Button 
                            size="sm"
                            onClick={() => router.push(`/workflows/phase3/${run.run_id}`)}
                          >
                            View Details
                            <ArrowRight className="ml-1 h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                    
                    {run.started_at && (
                      <div className="mt-3 pt-3 border-t text-xs text-gray-500">
                        Started: {new Date(run.started_at).toLocaleString()}
                        {run.completed_at && (
                          <span className="ml-4">
                            Completed: {new Date(run.completed_at).toLocaleString()}
                          </span>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
              {runs.length > 3 && (
                <div className="text-center pt-4">
                  <p className="text-sm text-gray-500 mb-2">
                    Showing 3 of {runs.length} executions
                  </p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Template Details Modal */}
      {selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl m-4">
            <CardHeader>
              <CardTitle>{selectedTemplate.name}</CardTitle>
              <CardDescription>{selectedTemplate.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-sm text-gray-500">Category</span>
                    <p className="font-medium">{selectedTemplate.category}</p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Version</span>
                    <p className="font-medium">{selectedTemplate.version}</p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Total Steps</span>
                    <p className="font-medium">{selectedTemplate.steps_count}</p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Status</span>
                    <p className="font-medium">
                      {selectedTemplate.is_active ? 'Active' : 'Inactive'}
                    </p>
                  </div>
                </div>
                
                <div className="flex justify-end gap-2 pt-4 border-t">
                  <Button 
                    variant="outline" 
                    onClick={() => setSelectedTemplate(null)}
                  >
                    Cancel
                  </Button>
                  <Button 
                    onClick={() => {
                      startWorkflow(selectedTemplate.id);
                    }}
                    disabled={loading}
                  >
                    <PlayCircle className="mr-2 h-4 w-4" />
                    Start Workflow
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}