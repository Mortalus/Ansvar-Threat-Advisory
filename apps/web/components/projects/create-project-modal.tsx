"use client";

import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { X, Plus, Trash2, Tag } from 'lucide-react';

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateProject: (projectData: ProjectData) => Promise<void>;
}

interface ProjectData {
  name: string;
  description: string;
  tags: string[];
  created_by?: string;
}

export default function CreateProjectModal({ 
  isOpen, 
  onClose, 
  onCreateProject 
}: CreateProjectModalProps) {
  const [formData, setFormData] = useState<ProjectData>({
    name: '',
    description: '',
    tags: [],
    created_by: ''
  });
  const [newTag, setNewTag] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Reset form when modal opens/closes
  React.useEffect(() => {
    if (isOpen) {
      setFormData({
        name: '',
        description: '',
        tags: [],
        created_by: ''
      });
      setNewTag('');
      setErrors({});
    }
  }, [isOpen]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Project name is required';
    } else if (formData.name.length < 3) {
      newErrors.name = 'Project name must be at least 3 characters';
    } else if (formData.name.length > 255) {
      newErrors.name = 'Project name must be less than 255 characters';
    }

    if (formData.description.length > 1000) {
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
      console.log('🚀 Creating project:', formData);
      
      await onCreateProject(formData);
      console.log('✅ Project created successfully');
      onClose();
      
    } catch (error) {
      console.error('❌ Failed to create project:', error);
      setErrors({ 
        submit: error instanceof Error ? error.message : 'Failed to create project' 
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const addTag = () => {
    const tag = newTag.trim();
    if (tag && !formData.tags.includes(tag) && formData.tags.length < 10) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tag]
      }));
      setNewTag('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleKeyPress = (e: React.KeyboardEvent, action: () => void) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      action();
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
            <span>🆕</span>
            <span>Create New Project</span>
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
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Project Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Project Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., E-commerce Platform Security Analysis"
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  errors.name ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={isSubmitting}
              />
              {errors.name && (
                <p className="text-sm text-red-600 mt-1">{errors.name}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe the system or application you want to analyze for security threats..."
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
                  {formData.description.length}/1000 characters
                </p>
              </div>
            </div>

            {/* Created By */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Created By (Optional)
              </label>
              <input
                type="text"
                value={formData.created_by}
                onChange={(e) => setFormData(prev => ({ ...prev, created_by: e.target.value }))}
                placeholder="Your name or team name"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isSubmitting}
              />
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tags (Optional)
              </label>
              <div className="space-y-3">
                {/* Add new tag */}
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={(e) => handleKeyPress(e, addTag)}
                    placeholder="Add a tag (e.g., web-app, mobile, api)"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isSubmitting || formData.tags.length >= 10}
                  />
                  <Button
                    type="button"
                    onClick={addTag}
                    disabled={!newTag.trim() || formData.tags.includes(newTag.trim()) || formData.tags.length >= 10}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>

                {/* Display tags */}
                {formData.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {formData.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center space-x-1 bg-blue-100 text-blue-800 text-sm px-3 py-1 rounded-full"
                      >
                        <Tag className="h-3 w-3" />
                        <span>{tag}</span>
                        <button
                          type="button"
                          onClick={() => removeTag(tag)}
                          className="hover:bg-blue-200 rounded-full p-0.5 ml-1"
                          disabled={isSubmitting}
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}

                <p className="text-sm text-gray-500">
                  Tags help organize and categorize your projects ({formData.tags.length}/10)
                </p>
              </div>
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
                className="bg-blue-600 hover:bg-blue-700"
              >
                {isSubmitting ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Creating...</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <Plus className="h-4 w-4" />
                    <span>Create Project</span>
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
