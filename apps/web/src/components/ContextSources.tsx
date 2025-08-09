import React, { useState } from 'react';
import { Database, Globe, FileText, Zap, Brain, Plus, Settings, MoreVertical, Edit, Trash2 } from 'lucide-react';
import { ContextSource } from '../types';

const mockContextSources: ContextSource[] = [
  {
    id: '1',
    name: 'Security Knowledge Base',
    type: 'rag_database',
    description: 'Comprehensive cybersecurity knowledge base with threat intelligence and best practices',
    configuration: {
      endpoint: 'https://api.security-kb.com/v1',
      apiKey: '***hidden***',
      parameters: { index: 'security-threats', similarity_threshold: 0.8 }
    },
    isActive: true,
    createdAt: '2024-01-15T10:00:00Z'
  },
  {
    id: '2',
    name: 'NIST Framework Documents',
    type: 'document',
    description: 'NIST Cybersecurity Framework documentation and guidelines',
    configuration: {
      documentPath: '/documents/nist-framework/',
      parameters: { format: 'pdf', version: '1.1' }
    },
    isActive: true,
    createdAt: '2024-01-12T14:30:00Z'
  },
  {
    id: '3',
    name: 'CVE Database Search',
    type: 'web_search',
    description: 'Real-time search of Common Vulnerabilities and Exposures database',
    configuration: {
      endpoint: 'https://cve.mitre.org/api',
      searchQuery: 'recent vulnerabilities',
      parameters: { limit: 50, severity: 'high' }
    },
    isActive: false,
    createdAt: '2024-01-10T09:15:00Z'
  }
];

export function ContextSources() {
  const [contextSources, setContextSources] = useState(mockContextSources);
  const [filter, setFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingSource, setEditingSource] = useState<ContextSource | null>(null);

  const sourceTypes = [
    { id: 'rag_database', label: 'RAG Database', icon: Database, color: 'bg-purple-500' },
    { id: 'document', label: 'Document', icon: FileText, color: 'bg-blue-500' },
    { id: 'web_search', label: 'Web Search', icon: Globe, color: 'bg-green-500' },
    { id: 'api', label: 'API', icon: Zap, color: 'bg-orange-500' },
    { id: 'knowledge_base', label: 'Knowledge Base', icon: Brain, color: 'bg-indigo-500' }
  ];

  const filteredSources = filter === 'all' 
    ? contextSources 
    : contextSources.filter(source => source.type === filter);

  const getSourceIcon = (type: string) => {
    const sourceType = sourceTypes.find(t => t.id === type);
    if (!sourceType) return Database;
    return sourceType.icon;
  };

  const getSourceColor = (type: string) => {
    const sourceType = sourceTypes.find(t => t.id === type);
    return sourceType?.color || 'bg-gray-500';
  };

  const handleEditSource = (source: ContextSource) => {
    setEditingSource(source);
    setShowEditModal(true);
  };

  const handleSaveSource = (updatedSource: ContextSource) => {
    setContextSources(prev => prev.map(s => s.id === updatedSource.id ? updatedSource : s));
    setShowEditModal(false);
    setEditingSource(null);
  };

  const handleDeleteSource = (sourceId: string) => {
    setContextSources(prev => prev.filter(s => s.id !== sourceId));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Knowledge Sources</h1>
          <p className="text-gray-600 mt-2">Manage data sources and knowledge bases for your AI agents on our secure, data-sovereign platform</p>
        </div>
        <button 
          onClick={() => setShowCreateModal(true)}
          className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg hover:shadow-lg transition-all duration-200 flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Add Context Source</span>
        </button>
      </div>

      {/* Source Type Filters */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            filter === 'all'
              ? 'bg-purple-100 text-purple-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          All Sources
        </button>
        {sourceTypes.map(type => {
          const Icon = type.icon;
          return (
            <button
              key={type.id}
              onClick={() => setFilter(type.id)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2 ${
                filter === type.id
                  ? 'bg-purple-100 text-purple-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{type.label}</span>
            </button>
          );
        })}
      </div>

      {/* Context Sources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSources.map(source => {
          const Icon = getSourceIcon(source.type);
          return (
            <div
              key={source.id}
              className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg hover:border-purple-300 transition-all duration-200"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className={`w-12 h-12 ${getSourceColor(source.type)} rounded-lg flex items-center justify-center`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{source.name}</h3>
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded capitalize">
                      {source.type.replace('_', ' ')}
                    </span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${source.isActive ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                  <button className="p-1 rounded hover:bg-gray-100">
                    <Settings className="w-4 h-4 text-gray-600" />
                  </button>
                </div>
              </div>

              <p className="text-gray-600 text-sm mb-4 line-clamp-3">{source.description}</p>

              {/* Configuration Preview */}
              <div className="space-y-2 mb-4">
                {source.configuration.endpoint && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Endpoint:</span>
                    <span className="text-gray-700 truncate ml-2">{source.configuration.endpoint}</span>
                  </div>
                )}
                {source.configuration.documentPath && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Path:</span>
                    <span className="text-gray-700 truncate ml-2">{source.configuration.documentPath}</span>
                  </div>
                )}
                {source.configuration.searchQuery && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Query:</span>
                    <span className="text-gray-700 truncate ml-2">{source.configuration.searchQuery}</span>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                <span className="text-xs text-gray-500">
                  Created {new Date(source.createdAt).toLocaleDateString()}
                </span>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleEditSource(source)}
                    className="flex items-center space-x-1 text-purple-600 hover:text-purple-700 text-sm font-medium"
                  >
                    <Edit className="w-4 h-4" />
                    <span>Edit</span>
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Context Source Modal */}
      {showCreateModal && (
        <CreateContextSourceModal
          sourceTypes={sourceTypes}
          onClose={() => setShowCreateModal(false)}
          onCreate={(newSource) => {
            setContextSources(prev => [...prev, { ...newSource, id: Date.now().toString(), createdAt: new Date().toISOString() }]);
            setShowCreateModal(false);
          }}
        />
      )}

      {/* Edit Context Source Modal */}
      {showEditModal && editingSource && (
        <ContextSourceEditModal
          source={editingSource}
          onSave={handleSaveSource}
          onClose={() => {
            setShowEditModal(false);
            setEditingSource(null);
          }}
          onDelete={handleDeleteSource}
        />
      )}
    </div>
  );
}

