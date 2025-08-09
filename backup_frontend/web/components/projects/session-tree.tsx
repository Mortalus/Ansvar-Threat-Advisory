"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { 
  GitBranch, 
  Play, 
  Archive, 
  CheckCircle, 
  Clock, 
  Plus,
  ArrowRight,
  Target,
  Calendar,
  FileText,
  AlertTriangle,
  MoreVertical,
  Edit,
  Trash2,
  Copy
} from 'lucide-react';

interface Session {
  id: string;
  name: string;
  description?: string;
  status: string;
  completion_percentage: number;
  created_at: string;
  updated_at?: string;
  is_main_branch: boolean;
  branch_point?: string;
  document_name?: string;
  total_threats: number;
  risk_summary?: { [key: string]: number };
  children: Session[];
}

interface SessionTreeProps {
  projectId: string;
  projectName: string;
  sessions: Session[];
  onLoadSession: (sessionId: string) => void;
  onCreateSession: (projectId: string) => void;
  onBranchSession: (sessionId: string, branchPoint: string) => void;
  onDeleteSession?: (sessionId: string) => void;
}

export default function SessionTree({ 
  projectId,
  projectName,
  sessions,
  onLoadSession,
  onCreateSession,
  onBranchSession,
  onDeleteSession
}: SessionTreeProps) {
  const [expandedSessions, setExpandedSessions] = useState<Set<string>>(new Set());
  const [selectedSession, setSelectedSession] = useState<string | null>(null);

  const toggleExpanded = (sessionId: string) => {
    const newExpanded = new Set(expandedSessions);
    if (newExpanded.has(sessionId)) {
      newExpanded.delete(sessionId);
    } else {
      newExpanded.add(sessionId);
    }
    setExpandedSessions(newExpanded);
  };

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

  const getRiskColor = (riskSummary?: { [key: string]: number }) => {
    if (!riskSummary) return 'text-gray-500';
    
    const critical = riskSummary.Critical || 0;
    const high = riskSummary.High || 0;
    
    if (critical > 0) return 'text-red-500';
    if (high > 0) return 'text-orange-500';
    return 'text-green-500';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const renderSession = (session: Session, level: number = 0) => {
    const isExpanded = expandedSessions.has(session.id);
    const hasChildren = session.children && session.children.length > 0;
    const isSelected = selectedSession === session.id;

    return (
      <div key={session.id} className="space-y-2">
        <Card 
          className={`transition-all duration-200 ${
            isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:shadow-md'
          } ${level > 0 ? 'ml-6 border-l-4 border-gray-200' : ''}`}
          style={{ marginLeft: level > 0 ? `${level * 24}px` : '0' }}
        >
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              {/* Session info */}
              <div className="flex items-center space-x-3 flex-1">
                {/* Branch indicator */}
                {level > 0 && (
                  <div className="flex items-center text-gray-400">
                    <GitBranch className="h-3 w-3 mr-1" />
                    <span className="text-xs">{session.branch_point}</span>
                  </div>
                )}

                {/* Status and name */}
                <div className="flex items-center space-x-2">
                  {getStatusIcon(session.status)}
                  <span className={`font-medium ${
                    session.is_main_branch ? 'text-blue-900' : 'text-gray-800'
                  }`}>
                    {session.name}
                    {session.is_main_branch && (
                      <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        main
                      </span>
                    )}
                  </span>
                </div>

                {/* Expand/collapse for children */}
                {hasChildren && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleExpanded(session.id)}
                    className="h-6 w-6 p-0"
                  >
                    <ArrowRight 
                      className={`h-3 w-3 transition-transform ${
                        isExpanded ? 'rotate-90' : ''
                      }`} 
                    />
                  </Button>
                )}
              </div>

              {/* Session metadata */}
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                {/* Progress */}
                <div className="flex items-center space-x-2">
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${session.completion_percentage}%` }}
                    ></div>
                  </div>
                  <span className="text-xs font-medium">
                    {session.completion_percentage}%
                  </span>
                </div>

                {/* Threats count */}
                {session.total_threats > 0 && (
                  <div className="flex items-center space-x-1">
                    <Target className={`h-3 w-3 ${getRiskColor(session.risk_summary)}`} />
                    <span className="text-xs font-medium">
                      {session.total_threats}
                    </span>
                  </div>
                )}

                {/* Last updated */}
                <div className="flex items-center space-x-1">
                  <Calendar className="h-3 w-3" />
                  <span className="text-xs">
                    {formatDate(session.updated_at || session.created_at)}
                  </span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center space-x-2 ml-4">
                <Button
                  size="sm"
                  onClick={() => {
                    setSelectedSession(session.id);
                    onLoadSession(session.id);
                  }}
                  className="text-xs bg-green-600 hover:bg-green-700"
                >
                  {session.status === 'completed' ? 'View' : 'Continue'}
                </Button>

                <div className="relative group">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0"
                  >
                    <MoreVertical className="h-3 w-3" />
                  </Button>
                  
                  {/* Dropdown menu */}
                  <div className="absolute right-0 top-8 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-[150px] opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                    <button
                      onClick={() => onBranchSession(session.id, 'current_state')}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 flex items-center space-x-2"
                    >
                      <GitBranch className="h-3 w-3" />
                      <span>Create Branch</span>
                    </button>
                    
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(session.id);
                      }}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 flex items-center space-x-2"
                    >
                      <Copy className="h-3 w-3" />
                      <span>Copy ID</span>
                    </button>

                    {onDeleteSession && session.status !== 'active' && (
                      <button
                        onClick={() => onDeleteSession(session.id)}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-red-50 text-red-600 flex items-center space-x-2"
                      >
                        <Trash2 className="h-3 w-3" />
                        <span>Delete</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Session description */}
            {session.description && (
              <p className="text-sm text-gray-600 mt-2 ml-6">
                {session.description}
              </p>
            )}

            {/* Document info */}
            {session.document_name && (
              <div className="flex items-center space-x-2 mt-2 ml-6 text-xs text-gray-500">
                <FileText className="h-3 w-3" />
                <span>{session.document_name}</span>
              </div>
            )}

            {/* Risk summary */}
            {session.risk_summary && Object.keys(session.risk_summary).length > 0 && (
              <div className="flex items-center space-x-3 mt-2 ml-6">
                {Object.entries(session.risk_summary).map(([level, count]) => (
                  count > 0 && (
                    <div 
                      key={level}
                      className={`flex items-center space-x-1 text-xs ${
                        level === 'Critical' ? 'text-red-600' :
                        level === 'High' ? 'text-orange-600' :
                        level === 'Medium' ? 'text-yellow-600' :
                        'text-green-600'
                      }`}
                    >
                      <AlertTriangle className="h-3 w-3" />
                      <span>{count} {level}</span>
                    </div>
                  )
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Render children */}
        {hasChildren && isExpanded && (
          <div className="space-y-2">
            {session.children.map(child => renderSession(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            📂 {projectName} Sessions
          </h2>
          <p className="text-gray-600 mt-1">
            Manage threat modeling sessions and their branches
          </p>
        </div>
        <Button 
          onClick={() => onCreateSession(projectId)}
          className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          <span>New Session</span>
        </Button>
      </div>

      {/* Sessions tree */}
      {sessions.length === 0 ? (
        <Card className="border-dashed border-2 border-gray-300">
          <CardContent className="p-8 text-center">
            <GitBranch className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No sessions yet
            </h3>
            <p className="text-gray-600 mb-4">
              Create your first threat modeling session to start analyzing security threats
            </p>
            <Button 
              onClick={() => onCreateSession(projectId)}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create First Session
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {sessions.map(session => renderSession(session))}
        </div>
      )}

      {/* Legend */}
      <Card className="bg-gray-50">
        <CardContent className="p-4">
          <h4 className="font-medium text-gray-900 mb-3">Session Status Legend</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="flex items-center space-x-2">
              <Play className="h-4 w-4 text-blue-500" />
              <span>Active (in progress)</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span>Completed</span>
            </div>
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-yellow-500" />
              <span>Pending</span>
            </div>
            <div className="flex items-center space-x-2">
              <Archive className="h-4 w-4 text-gray-500" />
              <span>Archived</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
