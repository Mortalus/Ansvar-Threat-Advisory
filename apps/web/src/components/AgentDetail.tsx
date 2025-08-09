import React, { useState } from 'react';
import { ArrowLeft, Save, Bot, Settings, Activity, Edit3 } from 'lucide-react';
import { Agent } from '../types';
import { SystemPromptModal } from './SystemPromptModal';

interface AgentDetailProps {
  agent: Agent;
  onBack: () => void;
  onSave: (agent: Agent) => void;
}

export function AgentDetail({ agent, onBack, onSave }: AgentDetailProps) {
  const [editedAgent, setEditedAgent] = useState<Agent>(agent);
  const [activeTab, setActiveTab] = useState('overview');
  const [showSystemPromptModal, setShowSystemPromptModal] = useState(false);

  const handleSave = () => {
    onSave(editedAgent);
  };

  const handleSystemPromptSave = (systemPrompt: string, capabilities: string[]) => {
    setEditedAgent(prev => ({
      ...prev,
      systemPrompt,
      capabilities
    }));
  };

  const updateSettings = (key: string, value: any) => {
    setEditedAgent(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        [key]: value
      }
    }));
  };

  const getSupportedInputTypes = (agentName: string) => {
    switch (agentName) {
      case 'DFD Generator':
        return [
          { name: 'Documents', description: 'System documentation and requirements' },
          { name: 'Architecture Files', description: 'System architecture descriptions' },
          { name: 'Specifications', description: 'Technical specifications and designs' }
        ];
      case 'DFD Quality Checker':
        return [
          { name: 'DFD JSON', description: 'Data Flow Diagram in JSON format' },
          { name: 'Source Documents', description: 'Original documents for validation' }
        ];
      case 'Mermaid Diagram Generator':
        return [
          { name: 'DFD Data', description: 'Validated Data Flow Diagram data' },
          { name: 'Structured Data', description: 'Any structured data for visualization' }
        ];
      case 'STRIDE Threat Analyzer':
        return [
          { name: 'DFD Structure', description: 'Data Flow Diagram structure' },
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
  };

  const getSupportedOutputTypes = (agentName: string) => {
    switch (agentName) {
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
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Bot },
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'activity', label: 'Activity', icon: Activity },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={onBack}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{agent.name}</h1>
            <p className="text-gray-600 mt-1">Configure your AI agent</p>
          </div>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleSave}
            className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg hover:shadow-lg transition-all duration-200 flex items-center space-x-2"
          >
            <Save className="w-4 h-4" />
            <span>Save Changes</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 pb-4 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="font-medium">{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
                  <input
                    type="text"
                    value={editedAgent.name}
                    onChange={(e) => setEditedAgent(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                  <textarea
                    value={editedAgent.description}
                    onChange={(e) => setEditedAgent(prev => ({ ...prev, description: e.target.value }))}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
                
                {/* Supported Input/Output Types */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Supported Input Types</label>
                    <div className="space-y-2 max-h-32 overflow-y-auto">
                      {getSupportedInputTypes(editedAgent.name).map((type, index) => (
                        <div key={index} className="flex items-center space-x-2 p-2 bg-blue-50 rounded text-sm">
                          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                          <span className="font-medium text-blue-900">{type.name}</span>
                          <span className="text-blue-700 text-xs">- {type.description}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Expected Output Types</label>
                    <div className="space-y-2 max-h-32 overflow-y-auto">
                      {getSupportedOutputTypes(editedAgent.name).map((type, index) => (
                        <div key={index} className="flex items-center space-x-2 p-2 bg-green-50 rounded text-sm">
                          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                          <span className="font-medium text-green-900">{type.name}</span>
                          <span className="text-green-700 text-xs">- {type.description}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
                  <select
                    value={editedAgent.category}
                    onChange={(e) => setEditedAgent(prev => ({ ...prev, category: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="assistant">Assistant</option>
                    <option value="analyzer">Analyzer</option>
                    <option value="generator">Generator</option>
                    <option value="classifier">Classifier</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">System Prompt & Capabilities</h3>
                <button
                  onClick={() => setShowSystemPromptModal(true)}
                  className="flex items-center space-x-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:shadow-lg transition-all duration-200"
                >
                  <Edit3 className="w-4 h-4" />
                  <span>Edit</span>
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">System Prompt</h4>
                  <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg line-clamp-3">
                    {editedAgent.systemPrompt}
                  </p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Capabilities ({editedAgent.capabilities.length})</h4>
                  <div className="flex flex-wrap gap-2">
                    {editedAgent.capabilities.slice(0, 6).map(capability => (
                      <span key={capability} className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded">
                        {capability}
                      </span>
                    ))}
                    {editedAgent.capabilities.length > 6 && (
                      <span className="text-xs text-gray-500">+{editedAgent.capabilities.length - 6} more</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Status</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Active</span>
                  <div className={`w-3 h-3 rounded-full ${editedAgent.isActive ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Provider</span>
                  <span className="text-sm text-gray-900">{editedAgent.provider}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Created</span>
                  <span className="text-sm text-gray-900">{new Date(editedAgent.createdAt).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Model</span>
                  <span className="text-sm text-gray-900">{editedAgent.settings.model}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'settings' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Configuration</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Model</label>
                <select
                  value={editedAgent.settings.model}
                  onChange={(e) => updateSettings('model', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="gpt-4">GPT-4</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="claude-3-opus">Claude 3 Opus</option>
                  <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                  <option value="claude-3-haiku">Claude 3 Haiku</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Provider</label>
                <select
                  value={editedAgent.provider}
                  onChange={(e) => setEditedAgent(prev => ({ ...prev, provider: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="OpenAI">OpenAI</option>
                  <option value="Anthropic">Anthropic</option>
                  <option value="Google">Google</option>
                  <option value="Cohere">Cohere</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Temperature ({editedAgent.settings.temperature})
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={editedAgent.settings.temperature}
                  onChange={(e) => updateSettings('temperature', parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Max Tokens</label>
                <input
                  type="number"
                  value={editedAgent.settings.maxTokens}
                  onChange={(e) => updateSettings('maxTokens', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Advanced Configuration</h3>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <h4 className="font-medium text-gray-900">Auto-retry on failure</h4>
                  <p className="text-sm text-gray-600">Automatically retry failed requests</p>
                </div>
                <button className="bg-purple-600 relative inline-flex h-6 w-11 items-center rounded-full">
                  <span className="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white transition" />
                </button>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <h4 className="font-medium text-gray-900">Logging enabled</h4>
                  <p className="text-sm text-gray-600">Log all interactions for debugging</p>
                </div>
                <button className="bg-gray-200 relative inline-flex h-6 w-11 items-center rounded-full">
                  <span className="translate-x-1 inline-block h-4 w-4 transform rounded-full bg-white transition" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'activity' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-4">
            <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">Agent configuration updated</p>
                <p className="text-xs text-gray-500">2 hours ago</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">Agent activated</p>
                <p className="text-xs text-gray-500">1 day ago</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">Agent created</p>
                <p className="text-xs text-gray-500">3 days ago</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <SystemPromptModal
        agent={editedAgent}
        isOpen={showSystemPromptModal}
        onClose={() => setShowSystemPromptModal(false)}
        onSave={handleSystemPromptSave}
      />
    </div>
  );
}