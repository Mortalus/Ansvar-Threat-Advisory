"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Play, 
  Pause, 
  CheckCircle, 
  XCircle, 
  Clock, 
  User, 
  AlertTriangle,
  RefreshCw,
  Eye,
  Filter,
  Calendar,
  TrendingUp
} from 'lucide-react';

interface WorkflowExecution {
  execution_id: string;
  template_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused';
  current_step: number;
  total_steps: number;
  progress_percent: number;
  started_at?: string;
  completed_at?: string;
  last_activity?: string;
  client_id?: string;
  client_email?: string;
  steps: ExecutionStep[];
}

interface ExecutionStep {
  step_index: number;
  step_name: string;
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  automated: boolean;
  confidence_score?: number;
  requires_review: boolean;
  started_at?: string;
  completed_at?: string;
  execution_time_ms?: number;
}

export default function WorkflowExecutionsPage() {
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null);
  const [filter, setFilter] = useState({
    status: 'all',
    client: '',
    template: '',
  });
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Auto-refresh executions
  useEffect(() => {
    const loadExecutions = async () => {
      try {
        // In a real implementation, this would be an API call to get all executions
        // For now, we'll simulate with sample data
        const sampleExecutions: WorkflowExecution[] = [
          {
            execution_id: '91789328-91cc-4e6b-b2cd-3ba930923a6b',
            template_name: 'Complete Threat Analysis',
            status: 'completed',
            current_step: 3,
            total_steps: 3,
            progress_percent: 100,
            started_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
            completed_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
            last_activity: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
            client_id: 'test_client',
            client_email: 'demo@company.com',
            steps: [
              {
                step_index: 0,
                step_name: 'Document Analysis',
                agent_name: 'document_analysis',
                status: 'completed',
                automated: true,
                confidence_score: 0.90,
                requires_review: false,
                started_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
                completed_at: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
                execution_time_ms: 2500,
              },
              {
                step_index: 1,
                step_name: 'Architectural Risk Assessment',
                agent_name: 'architectural_risk',
                status: 'completed',
                automated: true,
                confidence_score: 0.95,
                requires_review: false,
                started_at: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
                completed_at: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
                execution_time_ms: 3100,
              },
              {
                step_index: 2,
                step_name: 'Business Impact Analysis',
                agent_name: 'business_financial',
                status: 'completed',
                automated: true,
                confidence_score: 0.80,
                requires_review: false,
                started_at: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
                completed_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
                execution_time_ms: 1800,
              },
            ]
          },
          {
            execution_id: '45abc123-def4-5678-9012-3456789abcde',
            template_name: 'Quick Security Scan',
            status: 'running',
            current_step: 2,
            total_steps: 3,
            progress_percent: 67,
            started_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
            last_activity: new Date(Date.now() - 1000 * 30).toISOString(),
            client_id: 'client_xyz',
            client_email: 'security@clientxyz.com',
            steps: [
              {
                step_index: 0,
                step_name: 'Document Scan',
                agent_name: 'document_analysis',
                status: 'completed',
                automated: true,
                confidence_score: 0.88,
                requires_review: false,
                execution_time_ms: 1200,
              },
              {
                step_index: 1,
                step_name: 'Risk Assessment',
                agent_name: 'architectural_risk',
                status: 'running',
                automated: false,
                requires_review: false,
              },
              {
                step_index: 2,
                step_name: 'Compliance Check',
                agent_name: 'compliance_governance',
                status: 'pending',
                automated: false,
                requires_review: true,
              },
            ]
          },
          {
            execution_id: '78def456-ghi7-8901-2345-6789abcdef01',
            template_name: 'Financial Risk Analysis',
            status: 'failed',
            current_step: 1,
            total_steps: 2,
            progress_percent: 50,
            started_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
            last_activity: new Date(Date.now() - 1000 * 60 * 25).toISOString(),
            client_id: 'client_abc',
            steps: [
              {
                step_index: 0,
                step_name: 'Business Analysis',
                agent_name: 'business_financial',
                status: 'completed',
                automated: false,
                confidence_score: 0.65,
                requires_review: true,
                execution_time_ms: 4500,
              },
              {
                step_index: 1,
                step_name: 'Compliance Review',
                agent_name: 'compliance_governance',
                status: 'failed',
                automated: false,
                requires_review: true,
              },
            ]
          }
        ];
        
        setExecutions(sampleExecutions);
        setLoading(false);
      } catch (error) {
        console.error('Failed to load executions:', error);
        setLoading(false);
      }
    };

    loadExecutions();

    if (autoRefresh) {
      const interval = setInterval(loadExecutions, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'paused': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4" />;
      case 'running': return <Play className="h-4 w-4" />;
      case 'failed': return <XCircle className="h-4 w-4" />;
      case 'pending': return <Clock className="h-4 w-4" />;
      case 'paused': return <Pause className="h-4 w-4" />;
      default: return <Clock className="h-4 w-4" />;
    }
  };

  const formatTimeAgo = (timestamp?: string) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const filteredExecutions = executions.filter(exec => {
    if (filter.status !== 'all' && exec.status !== filter.status) return false;
    if (filter.client && !exec.client_id?.toLowerCase().includes(filter.client.toLowerCase())) return false;
    if (filter.template && !exec.template_name.toLowerCase().includes(filter.template.toLowerCase())) return false;
    return true;
  });

  const stats = {
    total: executions.length,
    running: executions.filter(e => e.status === 'running').length,
    completed: executions.filter(e => e.status === 'completed').length,
    failed: executions.filter(e => e.status === 'failed').length,
    avgProgress: Math.round(executions.reduce((sum, e) => sum + e.progress_percent, 0) / executions.length || 0),
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Workflow Executions</h1>
          <p className="text-muted-foreground mt-1">
            Monitor and manage running threat modeling workflows
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={autoRefresh ? 'text-blue-600' : ''}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto Refresh
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Executions</p>
              <div className="text-2xl font-bold">{stats.total}</div>
            </div>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Running</p>
              <div className="text-2xl font-bold text-blue-600">{stats.running}</div>
            </div>
            <Play className="h-4 w-4 text-blue-600" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Completed</p>
              <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
            </div>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Failed</p>
              <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
            </div>
            <XCircle className="h-4 w-4 text-red-600" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Avg Progress</p>
              <div className="text-2xl font-bold">{stats.avgProgress}%</div>
            </div>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center space-x-4">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium">Status:</label>
              <Select value={filter.status} onValueChange={(value) => setFilter(prev => ({ ...prev, status: value }))}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="running">Running</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="paused">Paused</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium">Client:</label>
              <Input
                placeholder="Filter by client..."
                value={filter.client}
                onChange={(e) => setFilter(prev => ({ ...prev, client: e.target.value }))}
                className="w-40"
              />
            </div>
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium">Template:</label>
              <Input
                placeholder="Filter by template..."
                value={filter.template}
                onChange={(e) => setFilter(prev => ({ ...prev, template: e.target.value }))}
                className="w-48"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Executions List */}
      <div className="grid gap-4">
        {loading ? (
          <Card>
            <CardContent className="flex items-center justify-center p-12">
              <RefreshCw className="h-6 w-6 animate-spin mr-2" />
              Loading executions...
            </CardContent>
          </Card>
        ) : filteredExecutions.length === 0 ? (
          <Card>
            <CardContent className="text-center p-12">
              <div className="text-muted-foreground">No workflow executions found matching the current filters.</div>
            </CardContent>
          </Card>
        ) : (
          filteredExecutions.map((execution) => (
            <Card key={execution.execution_id} className="cursor-pointer hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <Badge className={getStatusColor(execution.status)}>
                      {getStatusIcon(execution.status)}
                      <span className="ml-1">{execution.status}</span>
                    </Badge>
                    <div>
                      <h3 className="font-semibold">{execution.template_name}</h3>
                      <p className="text-sm text-muted-foreground">
                        ID: {execution.execution_id.substring(0, 8)}...
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                    {execution.client_email && (
                      <div className="flex items-center space-x-1">
                        <User className="h-4 w-4" />
                        <span>{execution.client_email}</span>
                      </div>
                    )}
                    <div className="flex items-center space-x-1">
                      <Calendar className="h-4 w-4" />
                      <span>{formatTimeAgo(execution.started_at)}</span>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setSelectedExecution(
                        selectedExecution?.execution_id === execution.execution_id ? null : execution
                      )}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Progress: {execution.current_step} / {execution.total_steps} steps</span>
                    <span>{execution.progress_percent}%</span>
                  </div>
                  <Progress value={execution.progress_percent} className="w-full" />
                </div>

                {/* Step Details */}
                {selectedExecution?.execution_id === execution.execution_id && (
                  <div className="mt-6 pt-4 border-t space-y-3">
                    <h4 className="font-medium flex items-center">
                      Step Details
                      {execution.steps.some(s => s.requires_review) && (
                        <AlertTriangle className="h-4 w-4 ml-2 text-yellow-600" />
                      )}
                    </h4>
                    {execution.steps.map((step) => (
                      <div key={step.step_index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <Badge variant="outline">
                            {step.step_index + 1}
                          </Badge>
                          <div>
                            <div className="font-medium">{step.step_name}</div>
                            <div className="text-sm text-muted-foreground">
                              Agent: {step.agent_name}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          {step.confidence_score !== undefined && (
                            <div className="text-sm">
                              <span className="text-muted-foreground">Confidence:</span>
                              <span className="ml-1 font-medium">
                                {(step.confidence_score * 100).toFixed(0)}%
                              </span>
                            </div>
                          )}
                          {step.execution_time_ms && (
                            <div className="text-sm text-muted-foreground">
                              {step.execution_time_ms}ms
                            </div>
                          )}
                          <div className="flex items-center space-x-1">
                            {step.automated && (
                              <Badge variant="secondary">Auto</Badge>
                            )}
                            {step.requires_review && (
                              <Badge variant="outline" className="text-yellow-600">
                                Review
                              </Badge>
                            )}
                            <Badge className={getStatusColor(step.status)}>
                              {step.status}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}