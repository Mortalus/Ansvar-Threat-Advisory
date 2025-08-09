'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  ArrowRight, 
  Play, 
  Clock, 
  CheckCircle2, 
  AlertCircle,
  GitBranch,
  Zap,
  Settings,
  History,
  Plus,
  Search,
  Filter,
  Grid3X3,
  List
} from 'lucide-react';

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  is_active: boolean;
  created_at: string;
  step_count?: number;
  estimated_duration?: string;
}

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
}

export default function WorkflowsPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [recentRuns, setRecentRuns] = useState<WorkflowRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'grid' | 'list'>('grid');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch workflow templates
      const templatesResponse = await fetch('/api/phase2/workflow/templates');
      if (templatesResponse.ok) {
        const templatesData = await templatesResponse.json();
        setTemplates(templatesData);
      }

      // Fetch recent workflow runs
      const runsResponse = await fetch('/api/phase2/workflow/runs?limit=5');
      if (runsResponse.ok) {
        const runsData = await runsResponse.json();
        setRecentRuns(runsData);
      }
    } catch (error) {
      console.error('Error fetching workflow data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'running':
        return <Play className="h-4 w-4 text-blue-500" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
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
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const categories = ['all', 'threat-modeling', 'security', 'compliance', 'demo'];
  const filteredTemplates = templates.filter(template => 
    selectedCategory === 'all' || template.category === selectedCategory
  );

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="space-y-6">
          <div className="h-8 bg-gray-200 rounded w-64 animate-pulse"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="h-48 bg-gray-200 rounded-lg animate-pulse"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-4xl font-bold">Workflows</h1>
          <p className="text-gray-600 mt-2">Manage and execute your threat modeling workflows</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={() => setView(view === 'grid' ? 'list' : 'grid')}>
            {view === 'grid' ? <List className="h-4 w-4" /> : <Grid3X3 className="h-4 w-4" />}
          </Button>
          <Link href="/workflows/templates/create">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Template
            </Button>
          </Link>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link href="/workflows/phase3">
          <Card className="hover:shadow-md transition-shadow cursor-pointer border-blue-200 bg-blue-50">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <Zap className="h-6 w-6 text-blue-600" />
                <ArrowRight className="h-4 w-4 text-blue-600" />
              </div>
              <CardTitle className="text-blue-900">Phase 3 Portal</CardTitle>
              <CardDescription className="text-blue-700">
                Advanced workflow execution with real-time updates
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>

        <Link href="/workflows/templates">
          <Card className="hover:shadow-md transition-shadow cursor-pointer border-green-200 bg-green-50">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <Settings className="h-6 w-6 text-green-600" />
                <ArrowRight className="h-4 w-4 text-green-600" />
              </div>
              <CardTitle className="text-green-900">Template Management</CardTitle>
              <CardDescription className="text-green-700">
                Create, edit, and manage workflow templates
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>

        <Link href="/workflows/history">
          <Card className="hover:shadow-md transition-shadow cursor-pointer border-purple-200 bg-purple-50">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <History className="h-6 w-6 text-purple-600" />
                <ArrowRight className="h-4 w-4 text-purple-600" />
              </div>
              <CardTitle className="text-purple-900">Execution History</CardTitle>
              <CardDescription className="text-purple-700">
                View and analyze past workflow executions
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>
      </div>

      {/* Recent Activity */}
      {recentRuns.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-semibold">Recent Activity</h2>
            <Link href="/workflows/history">
              <Button variant="outline" size="sm">
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {recentRuns.slice(0, 4).map((run) => (
              <Link key={run.id} href={`/workflows/phase3/${run.run_id}`}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium truncate">{run.template_name}</h3>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(run.status)}
                        <Badge className={`text-xs ${getStatusColor(run.status)}`}>
                          {run.status}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>{run.completed_steps}/{run.total_steps} steps</span>
                      <span>{new Date(run.started_at).toLocaleDateString()}</span>
                    </div>
                    <div className="mt-2 w-full bg-gray-200 rounded-full h-1.5">
                      <div 
                        className="bg-blue-500 h-1.5 rounded-full transition-all"
                        style={{ width: `${run.progress}%` }}
                      ></div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Workflow Templates */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold">Workflow Templates</h2>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm">
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Filter
            </Button>
          </div>
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap gap-2 mb-6">
          {categories.map((category) => (
            <Button
              key={category}
              variant={selectedCategory === category ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(category)}
              className="capitalize"
            >
              {category === 'all' ? 'All Categories' : category.replace('-', ' ')}
            </Button>
          ))}
        </div>

        {/* Templates Grid */}
        {filteredTemplates.length > 0 ? (
          <div className={view === 'grid' 
            ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" 
            : "space-y-4"
          }>
            {filteredTemplates.map((template) => (
              <Card key={template.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{template.name}</CardTitle>
                      <CardDescription className="mt-1">
                        {template.description}
                      </CardDescription>
                    </div>
                    <Badge 
                      variant={template.is_active ? "default" : "secondary"}
                      className="ml-2"
                    >
                      {template.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between text-sm text-gray-600 mb-4">
                    <span className="flex items-center gap-1">
                      <GitBranch className="h-3 w-3" />
                      {template.step_count || 0} steps
                    </span>
                    <span className="capitalize">{template.category}</span>
                  </div>
                  <div className="flex gap-2">
                    <Link href={`/workflows/phase3?template=${template.id}`} className="flex-1">
                      <Button size="sm" className="w-full">
                        <Play className="mr-2 h-4 w-4" />
                        Execute
                      </Button>
                    </Link>
                    <Link href={`/workflows/templates/${template.id}`}>
                      <Button variant="outline" size="sm">
                        <Settings className="h-4 w-4" />
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="text-center py-12">
              <GitBranch className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Templates Found</h3>
              <p className="text-gray-600 mb-4">
                {selectedCategory === 'all' 
                  ? "No workflow templates are available yet."
                  : `No templates found in the "${selectedCategory}" category.`
                }
              </p>
              <Link href="/workflows/templates/create">
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Your First Template
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}