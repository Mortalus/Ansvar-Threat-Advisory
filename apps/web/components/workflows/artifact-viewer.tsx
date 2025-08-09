'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Download,
  Eye,
  FileJson,
  FileText,
  File,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Package,
  Clock,
  Database
} from 'lucide-react';

interface Artifact {
  id: string;
  name: string;
  artifact_type: 'json' | 'text' | 'binary';
  version: number;
  is_latest: boolean;
  size?: number;
  created_at: string;
  content?: any;
}

interface ArtifactViewerProps {
  runId: string;
  stepId?: string;
  className?: string;
}

export function ArtifactViewer({ runId, stepId, className = '' }: ArtifactViewerProps) {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);
  const [expandedContent, setExpandedContent] = useState(false);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchArtifacts();
  }, [runId, stepId]);

  const fetchArtifacts = async () => {
    try {
      setLoading(true);
      // This endpoint would need to be implemented
      const url = stepId 
        ? `/api/phase2/workflow/runs/${runId}/steps/${stepId}/artifacts`
        : `/api/phase2/workflow/runs/${runId}/artifacts`;
      
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setArtifacts(data);
        if (data.length > 0 && !selectedArtifact) {
          setSelectedArtifact(data[0]);
        }
      }
    } catch (err) {
      console.error('Error fetching artifacts:', err);
    } finally {
      setLoading(false);
    }
  };

  const downloadArtifact = (artifact: Artifact) => {
    // Create download based on artifact type
    let content: string;
    let mimeType: string;
    
    switch (artifact.artifact_type) {
      case 'json':
        content = JSON.stringify(artifact.content, null, 2);
        mimeType = 'application/json';
        break;
      case 'text':
        content = artifact.content;
        mimeType = 'text/plain';
        break;
      default:
        content = artifact.content;
        mimeType = 'application/octet-stream';
    }
    
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${artifact.name}_v${artifact.version}.${artifact.artifact_type}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = (content: any) => {
    const text = typeof content === 'string' 
      ? content 
      : JSON.stringify(content, null, 2);
    
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getArtifactIcon = (type: string) => {
    switch (type) {
      case 'json':
        return <FileJson className="h-4 w-4" />;
      case 'text':
        return <FileText className="h-4 w-4" />;
      default:
        return <File className="h-4 w-4" />;
    }
  };

  const formatSize = (bytes?: number) => {
    if (!bytes) return 'Unknown';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const renderContent = (artifact: Artifact) => {
    if (!artifact.content) {
      return (
        <div className="text-center py-8 text-gray-500">
          <Database className="h-8 w-8 mx-auto mb-2" />
          <p>Content not loaded</p>
        </div>
      );
    }

    const content = artifact.content;
    const isJson = artifact.artifact_type === 'json';
    const displayContent = isJson 
      ? JSON.stringify(content, null, 2)
      : content.toString();

    const lines = displayContent.split('\n');
    const shouldTruncate = lines.length > 20;
    const visibleContent = expandedContent || !shouldTruncate
      ? displayContent
      : lines.slice(0, 20).join('\n') + '\n...';

    return (
      <div className="relative">
        <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm">
          <code>{visibleContent}</code>
        </pre>
        
        {shouldTruncate && (
          <Button
            variant="ghost"
            size="sm"
            className="mt-2"
            onClick={() => setExpandedContent(!expandedContent)}
          >
            {expandedContent ? (
              <>
                <ChevronUp className="mr-1 h-4 w-4" />
                Show Less
              </>
            ) : (
              <>
                <ChevronDown className="mr-1 h-4 w-4" />
                Show More ({lines.length - 20} more lines)
              </>
            )}
          </Button>
        )}
        
        <div className="absolute top-2 right-2 flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => copyToClipboard(content)}
          >
            {copied ? (
              <Check className="h-4 w-4 text-green-500" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => downloadArtifact(artifact)}
          >
            <Download className="h-4 w-4" />
          </Button>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="text-center py-8">
          <Package className="h-8 w-8 mx-auto text-gray-400 animate-pulse" />
          <p className="mt-2 text-gray-500">Loading artifacts...</p>
        </CardContent>
      </Card>
    );
  }

  if (artifacts.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="text-center py-8">
          <Package className="h-8 w-8 mx-auto text-gray-300" />
          <p className="mt-2 text-gray-500">No artifacts available</p>
          <p className="text-sm text-gray-400 mt-1">
            Artifacts will appear here as workflow steps complete
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Package className="h-5 w-5" />
          Workflow Artifacts
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Artifact List */}
          <div className="lg:col-span-1 space-y-2">
            <h3 className="text-sm font-medium text-gray-600 mb-2">
              Available Artifacts ({artifacts.length})
            </h3>
            {artifacts.map((artifact) => (
              <div
                key={artifact.id}
                className={`p-3 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
                  selectedArtifact?.id === artifact.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200'
                }`}
                onClick={() => setSelectedArtifact(artifact)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-2">
                    {getArtifactIcon(artifact.artifact_type)}
                    <div>
                      <p className="font-medium text-sm">{artifact.name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-xs">
                          v{artifact.version}
                        </Badge>
                        {artifact.is_latest && (
                          <Badge className="text-xs bg-green-100 text-green-800">
                            Latest
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  <Eye className="h-4 w-4 text-gray-400" />
                </div>
                
                <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                  <span>{formatSize(artifact.size)}</span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(artifact.created_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
          
          {/* Artifact Content Viewer */}
          <div className="lg:col-span-2">
            {selectedArtifact ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">{selectedArtifact.name}</h3>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">
                      {selectedArtifact.artifact_type}
                    </Badge>
                    <Badge variant="outline">
                      v{selectedArtifact.version}
                    </Badge>
                  </div>
                </div>
                
                {renderContent(selectedArtifact)}
                
                <div className="pt-4 border-t flex items-center justify-between text-sm text-gray-500">
                  <span>Created: {new Date(selectedArtifact.created_at).toLocaleString()}</span>
                  <span>Size: {formatSize(selectedArtifact.size)}</span>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Eye className="h-8 w-8 mx-auto mb-2" />
                <p>Select an artifact to view its content</p>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default ArtifactViewer;