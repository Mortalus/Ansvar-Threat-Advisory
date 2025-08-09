'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { 
  ArrowLeft,
  Search, 
  Filter,
  Calendar,
  Clock,
  Play,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Eye,
  Download,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Activity,
  User,
  GitBranch
} from 'lucide-react';

interface WorkflowRun {
  id: string;
  run_id: string;
  template_name: string;
  status: string;
  progress: number;
  started_at: string;
  completed_at?: string;
  total_steps: number;
  completed_steps: number;
  started_by?: string;
  duration_ms?: number;
  error_message?: string;
}

export default function WorkflowHistoryPage() {
  const router = useRouter();
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [filteredRuns, setFilteredRuns] = useState<WorkflowRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [expandedRun, setExpandedRun] = useState<string | null>(null);
  const [limit, setLimit] = useState<number>(10);

  useEffect(() => {
    fetchRuns();
  }, [limit]);

  useEffect(() => {
    filterRuns();
  }, [runs, searchQuery, statusFilter]);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const limitParam = limit === -1 ? 1000 : limit; // Use large number for 'all'
      const response = await fetch(`/api/phase2/workflow/runs?limit=${limitParam}`);
      if (response.ok) {
        const data = await response.json();
        setRuns(data);
      } else {
        console.error('Failed to fetch workflow runs');
      }
    } catch (error) {
      console.error('Error fetching workflow runs:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterRuns = () => {
    let filtered = runs;

    // Filter by search query
    if (searchQuery.trim()) {
      filtered = filtered.filter(run =>
        run.template_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        run.run_id.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(run => run.status.toLowerCase() === statusFilter);
    }

    // Sort by most recent first
    filtered.sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime());

    setFilteredRuns(filtered);
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'running':
        return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'cancelled':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDuration = (durationMs?: number) => {
    if (!durationMs) return 'N/A';
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 7) {
      return date.toLocaleDateString();
    } else if (diffDays > 0) {
      return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    } else if (diffHours > 0) {
      return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else {
      return 'Less than an hour ago';
    }
  };

  const statuses = ['all', 'running', 'completed', 'failed', 'cancelled'];

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="space-y-4">
          <div className="h-8 bg-gray-200 rounded w-64 animate-pulse"></div>
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="h-24 bg-gray-200 rounded-lg animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/workflows">
            <Button variant="outline" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Workflows
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Execution History</h1>
            <p className="text-gray-600 mt-1">View and analyze past workflow executions</p>
          </div>
        </div>
        
        <Button variant="outline" onClick={fetchRuns}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search by template name or run ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        
        <div className="flex gap-2 items-center">
          <div className="flex gap-1">
            {statuses.map((status) => (
              <Button
                key={status}
                variant={statusFilter === status ? "default" : "outline"}
                size="sm"
                onClick={() => setStatusFilter(status)}
                className="capitalize whitespace-nowrap"
              >
                {status === 'all' ? 'All Status' : status}
              </Button>
            ))}
          </div>
          
          <div className="flex items-center gap-2 border-l pl-4 ml-2">
            <span className="text-sm text-gray-600 whitespace-nowrap">Show:</span>
            <div className="flex gap-1">
              {[10, 20, 30, 40, 50, -1].map((limitOption) => (
                <Button
                  key={limitOption}
                  variant={limit === limitOption ? "default" : "outline"}
                  size="sm"
                  onClick={() => setLimit(limitOption)}
                  className="min-w-12"
                >
                  {limitOption === -1 ? 'All' : limitOption.toString()}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      {runs.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Runs</p>
                  <p className="text-2xl font-bold">{runs.length}</p>
                </div>
                <Activity className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Completed</p>
                  <p className="text-2xl font-bold text-green-600">
                    {runs.filter(r => r.status === 'completed').length}
                  </p>
                </div>
                <CheckCircle2 className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Running</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {runs.filter(r => r.status === 'running').length}
                  </p>
                </div>
                <Play className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Failed</p>
                  <p className="text-2xl font-bold text-red-600">
                    {runs.filter(r => r.status === 'failed').length}
                  </p>
                </div>
                <XCircle className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Execution History List */}
      {filteredRuns.length > 0 ? (
        <div className="space-y-4">
          {filteredRuns.map((run) => (
            <Card key={run.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-0">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setExpandedRun(expandedRun === run.id ? null : run.id)}
                      >
                        {expandedRun === run.id ? 
                          <ChevronDown className="h-4 w-4" /> : 
                          <ChevronRight className="h-4 w-4" />
                        }
                      </Button>
                      <div>
                        <h3 className="font-semibold text-lg">{run.template_name}</h3>
                        <p className="text-sm text-gray-600 font-mono">{run.run_id}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <Badge className={`${getStatusColor(run.status)}`}>
                        <span className="flex items-center gap-1">
                          {getStatusIcon(run.status)}
                          {run.status}
                        </span>
                      </Badge>
                      
                      <div className="text-right text-sm text-gray-600">
                        <div>{formatRelativeTime(run.started_at)}</div>
                        <div>{formatDuration(run.duration_ms)}</div>
                      </div>

                      <div className="flex gap-2">
                        <Link href={`/workflows/phase3/${run.run_id}`}>
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Link>
                        <Button variant="outline" size="sm">
                          <Download className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-600">
                        Progress: {run.completed_steps}/{run.total_steps} steps
                      </span>
                      <span className="text-sm font-medium">{Math.round(run.progress)}%</span>
                    </div>
                    <Progress value={run.progress} className="h-2" />
                  </div>

                  {/* Expanded Details */}
                  {expandedRun === run.id && (
                    <div className="border-t pt-4 space-y-3">
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-gray-700">Started by:</span>
                          <div className="flex items-center gap-1 mt-1">
                            <User className="h-3 w-3 text-gray-400" />
                            <span>{run.started_by || 'System'}</span>
                          </div>
                        </div>
                        <div>
                          <span className="font-medium text-gray-700">Started at:</span>
                          <div className="flex items-center gap-1 mt-1">
                            <Calendar className="h-3 w-3 text-gray-400" />
                            <span>{new Date(run.started_at).toLocaleString()}</span>
                          </div>
                        </div>
                        {run.completed_at && (
                          <div>
                            <span className="font-medium text-gray-700">Completed at:</span>
                            <div className="flex items-center gap-1 mt-1">
                              <CheckCircle2 className="h-3 w-3 text-gray-400" />
                              <span>{new Date(run.completed_at).toLocaleString()}</span>
                            </div>
                          </div>
                        )}
                      </div>

                      {run.error_message && (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                          <div className="flex items-start gap-2">
                            <AlertCircle className="h-4 w-4 text-red-500 mt-0.5" />
                            <div>
                              <span className="text-sm font-medium text-red-800">Error:</span>
                              <p className="text-sm text-red-700 mt-1">{run.error_message}</p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="text-center py-12">
            <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchQuery || statusFilter !== 'all' ? 'No Matching Executions' : 'No Executions Found'}
            </h3>
            <p className="text-gray-600 mb-4">
              {searchQuery || statusFilter !== 'all'
                ? 'No workflow executions match your current filters.'
                : 'No workflows have been executed yet.'
              }
            </p>
            {!searchQuery && statusFilter === 'all' && (
              <Link href="/workflows/phase3">
                <Button>
                  <Play className="mr-2 h-4 w-4" />
                  Execute Your First Workflow
                </Button>
              </Link>
            )}
          </CardContent>
        </Card>
      )}

      {/* Footer */}
      {filteredRuns.length > 0 && (
        <div className="text-sm text-gray-500 text-center pt-4 border-t">
          Showing {filteredRuns.length} of {runs.length} execution{runs.length !== 1 ? 's' : ''}
          {limit !== -1 && runs.length >= limit && (
            <span className="ml-2 text-blue-600">
              (Limited to {limit} most recent)
            </span>
          )}
        </div>
      )}
    </div>
  );
}