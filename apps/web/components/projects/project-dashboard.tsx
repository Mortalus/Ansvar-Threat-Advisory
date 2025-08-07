"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { 
  Plus, 
  Search, 
  Calendar, 
  FolderOpen, 
  GitBranch, 
  Target, 
  Clock,
  AlertTriangle,
  CheckCircle,
  Play,
  Archive
} from 'lucide-react';

interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at?: string;
  created_by?: string;
  tags?: string[];
  session_count: number;
  latest_session?: {
    id: string;
    name: string;
    status: string;
    completion_percentage: number;
    updated_at: string;
  };
}

interface ProjectDashboardProps {
  onCreateProject: () => void;
  onSelectProject: (project: Project) => void;
  onLoadSession: (sessionId: string, projectId: string) => void;
}

export default function ProjectDashboard({ 
  onCreateProject, 
  onSelectProject, 
  onLoadSession 
}: ProjectDashboardProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Load projects from API
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/projects', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to load projects: ${response.statusText}`);
      }

      const data = await response.json();
      setProjects(data);
      console.log('📋 Loaded projects:', data.length);
      
    } catch (err) {
      console.error('❌ Failed to load projects:', err);
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  // Filter projects based on search
  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (project.description && project.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'active':
        return <Play className="h-4 w-4 text-blue-500" />;
      case 'archived':
        return <Archive className="h-4 w-4 text-gray-500" />;
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRiskColor = (percentage: number) => {
    if (percentage >= 80) return 'text-red-500';
    if (percentage >= 60) return 'text-orange-500';
    if (percentage >= 40) return 'text-yellow-500';
    return 'text-green-500';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2 text-gray-600">Loading projects...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">🛡️ Threat Modeling Projects</h1>
          <p className="text-gray-600 mt-1">
            Manage your security analysis projects and sessions
          </p>
        </div>
        <Button 
          onClick={onCreateProject}
          className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          <span>New Project</span>
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
        <input
          type="text"
          placeholder="Search projects..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Error State */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2 text-red-700">
              <AlertTriangle className="h-4 w-4" />
              <span>{error}</span>
            </div>
            <Button 
              onClick={loadProjects}
              className="mt-2 text-sm bg-red-600 hover:bg-red-700"
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Projects Grid */}
      {filteredProjects.length === 0 ? (
        <Card className="border-dashed border-2 border-gray-300">
          <CardContent className="p-8 text-center">
            <FolderOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {projects.length === 0 ? 'No projects yet' : 'No projects found'}
            </h3>
            <p className="text-gray-600 mb-4">
              {projects.length === 0 
                ? 'Create your first threat modeling project to get started'
                : 'Try adjusting your search term'
              }
            </p>
            {projects.length === 0 && (
              <Button 
                onClick={onCreateProject}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create First Project
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <Card 
              key={project.id} 
              className="hover:shadow-lg transition-shadow cursor-pointer border border-gray-200"
              onClick={() => onSelectProject(project)}
            >
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg font-semibold text-gray-900 line-clamp-1">
                    {project.name}
                  </CardTitle>
                  <div className="flex space-x-1">
                    <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded">
                      {project.session_count} sessions
                    </span>
                  </div>
                </div>
                {project.description && (
                  <p className="text-sm text-gray-600 line-clamp-2 mt-1">
                    {project.description}
                  </p>
                )}
              </CardHeader>

              <CardContent className="pt-2">
                {/* Tags */}
                {project.tags && project.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {project.tags.slice(0, 3).map((tag, index) => (
                      <span 
                        key={index}
                        className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                    {project.tags.length > 3 && (
                      <span className="text-xs text-gray-500">
                        +{project.tags.length - 3} more
                      </span>
                    )}
                  </div>
                )}

                {/* Latest Session */}
                {project.latest_session && (
                  <div className="bg-gray-50 rounded-lg p-3 mb-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(project.latest_session.status)}
                        <span className="text-sm font-medium text-gray-900">
                          {project.latest_session.name}
                        </span>
                      </div>
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          onLoadSession(project.latest_session!.id, project.id);
                        }}
                        size="sm"
                        className="text-xs bg-green-600 hover:bg-green-700"
                      >
                        Continue
                      </Button>
                    </div>
                    
                    {/* Progress bar */}
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${project.latest_session.completion_percentage}%` }}
                      ></div>
                    </div>
                    
                    <div className="flex justify-between items-center text-xs text-gray-600">
                      <span>{project.latest_session.completion_percentage}% complete</span>
                      <span>Updated {formatDate(project.latest_session.updated_at)}</span>
                    </div>
                  </div>
                )}

                {/* Project metadata */}
                <div className="space-y-2 text-xs text-gray-500">
                  <div className="flex items-center space-x-2">
                    <Calendar className="h-3 w-3" />
                    <span>Created {formatDate(project.created_at)}</span>
                  </div>
                  {project.created_by && (
                    <div className="flex items-center space-x-2">
                      <span>👤</span>
                      <span>by {project.created_by}</span>
                    </div>
                  )}
                </div>

                {/* Action buttons */}
                <div className="flex space-x-2 mt-4">
                  <Button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectProject(project);
                    }}
                    size="sm"
                    variant="outline"
                    className="flex-1 text-xs"
                  >
                    <GitBranch className="h-3 w-3 mr-1" />
                    View Sessions
                  </Button>
                  <Button
                    onClick={(e) => {
                      e.stopPropagation();
                      // TODO: Quick start new session
                    }}
                    size="sm"
                    className="flex-1 text-xs bg-blue-600 hover:bg-blue-700"
                  >
                    <Target className="h-3 w-3 mr-1" />
                    New Analysis
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
