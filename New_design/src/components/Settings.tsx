import React, { useState } from 'react';
import { Plus, Edit, Trash2, Key, Server, Globe, Monitor, Settings as SettingsIcon } from 'lucide-react';
import { LLMProvider } from '../types';

const mockProviders: LLMProvider[] = [
  {
    id: '1',
    name: 'OpenAI GPT-4',
    type: 'openai',
    configuration: {
      apiKey: '***hidden***',
      models: ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo']
    },
    isActive: true,
    createdAt: '2024-01-15T10:00:00Z'
  },
  {
    id: '2',
    name: 'Azure OpenAI',
    type: 'azure',
    configuration: {
      apiKey: '***hidden***',
      endpoint: 'https://myresource.openai.azure.com/',
      region: 'East US',
      models: ['gpt-4', 'gpt-35-turbo']
    },
    isActive: true,
    createdAt: '2024-01-12T14:30:00Z'
  }
];

export function Settings() {
  const [providers, setProviders] = useState(mockProviders);
  const [showProviderModal, setShowProviderModal] = useState(false);
  const [editingProvider, setEditingProvider] = useState<LLMProvider | null>(null);
  const [currentUserRole, setCurrentUserRole] = useState('admin'); // This should come from props in real app
  const [newProvider, setNewProvider] = useState<Partial<LLMProvider>>({
    name: '',
    type: 'openai',
    configuration: {},
    isActive: true
  });

  const providerTypes = [
    { id: 'openai', name: 'OpenAI', icon: Key, color: 'bg-green-500' },
    { id: 'azure', name: 'Azure AI', icon: Server, color: 'bg-blue-500' },
    { id: 'scaleway', name: 'Scaleway', icon: Globe, color: 'bg-purple-500' },
    { id: 'ollama', name: 'Local Ollama', icon: Monitor, color: 'bg-orange-500' },
    { id: 'custom', name: 'Custom', icon: SettingsIcon, color: 'bg-gray-500' }
  ];

  const getProviderIcon = (type: string) => {
    const providerType = providerTypes.find(p => p.id === type);
    return providerType?.icon || Key;
  };

  const getProviderColor = (type: string) => {
    const providerType = providerTypes.find(p => p.id === type);
    return providerType?.color || 'bg-gray-500';
  };

  const handleSaveProvider = () => {
    if (editingProvider) {
      setProviders(prev => prev.map(p => p.id === editingProvider.id ? { ...editingProvider } : p));
    } else {
      const provider: LLMProvider = {
        ...newProvider as LLMProvider,
        id: Date.now().toString(),
        createdAt: new Date().toISOString()
      };
      setProviders(prev => [...prev, provider]);
    }
    setShowProviderModal(false);
    setEditingProvider(null);
    setNewProvider({ name: '', type: 'openai', configuration: {}, isActive: true });
  };

  const handleEditProvider = (provider: LLMProvider) => {
    setEditingProvider(provider);
    setShowProviderModal(true);
  };

  const handleDeleteProvider = (providerId: string) => {
    setProviders(prev => prev.filter(p => p.id !== providerId));
  };

  const renderProviderForm = () => {
    const provider = editingProvider || newProvider;
    const updateProvider = (updates: Partial<LLMProvider>) => {
      if (editingProvider) {
        setEditingProvider({ ...editingProvider, ...updates });
      } else {
        setNewProvider({ ...newProvider, ...updates });
      }
    };

    return (
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Provider Name</label>
          <input
            type="text"
            value={provider.name}
            onChange={(e) => updateProvider({ name: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            placeholder="Enter provider name"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Provider Type</label>
          <select
            value={provider.type}
            onChange={(e) => updateProvider({ type: e.target.value as any })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            {providerTypes.map(type => (
              <option key={type.id} value={type.id}>{type.name}</option>
            ))}
          </select>
        </div>

        {provider.type !== 'ollama' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">API Key</label>
            <input
              type="password"
              value={provider.configuration?.apiKey || ''}
              onChange={(e) => updateProvider({ 
                configuration: { ...provider.configuration, apiKey: e.target.value }
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Enter API key"
            />
          </div>
        )}

        {(provider.type === 'azure' || provider.type === 'custom' || provider.type === 'ollama' || provider.type === 'scaleway') && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Endpoint URL</label>
            <input
              type="url"
              value={provider.configuration?.endpoint || ''}
              onChange={(e) => updateProvider({ 
                configuration: { ...provider.configuration, endpoint: e.target.value }
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder={
                provider.type === 'ollama' ? 'http://localhost:11434' :
                provider.type === 'scaleway' ? 'https://api.scaleway.ai/v1' :
                'Enter endpoint URL'
              }
            />
          </div>
        )}

        {provider.type === 'azure' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Region</label>
            <input
              type="text"
              value={provider.configuration?.region || ''}
              onChange={(e) => updateProvider({ 
                configuration: { ...provider.configuration, region: e.target.value }
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="e.g., East US"
            />
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Available Models (comma-separated)</label>
          <input
            type="text"
            value={provider.configuration?.models?.join(', ') || ''}
            onChange={(e) => updateProvider({ 
              configuration: { 
                ...provider.configuration, 
                models: e.target.value.split(',').map(m => m.trim()).filter(Boolean)
              }
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            placeholder={
              provider.type === 'openai' ? 'gpt-4, gpt-3.5-turbo, gpt-4-turbo' :
              provider.type === 'azure' ? 'gpt-4, gpt-35-turbo' :
              provider.type === 'scaleway' ? 'llama-3-8b, llama-3-70b' :
              provider.type === 'ollama' ? 'llama2, codellama, mistral' :
              'Enter available models'
            }
          />
        </div>

        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="isActive"
            checked={provider.isActive}
            onChange={(e) => updateProvider({ isActive: e.target.checked })}
            className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
          />
          <label htmlFor="isActive" className="text-sm font-medium text-gray-700">
            Active Provider
          </label>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Platform Settings</h1>
        <p className="text-gray-600 mt-2">Configure your data-sovereign platform preferences and AI model providers</p>
      </div>

      {/* LLM Providers */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">LLM Providers</h2>
          {(currentUserRole === 'admin' || currentUserRole === 'user') && (
            <button
              onClick={() => setShowProviderModal(true)}
              className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:shadow-lg transition-all duration-200 flex items-center space-x-2"
            >
              <Plus className="w-4 h-4" />
              <span>Add Provider</span>
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {providers.map(provider => {
            const Icon = getProviderIcon(provider.type);
            return (
              <div key={provider.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 ${getProviderColor(provider.type)} rounded-lg flex items-center justify-center`}>
                      <Icon className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">{provider.name}</h3>
                      <p className="text-sm text-gray-600 capitalize">{provider.type}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${provider.isActive ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                    {(currentUserRole === 'admin' || currentUserRole === 'user') && (
                      <>
                        <button
                          onClick={() => handleEditProvider(provider)}
                          className="p-1 rounded hover:bg-gray-100 text-gray-600"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteProvider(provider.id)}
                          className="p-1 rounded hover:bg-red-100 text-red-600"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
                
                <div className="text-sm text-gray-600">
                  {provider.configuration.models && (
                    <p>Models: {provider.configuration.models.slice(0, 2).join(', ')}
                      {provider.configuration.models.length > 2 && ` +${provider.configuration.models.length - 2} more`}
                    </p>
                  )}
                  {provider.configuration.endpoint && (
                    <p className="truncate">Endpoint: {provider.configuration.endpoint}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* General Settings */}
      {/* Chat Settings */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Chat with Documents Settings</h2>
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Enabled Providers for Chat</h3>
            <p className="text-sm text-gray-600 mb-4">
              Select which LLM providers can be used for document chat functionality
            </p>
            <div className="space-y-3">
              {providers.map(provider => (
                <div key={provider.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 ${getProviderColor(provider.type)} rounded-lg flex items-center justify-center`}>
                      {React.createElement(getProviderIcon(provider.type), { className: "w-5 h-5 text-white" })}
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">{provider.name}</h4>
                      <p className="text-sm text-gray-600">
                        {provider.configuration.models?.length || 0} models available
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-sm text-gray-600">
                      {provider.isActive ? 'Active' : 'Inactive'}
                    </span>
                    <button 
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        provider.isActive ? 'bg-purple-600' : 'bg-gray-200'
                      }`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        provider.isActive ? 'translate-x-6' : 'translate-x-1'
                      }`} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Default Model</label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent">
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                <option value="claude-3-opus">Claude 3 Opus</option>
                <option value="claude-3-sonnet">Claude 3 Sonnet</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Max Tokens per Chat</label>
              <input
                type="number"
                defaultValue="4096"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Temperature (0.0 - 1.0)
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              defaultValue="0.7"
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>More Focused</span>
              <span>More Creative</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">General Settings</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-medium text-gray-900">Dark Mode</h4>
              <p className="text-sm text-gray-600">Switch to dark theme</p>
            </div>
            <button className="bg-gray-200 relative inline-flex h-6 w-11 items-center rounded-full">
              <span className="translate-x-1 inline-block h-4 w-4 transform rounded-full bg-white transition" />
            </button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-medium text-gray-900">Notifications</h4>
              <p className="text-sm text-gray-600">Receive workflow notifications</p>
            </div>
            <button className="bg-purple-600 relative inline-flex h-6 w-11 items-center rounded-full">
              <span className="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white transition" />
            </button>
          </div>
        </div>
      </div>

      {/* Provider Modal */}
      {showProviderModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">
                {editingProvider ? 'Edit Provider' : 'Add LLM Provider'}
              </h2>
              <button
                onClick={() => {
                  setShowProviderModal(false);
                  setEditingProvider(null);
                  setNewProvider({ name: '', type: 'openai', configuration: {}, isActive: true });
                }}
                className="p-2 rounded-lg hover:bg-gray-100"
              >
                ×
              </button>
            </div>
            <div className="p-6">
              {renderProviderForm()}
            </div>
            <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200">
              <button
                onClick={() => {
                  setShowProviderModal(false);
                  setEditingProvider(null);
                  setNewProvider({ name: '', type: 'openai', configuration: {}, isActive: true });
                }}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveProvider}
                className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-2 rounded-lg hover:shadow-lg transition-all duration-200"
              >
                {editingProvider ? 'Update Provider' : 'Add Provider'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}