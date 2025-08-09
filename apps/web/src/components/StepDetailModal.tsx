import React, { useState } from 'react';
import { X, Bot, Database, Plus, Trash2, Edit3 } from 'lucide-react';
import { WorkflowStep, Agent, ContextSource } from '../types';

interface StepDetailModalProps {
  step: WorkflowStep;
  agent?: Agent;
  contextSources: ContextSource[];
  isOpen: boolean;
  onClose: () => void;
  onUpdateStep: (step: WorkflowStep) => void;
  onEditAgent: (agent: Agent) => void;
}

export function StepDetailModal({ 
  step, 
  agent, 
  contextSources, 
  isOpen, 
  onClose, 
  onUpdateStep, 
  onEditAgent 
}: StepDetailModalProps) {
  const [selectedContextSources, setSelectedContextSources] = useState<string[]>(
    step.contextSources || []
  );
  const [inputData, setInputData] = useState(
    step.inputData ? JSON.stringify(step.inputData, null, 2) : ''
  );
  const [outputData, setOutputData] = useState(
    step.outputData ? JSON.stringify(step.outputData, null, 2) : ''
  );

  if (!isOpen) return null;

  const handleSave = () => {
    const updatedStep: WorkflowStep = {
      ...step,
      contextSources: selectedContextSources,
      inputData: inputData ? JSON.parse(inputData) : undefined,
      outputData: outputData ? JSON.parse(outputData) : undefined
    };
    onUpdateStep(updatedStep);
    onClose();
  };

  const toggleContextSource = (sourceId: string) => {
    setSelectedContextSources(prev => 
      prev.includes(sourceId) 
        ? prev.filter(id => id !== sourceId)
        : [...prev, sourceId]
    );
  };

  const getSupportedInputTypes = (stepType: string, agent?: Agent) => {
    if (stepType === 'input') {
      return [
        { name: 'Documents', description: 'PDF, DOC, DOCX, TXT, MD files' },
        { name: 'Web URLs', description: 'Links to web pages and online documents' },
        { name: 'Data Files', description: 'CSV, JSON, XML, YAML files' },
        { name: 'Images', description: 'PNG, JPG, SVG files for analysis' }
      ];
    }
    
    if (stepType === 'agent' && agent) {
      switch (agent.name) {
        case 'DFD Generator':
          return [
            { name: 'Text Documents', description: 'System documentation and requirements' },
            { name: 'Architecture Files', description: 'System architecture descriptions' },
            { name: 'Specification Files', description: 'Technical specifications and designs' }
          ];
        case 'DFD Quality Checker':
          return [
            { name: 'DFD JSON', description: 'Data Flow Diagram in JSON format' },
            { name: 'Original Documents', description: 'Source documents for validation' }
          ];
        case 'Mermaid Diagram Generator':
          return [
            { name: 'DFD JSON', description: 'Validated Data Flow Diagram data' },
            { name: 'Structured Data', description: 'Any structured data for visualization' }
          ];
        case 'STRIDE Threat Analyzer':
          return [
            { name: 'DFD Data', description: 'Data Flow Diagram structure' },
            { name: 'System Context', description: 'System boundaries and components' }
          ];
        case 'Business Risk Assessor':
          return [
            { name: 'Threat Analysis', description: 'STRIDE analysis results' },
            { name: 'Business Context', description: 'Business requirements and constraints' }
          ];
        case 'Attack Path Generator':
          return [
            { name: 'Risk Assessment', description: 'Business-contextualized threats' },
            { name: 'System Architecture', description: 'System components and relationships' }
          ];
        default:
          return [
            { name: 'Text Data', description: 'Plain text input for processing' },
            { name: 'Structured Data', description: 'JSON, XML, or other structured formats' }
          ];
      }
    }
    
    return [
      { name: 'Previous Step Output', description: 'Output from the previous workflow step' }
    ];
  };

  const getSupportedOutputTypes = (stepType: string, agent?: Agent) => {
    if (stepType === 'output') {
      return [
        { name: 'Final Report', description: 'Complete analysis results' },
        { name: 'Structured Data', description: 'Processed data in various formats' },
        { name: 'Visualizations', description: 'Charts, diagrams, and visual outputs' }
      ];
    }
    
    if (stepType === 'agent' && agent) {
      switch (agent.name) {
        case 'DFD Generator':
          return [
            { name: 'DFD JSON', description: 'Data Flow Diagram in structured JSON format' },
            { name: 'Component List', description: 'List of identified system components' }
          ];
        case 'DFD Quality Checker':
          return [
            { name: 'Validated DFD', description: 'Quality-checked and improved DFD' },
            { name: 'Quality Report', description: 'Validation results and improvements' }
          ];
        case 'Mermaid Diagram Generator':
          return [
            { name: 'Mermaid Code', description: 'Diagram code for visual rendering' },
            { name: 'SVG Diagram', description: 'Rendered diagram in SVG format' }
          ];
        case 'STRIDE Threat Analyzer':
          return [
            { name: 'Threat List', description: 'Identified threats using STRIDE methodology' },
            { name: 'Risk Matrix', description: 'Threat categorization and severity' }
          ];
        case 'Business Risk Assessor':
          return [
            { name: 'Risk Assessment', description: 'Business-contextualized risk analysis' },
            { name: 'Priority Matrix', description: 'Threat prioritization for business' }
          ];
        case 'Attack Path Generator':
          return [
            { name: 'Attack Paths', description: 'Detailed attack scenarios and paths' },
            { name: 'Mitigation Strategies', description: 'Recommended security controls' }
          ];
        default:
          return [
            { name: 'Processed Text', description: 'Analyzed and processed text output' },
            { name: 'Structured Results', description: 'Results in JSON or other formats' }
          ];
      }
    }
    
    return [
      { name: 'Step Output', description: 'Processed data for next workflow step' }
    ];
  };

  const getContextSourceIcon = (type: string) => {
    switch (type) {
      case 'rag_database': return Database;
      case 'document': return Edit3;
      case 'web_search': return Bot;
      default: return Database;
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Step Details: {step.name}</h2>
            <p className="text-gray-600 mt-1">{step.description}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column */}
            <div className="space-y-6">
              {/* Agent Information */}
              {agent && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Connected Agent</h3>
                    <button
                      onClick={() => onEditAgent(agent)}
                      className="flex items-center space-x-2 bg-purple-600 text-white px-3 py-1 rounded-lg hover:bg-purple-700 transition-colors"
                    >
                      <Edit3 className="w-4 h-4" />
                      <span>Edit Agent</span>
                    </button>
                  </div>
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">{agent.name}</h4>
                      <p className="text-sm text-gray-600">{agent.provider} - {agent.settings.model}</p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{agent.description}</p>
                  <div className="text-xs text-gray-500">
                    <strong>System Prompt Preview:</strong>
                    <p className="mt-1 line-clamp-3">{agent.systemPrompt}</p>
                  </div>
                </div>
              )}

              {/* Context Sources */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Context Sources</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Select additional data sources to provide context for this step.
                </p>
                
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {contextSources.map(source => {
                    const Icon = getContextSourceIcon(source.type);
                    const isSelected = selectedContextSources.includes(source.id);
                    const isInTemplate = agent?.contextSources?.includes(source.id) || false;
                    
                    return (
                      <div
                        key={source.id}
                        onClick={() => toggleContextSource(source.id)}
                        className={`flex items-center space-x-3 p-3 rounded-lg border transition-colors ${
                          isInTemplate ? 'bg-gray-100 border-gray-200 cursor-not-allowed opacity-60' :
                          isSelected 
                            ? 'border-purple-300 bg-purple-50 cursor-pointer' 
                            : 'border-gray-200 hover:border-gray-300 cursor-pointer'
                        }`}
                      >
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                          source.type === 'rag_database' ? 'bg-purple-500' :
                          source.type === 'document' ? 'bg-blue-500' :
                          source.type === 'web_search' ? 'bg-green-500' : 'bg-gray-500'
                        }`}>
                          <Icon className="w-4 h-4 text-white" />
                        </div>
                        <div className="flex-1">
                          <h4 className="text-sm font-medium text-gray-900">{source.name}</h4>
                          <p className="text-xs text-gray-600 capitalize">
                            {source.type.replace('_', ' ')} {isInTemplate && '(from template)'}
                          </p>
                        </div>
                        <div className={`w-4 h-4 rounded border-2 ${
                          isInTemplate ? 'bg-gray-300 border-gray-300' :
                          isSelected ? 'bg-purple-600 border-purple-600' : 'border-gray-300'
                        }`}>
                          {(isSelected || isInTemplate) && (
                            <div className="w-full h-full flex items-center justify-center">
                              <div className={`w-2 h-2 rounded-full ${isInTemplate ? 'bg-gray-500' : 'bg-white'}`}></div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-6">
              {/* Supported Input Types */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Supported Input Types</h3>
                <div className="space-y-3">
                  {getSupportedInputTypes(step.type, agent).map((type, index) => (
                    <div key={index} className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <div>
                        <p className="text-sm font-medium text-blue-900">{type.name}</p>
                        <p className="text-xs text-blue-700">{type.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Expected Output Types */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Expected Output Types</h3>
                <div className="space-y-3">
                  {getSupportedOutputTypes(step.type, agent).map((type, index) => (
                    <div key={index} className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <div>
                        <p className="text-sm font-medium text-green-900">{type.name}</p>
                        <p className="text-xs text-green-700">{type.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-2 rounded-lg hover:shadow-lg transition-all duration-200"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}