'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  PlayCircle,
  PauseCircle,
  Eye, 
  Edit3, 
  Download,
  RefreshCw,
  Bot,
  FileText,
  Shield,
  AlertTriangle
} from 'lucide-react';

interface ExecutionStep {
  step_index: number;
  step_name: string;
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'review_required';
  automated: boolean;
  confidence_score?: number;
  requires_review: boolean;
  started_at?: string;
  completed_at?: string;
  execution_time_ms?: number;
}

interface ExecutionStatus {
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

interface WorkflowExecutionProps {
  executionId: string;
  onStatusChange?: (status: ExecutionStatus) => void;
}

export function WorkflowExecution({ executionId, onStatusChange }: WorkflowExecutionProps) {
  const [executionStatus, setExecutionStatus] = useState<ExecutionStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch execution status
  const fetchStatus = async () => {
    try {
      const response = await fetch(`/api/workflows/executions/${executionId}/status`);
      if (response.ok) {
        const status = await response.json();
        setExecutionStatus(status);
        setError(null);
        
        // Notify parent component
        if (onStatusChange) {
          onStatusChange(status);
        }
        
        // Stop auto-refresh if workflow is complete
        if (status.status === 'completed' || status.status === 'failed') {
          setAutoRefresh(false);
        }
      } else {
        throw new Error(`Failed to fetch status: ${response.statusText}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status');
    } finally {
      setIsLoading(false);
    }
  };

  // Set up auto-refresh
  useEffect(() => {
    fetchStatus();
    
    let interval: NodeJS.Timeout | null = null;
    if (autoRefresh) {
      interval = setInterval(fetchStatus, 5000); // Refresh every 5 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [executionId, autoRefresh]);

  const approveStep = async (stepIndex: number, data: any = {}) => {
    try {
      const response = await fetch(
        `/api/workflows/executions/${executionId}/steps/${stepIndex}/action`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: 'approve',
            data,
            comment: 'Approved by client'
          })
        }
      );
      
      if (response.ok) {
        // Refresh status after approval
        await fetchStatus();
      } else {
        throw new Error('Failed to approve step');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve step');
    }
  };

  const getStepIcon = (step: ExecutionStep) => {
    const iconClass = "w-5 h-5";
    
    switch (step.status) {
      case 'completed':
        return <CheckCircle2 className={`${iconClass} text-green-600`} />;
      case 'running':
        return <RefreshCw className={`${iconClass} text-blue-600 animate-spin`} />;
      case 'failed':
        return <AlertCircle className={`${iconClass} text-red-600`} />;
      case 'review_required':
        return <Eye className={`${iconClass} text-yellow-600`} />;
      default:
        return <Clock className={`${iconClass} text-gray-400`} />;
    }
  };

  const getStepBadgeColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-200';
      case 'running': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      case 'review_required': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatDuration = (startTime?: string, endTime?: string) => {
    if (!startTime) return '--';
    
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.round((end.getTime() - start.getTime()) / 1000);
    
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
  };

  if (isLoading && !executionStatus) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="w-6 h-6 animate-spin mr-2" />
        <span>Loading workflow status...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
          <span className="text-red-800 font-medium">Error</span>
        </div>
        <p className="text-red-700 mt-2">{error}</p>
        <Button
          onClick={fetchStatus}
          variant="outline"
          className="mt-4"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry
        </Button>
      </div>
    );
  }

  if (!executionStatus) {
    return (
      <div className="text-center p-8 text-gray-500">
        <AlertCircle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>Workflow execution not found</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">
              {executionStatus.template_name}
            </h1>
            <p className="text-gray-600">
              Execution ID: {executionStatus.execution_id}
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <Badge className={getStepBadgeColor(executionStatus.status)}>
              {executionStatus.status.charAt(0).toUpperCase() + executionStatus.status.slice(1)}
            </Badge>
            
            <Button
              onClick={() => setAutoRefresh(!autoRefresh)}
              variant="outline"
              size="sm"
            >
              {autoRefresh ? <PauseCircle className="w-4 h-4" /> : <PlayCircle className="w-4 h-4" />}
            </Button>
            
            <Button
              onClick={fetchStatus}
              variant="outline"
              size="sm"
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-600">
            <span>
              Step {executionStatus.current_step} of {executionStatus.total_steps}
            </span>
            <span>{Math.round(executionStatus.progress_percent)}% Complete</span>
          </div>
          <Progress value={executionStatus.progress_percent} className="h-3" />
        </div>
        
        {/* Timing Information */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 text-sm">
          <div>
            <span className="text-gray-600">Started:</span>
            <span className="ml-2 font-medium">
              {executionStatus.started_at 
                ? new Date(executionStatus.started_at).toLocaleString()
                : '--'}
            </span>
          </div>
          
          <div>
            <span className="text-gray-600">Duration:</span>
            <span className="ml-2 font-medium">
              {formatDuration(executionStatus.started_at, executionStatus.completed_at)}
            </span>
          </div>
          
          <div>
            <span className="text-gray-600">Last Activity:</span>
            <span className="ml-2 font-medium">
              {executionStatus.last_activity 
                ? new Date(executionStatus.last_activity).toLocaleString()
                : '--'}
            </span>
          </div>
        </div>
      </div>

      {/* Workflow Steps */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-900">Workflow Steps</h2>
        
        {executionStatus.steps.map((step) => (
          <Card key={step.step_index} className="border border-gray-200">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getStepIcon(step)}
                  <div>
                    <CardTitle className="text-lg">
                      Step {step.step_index + 1}: {step.step_name}
                    </CardTitle>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        <Bot className="w-3 h-3 mr-1" />
                        {step.agent_name}
                      </Badge>
                      
                      {step.automated && (
                        <Badge variant="secondary" className="text-xs">
                          Automated
                        </Badge>
                      )}
                      
                      {step.confidence_score !== undefined && (
                        <Badge variant="outline" className="text-xs">
                          {(step.confidence_score * 100).toFixed(0)}% Confidence
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
                
                <Badge className={getStepBadgeColor(step.status)}>
                  {step.status.replace('_', ' ').charAt(0).toUpperCase() + 
                   step.status.replace('_', ' ').slice(1)}
                </Badge>
              </div>
            </CardHeader>
            
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Started:</span>
                  <span className="ml-2">
                    {step.started_at 
                      ? new Date(step.started_at).toLocaleString()
                      : 'Not started'}
                  </span>
                </div>
                
                <div>
                  <span className="text-gray-600">Duration:</span>
                  <span className="ml-2">
                    {step.execution_time_ms 
                      ? `${step.execution_time_ms}ms`
                      : formatDuration(step.started_at, step.completed_at)}
                  </span>
                </div>
              </div>
              
              {/* Action Buttons */}
              {step.status === 'review_required' && (
                <div className="flex items-center space-x-2 mt-4 pt-4 border-t border-gray-200">
                  <AlertTriangle className="w-4 h-4 text-yellow-600" />
                  <span className="text-sm text-yellow-700 mr-auto">
                    This step requires your review before proceeding
                  </span>
                  
                  <Button
                    size="sm"
                    variant="outline"
                    className="mr-2"
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    Review Details
                  </Button>
                  
                  <Button
                    size="sm"
                    onClick={() => approveStep(step.step_index)}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    <CheckCircle2 className="w-4 h-4 mr-1" />
                    Approve
                  </Button>
                </div>
              )}
              
              {step.status === 'completed' && (
                <div className="flex items-center space-x-2 mt-4 pt-4 border-t border-gray-200">
                  <Button
                    size="sm"
                    variant="outline"
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    View Results
                  </Button>
                  
                  <Button
                    size="sm"
                    variant="outline"
                  >
                    <Edit3 className="w-4 h-4 mr-1" />
                    Modify
                  </Button>
                  
                  <Button
                    size="sm"
                    variant="outline"
                  >
                    <Download className="w-4 h-4 mr-1" />
                    Export
                  </Button>
                </div>
              )}
              
              {step.status === 'running' && (
                <div className="flex items-center space-x-2 mt-4 pt-4 border-t border-gray-200">
                  <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
                  <span className="text-sm text-blue-700">
                    Processing... This may take several minutes
                  </span>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Final Actions */}
      {executionStatus.status === 'completed' && (
        <Card className="bg-green-50 border border-green-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <CheckCircle2 className="w-6 h-6 text-green-600 mr-3" />
                <div>
                  <h3 className="text-lg font-semibold text-green-900">
                    Workflow Completed Successfully!
                  </h3>
                  <p className="text-green-700">
                    All steps have been executed and the threat analysis is ready.
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <Button
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Generate Report
                </Button>
                
                <Button variant="outline">
                  <Download className="w-4 h-4 mr-2" />
                  Export Data
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      
      {executionStatus.status === 'failed' && (
        <Card className="bg-red-50 border border-red-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <AlertCircle className="w-6 h-6 text-red-600 mr-3" />
                <div>
                  <h3 className="text-lg font-semibold text-red-900">
                    Workflow Failed
                  </h3>
                  <p className="text-red-700">
                    The workflow encountered an error and could not complete.
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <Button variant="outline">
                  <Eye className="w-4 h-4 mr-2" />
                  View Error Details
                </Button>
                
                <Button
                  className="bg-red-600 hover:bg-red-700 text-white"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Retry Workflow
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}