interface CreateContextSourceModalProps {
  sourceTypes: any[];
  onClose: () => void;
  onCreate: (source: Partial<ContextSource>) => void;
}

function CreateContextSourceModal({ sourceTypes, onClose, onCreate }: CreateContextSourceModalProps) {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    configuration: {}
  });

  const handleTypeSelect = (typeId: string) => {
    setSelectedType(typeId);
  };

  const handleCreate = () => {
    if (selectedType) {
      onCreate({
        ...formData,
        type: selectedType as any,
        isActive: true
      });
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Add Context Source</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100"
          >
            ×
          </button>
        </div>
        <div className="p-6">
          {!selectedType ? (
            <div className="grid grid-cols-2 gap-4">
              {sourceTypes.map(type => {
                const Icon = type.icon;
                return (
                  <button
                    key={type.id}
                    onClick={() => handleTypeSelect(type.id)}
                    className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition-colors"
                  >
                    <div className={`w-10 h-10 ${type.color} rounded-lg flex items-center justify-center`}>
                      <Icon className="w-5 h-5 text-white" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-medium text-gray-900">{type.label}</h3>
                      <p className="text-sm text-gray-600">Add {type.label.toLowerCase()}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <button
                  onClick={() => setSelectedType(null)}
                  className="text-purple-600 hover:text-purple-700"
                >
                  ← Back
                </button>
                <span className="text-gray-600">Creating {sourceTypes.find(t => t.id === selectedType)?.label}</span>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Enter source name"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Describe this context source"
                />
              </div>
              
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  onClick={onClose}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreate}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:shadow-lg transition-all duration-200"
                >
                  Create Source
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface ContextSourceEditModalProps {
  source: ContextSource;
  onSave: (source: ContextSource) => void;
  onClose: () => void;
  onDelete: (sourceId: string) => void;
}

function ContextSourceEditModal({ source, onSave, onClose, onDelete }: ContextSourceEditModalProps) {
  const [editedSource, setEditedSource] = useState<ContextSource>(source);

  const handleSave = () => {
    onSave(editedSource);
  };

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this context source?')) {
      onDelete(source.id);
      onClose();
    }
  };

  const updateConfiguration = (key: string, value: any) => {
    setEditedSource(prev => ({
      ...prev,
      configuration: {
        ...prev.configuration,
        [key]: value
      }
    }));
  };

  const updateParameters = (key: string, value: any) => {
    setEditedSource(prev => ({
      ...prev,
      configuration: {
        ...prev.configuration,
        parameters: {
          ...prev.configuration.parameters,
          [key]: value
        }
      }
    }));
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Edit Context Source</h2>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100">
            ×
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
                <input
                  type="text"
                  value={editedSource.name}
                  onChange={(e) => setEditedSource(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
                <select
                  value={editedSource.type}
                  onChange={(e) => setEditedSource(prev => ({ ...prev, type: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="rag_database">RAG Database</option>
                  <option value="document">Document</option>
                  <option value="web_search">Web Search</option>
                  <option value="api">API</option>
                  <option value="knowledge_base">Knowledge Base</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
              <textarea
                value={editedSource.description}
                onChange={(e) => setEditedSource(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* Configuration */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Configuration</h3>
              
              {(editedSource.type === 'rag_database' || editedSource.type === 'api') && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Endpoint URL</label>
                    <input
                      type="url"
                      value={editedSource.configuration.endpoint || ''}
                      onChange={(e) => updateConfiguration('endpoint', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="https://api.example.com/v1"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">API Key</label>
                    <input
                      type="password"
                      value={editedSource.configuration.apiKey || ''}
                      onChange={(e) => updateConfiguration('apiKey', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="Enter API key"
                    />
                  </div>
                </>
              )}

              {editedSource.type === 'document' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Document Path</label>
                  <input
                    type="text"
                    value={editedSource.configuration.documentPath || ''}
                    onChange={(e) => updateConfiguration('documentPath', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="/documents/folder/"
                  />
                </div>
              )}

              {editedSource.type === 'web_search' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Default Search Query</label>
                  <input
                    type="text"
                    value={editedSource.configuration.searchQuery || ''}
                    onChange={(e) => updateConfiguration('searchQuery', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="Enter default search terms"
                  />
                </div>
              )}
            </div>

            {/* Parameters */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Parameters</h3>
              
              {editedSource.type === 'rag_database' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Index Name</label>
                    <input
                      type="text"
                      value={editedSource.configuration.parameters?.index || ''}
                      onChange={(e) => updateParameters('index', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="security-threats"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Similarity Threshold</label>
                    <input
                      type="number"
                      min="0"
                      max="1"
                      step="0.1"
                      value={editedSource.configuration.parameters?.similarity_threshold || 0.8}
                      onChange={(e) => updateParameters('similarity_threshold', parseFloat(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>
                </>
              )}

              {editedSource.type === 'web_search' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Results Limit</label>
                    <input
                      type="number"
                      value={editedSource.configuration.parameters?.limit || 10}
                      onChange={(e) => updateParameters('limit', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Severity Filter</label>
                    <select
                      value={editedSource.configuration.parameters?.severity || 'all'}
                      onChange={(e) => updateParameters('severity', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    >
                      <option value="all">All</option>
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>
                </>
              )}
            {/* Status */}
            <div className="flex items-center space-x-3">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={editedSource.isActive}
                  onChange={(e) => setEditedSource(prev => ({ ...prev, isActive: e.target.checked }))}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm font-medium text-gray-700">Active</span>
              </label>
            </div>
          </div>
          </div>
        </div>
        <div className="flex items-center justify-between p-6 border-t border-gray-200">
          <button
            onClick={handleDelete}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2"
          >
            <Trash2 className="w-4 h-4" />
            <span>Delete</span>
          </button>
          <div className="flex space-x-3">
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
    </div>
  );
}