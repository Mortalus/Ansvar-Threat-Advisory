import React, { useState } from 'react';
import { Workflow, Play, Clock, Users, Shield, FileText } from 'lucide-react';
import { Workflow as WorkflowType } from '../types';

interface WorkflowsViewProps {
  workflows: WorkflowType[];
  onWorkflowClick: (workflow: WorkflowType) => void;
}

export function WorkflowsView({ workflows, onWorkflowClick }: WorkflowsViewProps) {
  const [filter, setFilter] = useState('all');
  
  const filteredWorkflows = filter === 'all' 
    ? workflows 
    : workflows.filter(workflow => filter === 'template' ? workflow.isTemplate : !workflow.isTemplate);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Security Workflows</h1>
          <p className="text-gray-600 mt-2">Modular AI-powered workflows for automated security analysis and threat detection</p>
        </div>
        <button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg hover:shadow-lg transition-all duration-200">
          Create Workflow
        </button>
      </div>

      {/* Filters */}
      <div className="flex space-x-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            filter === 'all'
              ? 'bg-purple-100 text-purple-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFilter('template')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            filter === 'template'
              ? 'bg-purple-100 text-purple-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Templates
        </button>
        <button
          onClick={() => setFilter('custom')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            filter === 'custom'
              ? 'bg-purple-100 text-purple-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Custom
        </button>
      </div>

      {/* Workflows Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredWorkflows.map(workflow => (
          <div
            key={workflow.id}
            onClick={() => onWorkflowClick(workflow)}
            className={`bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg hover:border-purple-300 transition-all duration-200 cursor-pointer group ${
              workflow.name === 'Threat Modeling Pipeline' ? 'ring-2 ring-purple-200 bg-gradient-to-br from-purple-50 to-blue-50' : ''
            }`}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                  workflow.name === 'Threat Modeling Pipeline' 
                    ? 'bg-gradient-to-r from-red-500 to-orange-500' 
                    : 'bg-gradient-to-r from-blue-500 to-purple-500'
                }`}>
                  {workflow.name === 'Threat Modeling Pipeline' ? (
                    <Shield className="w-6 h-6 text-white" />
                  ) : (
                    <Workflow className="w-6 h-6 text-white" />
                  )}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 group-hover:text-purple-700 transition-colors">
                    {workflow.name}
                  </h3>
                  <div className="flex items-center space-x-2 mt-1">
                    {workflow.isTemplate && (
                      <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                        Template
                      </span>
                    )}
                    {workflow.name === 'Threat Modeling Pipeline' && (
                      <span className="text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
                        Security
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <p className="text-gray-600 text-sm mb-4 line-clamp-3">{workflow.description}</p>

            <div className="flex items-center space-x-4 text-sm text-gray-500 mb-4">
              <div className="flex items-center space-x-1">
                <Users className="w-4 h-4" />
                <span>{workflow.steps.length} steps</span>
              </div>
              <div className="flex items-center space-x-1">
                <FileText className="w-4 h-4" />
                <span>{workflow.steps.filter(s => s.type === 'agent').length} agents</span>
              </div>
              <div className="flex items-center space-x-1">
                <Clock className="w-4 h-4" />
                <span>{new Date(workflow.createdAt).toLocaleDateString()}</span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
              <div className="flex -space-x-2">
                {workflow.steps.filter(s => s.type === 'agent').slice(0, 3).map((step, index) => (
                  <div
                    key={step.id}
                    className={`w-8 h-8 rounded-full border-2 border-white flex items-center justify-center ${
                      workflow.name === 'Threat Modeling Pipeline'
                        ? 'bg-gradient-to-r from-red-400 to-orange-400'
                        : 'bg-gradient-to-r from-purple-400 to-blue-400'
                    }`}
                    style={{ zIndex: 3 - index }}
                  >
                    <span className="text-xs text-white font-medium">{index + 1}</span>
                  </div>
                ))}
                {workflow.steps.filter((s) => s.type === 'agent').length > 3 && (
                  <div className="w-8 h-8 bg-gray-200 rounded-full border-2 border-white flex items-center justify-center">
                    <span className="text-xs text-gray-600">+{workflow.steps.filter((s) => s.type === 'agent').length - 3}</span>
                  </div>
                )}
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  // Run workflow
                }}
                className="p-2 rounded-lg hover:bg-green-100 text-green-600"
              >
                <Play className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}