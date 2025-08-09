import React, { useState } from 'react';
import { X, Save, Plus, Trash2 } from 'lucide-react';
import { Agent } from '../types';

interface SystemPromptModalProps {
  agent: Agent;
  isOpen: boolean;
  onClose: () => void;
  onSave: (systemPrompt: string, capabilities: string[]) => void;
}

export function SystemPromptModal({ agent, isOpen, onClose, onSave }: SystemPromptModalProps) {
  const [systemPrompt, setSystemPrompt] = useState(agent.systemPrompt);
  const [capabilities, setCapabilities] = useState([...agent.capabilities]);
  const [newCapability, setNewCapability] = useState('');

  if (!isOpen) return null;

  const handleSave = () => {
    onSave(systemPrompt, capabilities);
    onClose();
  };

  const addCapability = () => {
    if (newCapability.trim() && !capabilities.includes(newCapability.trim())) {
      setCapabilities([...capabilities, newCapability.trim()]);
      setNewCapability('');
    }
  };

  const removeCapability = (index: number) => {
    setCapabilities(capabilities.filter((_, i) => i !== index));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      addCapability();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">System Prompt & Capabilities</h2>
            <p className="text-gray-600 mt-1">{agent.name}</p>
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
          <div className="space-y-6">
            {/* System Prompt Section */}
            <div>
              <label className="block text-lg font-semibold text-gray-900 mb-3">
                System Prompt
              </label>
              <p className="text-sm text-gray-600 mb-4">
                Define the agent's behavior, personality, and core instructions. This prompt will be used to guide the AI's responses.
              </p>
              <div className="border border-gray-300 rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-3 py-2 border-b border-gray-300 flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">System Prompt Editor</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">{systemPrompt.length} characters</span>
                    <button
                      type="button"
                      onClick={() => setSystemPrompt('')}
                      className="text-xs text-red-600 hover:text-red-700"
                    >
                      Clear
                    </button>
                  </div>
                </div>
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  rows={12}
                  className="w-full px-4 py-3 border-0 focus:ring-0 focus:outline-none resize-none font-mono text-sm"
                  placeholder="Enter the system prompt that defines how this agent should behave..."
                />
              </div>
            </div>

            {/* Capabilities Section */}
            <div>
              <label className="block text-lg font-semibold text-gray-900 mb-3">
                Capabilities
              </label>
              <p className="text-sm text-gray-600 mb-4">
                Define what this agent can do. These capabilities will be displayed to users and help them understand the agent's strengths.
              </p>
              
              {/* Add New Capability */}
              <div className="flex space-x-2 mb-4">
                <input
                  type="text"
                  value={newCapability}
                  onChange={(e) => setNewCapability(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Add a new capability..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <button
                  onClick={addCapability}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:shadow-lg transition-all duration-200 flex items-center space-x-2"
                >
                  <Plus className="w-4 h-4" />
                  <span>Add</span>
                </button>
              </div>

              {/* Capabilities List */}
              <div className="space-y-2">
                {capabilities.map((capability, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                      <span className="text-gray-900 font-medium">{capability}</span>
                    </div>
                    <button
                      onClick={() => removeCapability(index)}
                      className="p-1 rounded hover:bg-red-100 text-red-500 hover:text-red-700 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
                {capabilities.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <p>No capabilities defined yet.</p>
                    <p className="text-sm">Add capabilities to help users understand what this agent can do.</p>
                  </div>
                )}
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
            className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-2 rounded-lg hover:shadow-lg transition-all duration-200 flex items-center space-x-2"
          >
            <Save className="w-4 h-4" />
            <span>Save Changes</span>
          </button>
        </div>
      </div>
    </div>
  );
}