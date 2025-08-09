'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  ArrowLeft,
  Search, 
  Plus,
  Edit3,
  Copy,
  Trash2,
  Play,
  Settings,
  GitBranch,
  Clock,
  User,
  Calendar,
  Filter,
  Grid3X3,
  List,
  MoreVertical
} from 'lucide-react';

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
  created_by?: string;
  step_count?: number;
  estimated_duration?: string;
}

export default function WorkflowTemplatesPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [filteredTemplates, setFilteredTemplates] = useState<WorkflowTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [view, setView] = useState<'grid' | 'list'>('grid');

  useEffect(() => {
    fetchTemplates();
  }, []);

  useEffect(() => {
    filterTemplates();
  }, [templates, searchQuery, selectedCategory]);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/phase2/workflow/templates');
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      } else {
        console.error('Failed to fetch templates');
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterTemplates = () => {
    let filtered = templates;

    // Filter by search query
    if (searchQuery.trim()) {
      filtered = filtered.filter(template =>
        template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        template.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(template => template.category === selectedCategory);
    }

    setFilteredTemplates(filtered);
  };

  const duplicateTemplate = async (templateId: string) => {
    try {
      const response = await fetch(`/api/phase2/workflow/templates/${templateId}/duplicate`, {
        method: 'POST',
      });
      if (response.ok) {
        fetchTemplates(); // Refresh the list
      }
    } catch (error) {
      console.error('Error duplicating template:', error);
    }
  };

  const toggleTemplateStatus = async (templateId: string, isActive: boolean) => {
    try {
      const response = await fetch(`/api/phase2/workflow/templates/${templateId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_active: !isActive }),
      });
      if (response.ok) {
        fetchTemplates(); // Refresh the list
      }
    } catch (error) {
      console.error('Error updating template status:', error);
    }
  };

  const categories = ['all', 'threat-modeling', 'security', 'compliance', 'demo'];

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="space-y-6">
          <div className="h-8 bg-gray-200 rounded w-64 animate-pulse"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="h-64 bg-gray-200 rounded-lg animate-pulse"></div>
            ))}
          </div>
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
            <h1 className="text-3xl font-bold">Workflow Templates</h1>
            <p className="text-gray-600 mt-1">Create and manage reusable workflow templates</p>
          </div>
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

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        
        <div className="flex gap-2">
          {categories.map((category) => (
            <Button
              key={category}
              variant={selectedCategory === category ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(category)}
              className="capitalize whitespace-nowrap"
            >
              {category === 'all' ? 'All' : category.replace('-', ' ')}
            </Button>
          ))}
        </div>
      </div>

      {/* Templates Grid/List */}
      {filteredTemplates.length > 0 ? (
        <div className={view === 'grid' 
          ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" 
          : "space-y-4"
        }>
          {filteredTemplates.map((template) => (
            <Card key={template.id} className="hover:shadow-md transition-shadow relative">
              {view === 'grid' ? (
                <>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <CardTitle className="text-lg truncate">{template.name}</CardTitle>
                          {template.is_default && (
                            <Badge variant="outline" className="text-xs">Default</Badge>
                          )}
                        </div>
                        <CardDescription className="line-clamp-2">
                          {template.description}
                        </CardDescription>
                      </div>
                      <Badge 
                        variant={template.is_active ? "default" : "secondary"}
                        className="ml-2 shrink-0"
                      >
                        {template.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                  </CardHeader>

                  <CardContent>
                    <div className="space-y-4">
                      {/* Template Details */}
                      <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                          <GitBranch className="h-3 w-3" />
                          <span>{template.step_count || 0} steps</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          <span>v{template.version}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <User className="h-3 w-3" />
                          <span className="truncate">{template.created_by || 'System'}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          <span className="capitalize">{template.category}</span>
                        </div>
                      </div>

                      <div className="text-xs text-gray-500">
                        Created: {new Date(template.created_at).toLocaleDateString()}
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2">
                        <Link href={`/workflows/phase3?template=${template.id}`} className="flex-1">
                          <Button size="sm" className="w-full">
                            <Play className="mr-2 h-4 w-4" />
                            Execute
                          </Button>
                        </Link>
                        <div className="flex gap-1">
                          <Link href={`/workflows/templates/${template.id}/edit`}>
                            <Button variant="outline" size="sm">
                              <Edit3 className="h-4 w-4" />
                            </Button>
                          </Link>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => duplicateTemplate(template.id)}
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </>
              ) : (
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <h3 className="font-medium truncate">{template.name}</h3>
                        <Badge 
                          variant={template.is_active ? "default" : "secondary"}
                          className="text-xs shrink-0"
                        >
                          {template.is_active ? "Active" : "Inactive"}
                        </Badge>
                        {template.is_default && (
                          <Badge variant="outline" className="text-xs shrink-0">Default</Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 truncate mb-2">{template.description}</p>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>{template.step_count || 0} steps</span>
                        <span>v{template.version}</span>
                        <span className="capitalize">{template.category}</span>
                        <span>Created {new Date(template.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <Link href={`/workflows/phase3?template=${template.id}`}>
                        <Button size="sm">
                          <Play className="mr-2 h-4 w-4" />
                          Execute
                        </Button>
                      </Link>
                      <Link href={`/workflows/templates/${template.id}/edit`}>
                        <Button variant="outline" size="sm">
                          <Edit3 className="h-4 w-4" />
                        </Button>
                      </Link>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => duplicateTemplate(template.id)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="text-center py-12">
            <GitBranch className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchQuery ? 'No Matching Templates' : 'No Templates Found'}
            </h3>
            <p className="text-gray-600 mb-4">
              {searchQuery 
                ? `No templates match your search "${searchQuery}"`
                : selectedCategory === 'all' 
                  ? "No workflow templates are available yet."
                  : `No templates found in the "${selectedCategory}" category.`
              }
            </p>
            {!searchQuery && (
              <Link href="/workflows/templates/create">
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Your First Template
                </Button>
              </Link>
            )}
          </CardContent>
        </Card>
      )}

      {/* Summary */}
      {filteredTemplates.length > 0 && (
        <div className="text-sm text-gray-500 text-center pt-4 border-t">
          Showing {filteredTemplates.length} of {templates.length} template{templates.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}