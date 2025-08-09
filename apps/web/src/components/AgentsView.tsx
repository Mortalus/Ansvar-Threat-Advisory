import React, { useState } from 'react';
import { Bot, Settings, Play, Pause, MoreVertical } from 'lucide-react';
import { Agent } from '../types';

interface AgentsViewProps {
  agents: Agent[];
  onAgentClick: (agent: Agent) => void;
}

export function AgentsView({ agents, onAgentClick }: AgentsViewProps) {
  const [filter, setFilter] = useState('all');
  const categories = ['all', ...new Set(agents.map(agent => agent.category))];

  const filteredAgents = filter === 'all' 
    ? agents 
    : agents.filter(agent => agent.category === filter);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Security Agents</h1>
          <p className="text-gray-600 mt-2">Privacy-focused AI agents for automated security workflows on our data-sovereign platform</p>
        </div>
        <button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg hover:shadow-lg transition-all duration-200">
          Add New Agent
        </button>
      </div>

      {/* Filters */}
      <div className="flex space-x-2">
        {categories.map(category => (
          <button
            key={category}
            onClick={() => setFilter(category)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === category
                ? 'bg-purple-100 text-purple-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {category.charAt(0).toUpperCase() + category.slice(1)}
          </button>
        ))}
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgents.map(agent => (
          <div
            key={agent.id}
            onClick={() => onAgentClick(agent)}
            className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg hover:border-purple-300 transition-all duration-200 cursor-pointer group"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                  <Bot className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 group-hover:text-purple-700 transition-colors">
                    {agent.name}
                  </h3>
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    {agent.category}
                  </span>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${agent.isActive ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                <button className="p-1 rounded hover:bg-gray-100 opacity-0 group-hover:opacity-100 transition-opacity">
                  <MoreVertical className="w-4 h-4 text-gray-600" />
                </button>
              </div>
            </div>

            <p className="text-gray-600 text-sm mb-4 line-clamp-3">{agent.description}</p>

            <div className="flex flex-wrap gap-2 mb-4">
              {agent.capabilities.slice(0, 3).map(capability => (
                <span key={capability} className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded">
                  {capability}
                </span>
              ))}
              {agent.capabilities.length > 3 && (
                <span className="text-xs text-gray-500">+{agent.capabilities.length - 3} more</span>
              )}
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                <div className="flex items-center space-x-1">
                  <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                  <span>{agent.provider}</span>
                </div>
                <div className="flex items-center space-x-1">
                <Settings className="w-4 h-4" />
                  <span>{agent.settings.model}</span>
              </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  // Toggle agent active state
                }}
                className="p-2 rounded-lg hover:bg-gray-100"
              >
                {agent.isActive ? (
                  <Pause className="w-4 h-4 text-orange-500" />
                ) : (
                  <Play className="w-4 h-4 text-green-500" />
                )}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}