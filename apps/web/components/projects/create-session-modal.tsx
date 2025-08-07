"use client";

import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { X, Plus, GitBranch, Target } from 'lucide-react';

interface CreateSessionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateSession: (sessionData: SessionData) => Promise<void>;
  projectId: string;
  projectName: string;
  parentSession?: {
    id: string;
    name: string;
  };
  branchPoint?: string;
}

interface SessionData {
  project_id: string;
  name: string;
  description?: string;
  parent_session_id?: string;
  branch_point?: string;
}

export default function CreateSessionModal({ 
  isOpen, 
  onClose, 
  onCreateSession,
  projectId,
  projectName,
  parentSession,
  branchPoint
}: CreateSessionModalProps) {
  const [formData, setFormData] = useState<SessionData>({
    project_id: projectId,
    name: '',
    description: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const isBranching = parentSession && branchPoint;

  // Reset form when modal opens/closes
  React.useEffect(() => {
    if (isOpen) {
      setFormData({
        project_id: projectId,
        name: isBranching ? `${parentSession?.name} - Branch` : '',
        description: isBranching ? `Branched from ${parentSession?.name} at ${branchPoint}` : '',
        parent_session_id: parentSession?.id,
        branch_point: branchPoint
      });
      setErrors({});
    }
  }, [isOpen, projectId, parentSession, branchPoint, isBranching]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Session name is required';
    } else if (formData.name.length < 3) {
      newErrors.name = 'Session name must be at least 3 characters';
    } else if (formData.name.length > 255) {
      newErrors.name = 'Session name must be less than 255 characters';
    }

    if (formData.description && formData.description.length > 1000) {
      newErrors.description = 'Description must be less than 1000 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      setIsSubmitting(true);
      console.log('🚀 Creating session:', formData);
      
      await onCreateSession(formData);
      console.log('✅ Session created successfully');
      onClose();
      
    } catch (error) {
      console.error('❌ Failed to create session:', error);
      setErrors({ 
        submit: error instanceof Error ? error.message : 'Failed to create session' 
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const generateSessionNameSuggestions = () => {
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
    
    if (isBranching) {
      return [
        `${parentSession?.name} - Updated Analysis`,
        `${parentSession?.name} - Alternative Approach`,
        `${parentSession?.name} - ${dateStr}`,
      ];
    } else {
      return [
        `Initial Security Analysis`,
        `Threat Assessment - ${dateStr}`,
        `Security Review`,
        `Risk Analysis Session`,
      ];
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="text-xl font-semibold flex items-center space-x-2">
            {isBranching ? (
              <>
                <GitBranch className="h-5 w-5 text-blue-600" />
                <span>Create Session Branch</span>
              </>
            ) : (
              <>
                <Target className="h-5 w-5 text-green-600" />
                <span>Create New Session</span>
              </>
            )}
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>

        <CardContent>
          {/* Project context */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h3 className="font-medium text-gray-900 mb-2">
              📂 Project: {projectName}
            </h3>
            {isBranching && (
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-center space-x-2">
                  <GitBranch className="h-4 w-4" />
                  <span>Branching from: <strong>{parentSession?.name}</strong></span>
                </div>
                <div className="flex items-center space-x-2">
                  <span>📍</span>
                  <span>Branch point: <strong>{branchPoint}</strong></span>
                </div>
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Session Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Session Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Initial Security Analysis"
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  errors.name ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={isSubmitting}
              />
              {errors.name && (
                <p className="text-sm text-red-600 mt-1">{errors.name}</p>
              )}

              {/* Name suggestions */}
              <div className="mt-3">
                <p className="text-sm text-gray-600 mb-2">Quick suggestions:</p>
                <div className="flex flex-wrap gap-2">
                  {generateSessionNameSuggestions().map((suggestion, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, name: suggestion }))}
                      className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded hover:bg-blue-200 transition-colors"
                      disabled={isSubmitting}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description (Optional)
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder={
                  isBranching 
                    ? "Describe what changes or additional analysis you plan to make in this branch..."
                    : "Describe the goals and scope of this threat modeling session..."
                }
                rows={4}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none ${
                  errors.description ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={isSubmitting}
              />
              <div className="flex justify-between items-center mt-1">
                {errors.description && (
                  <p className="text-sm text-red-600">{errors.description}</p>
                )}
                <p className="text-sm text-gray-500 ml-auto">
                  {(formData.description || '').length}/1000 characters
                </p>
              </div>
            </div>

            {/* Information about what happens next */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">
                {isBranching ? '🌿 What happens when you create a branch?' : '🚀 What happens next?'}
              </h4>
              <ul className="text-sm text-blue-800 space-y-1">
                {isBranching ? (
                  <>
                    <li>• A new session will be created with the current state from the parent session</li>
                    <li>• You can modify and continue the analysis independently</li>
                    <li>• The original session remains unchanged</li>
                    <li>• You can compare results between branches later</li>
                  </>
                ) : (
                  <>
                    <li>• A new threat modeling session will be created</li>
                    <li>• You'll be guided through the document upload process</li>
                    <li>• The AI will extract data flow diagrams and generate threats</li>
                    <li>• You can review and refine the analysis at each step</li>
                  </>
                )}
              </ul>
            </div>

            {/* Submit Error */}
            {errors.submit && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-700">{errors.submit}</p>
              </div>
            )}

            {/* Form Actions */}
            <div className="flex justify-end space-x-3 pt-4 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting || !formData.name.trim()}
                className={isBranching ? "bg-blue-600 hover:bg-blue-700" : "bg-green-600 hover:bg-green-700"}
              >
                {isSubmitting ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Creating...</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    {isBranching ? (
                      <>
                        <GitBranch className="h-4 w-4" />
                        <span>Create Branch</span>
                      </>
                    ) : (
                      <>
                        <Plus className="h-4 w-4" />
                        <span>Create Session</span>
                      </>
                    )}
                  </div>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
