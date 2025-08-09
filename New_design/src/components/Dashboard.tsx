import React, { useState } from 'react';
import { Play, Pause, MoreVertical, Calendar, Clock, Users, TrendingUp, Activity } from 'lucide-react';
import { Workflow } from '../types';

interface DashboardProps {
  workflows: Workflow[];
  onWorkflowClick: (workflow: Workflow) => void;
}

export function Dashboard({ workflows, onWorkflowClick }: DashboardProps) {
  const [filter, setFilter] = useState('all');

  const activeWorkflows = workflows.filter(w => !w.isTemplate);
  const recentWorkflows = workflows.slice(0, 6);
  const totalRuns = 1247; // Mock data
  const successRate = 94.2; // Mock data

  const filteredWorkflows = filter === 'all' 
    ? workflows 
    : filter === 'active' 
    ? workflows.filter(w => !w.isTemplate)
    : workflows.filter(w => w.isTemplate);

  const stats = [
    {
      title: 'Total Workflows',
      value: workflows.length,
      change: '+12%',
      icon: Activity,
      color: 'text-purple-600 bg-purple-100'
    },
    {
      title: 'Active Workflows',
      value: activeWorkflows.length,
      change: '+8%',
      icon: Play,
      color: 'text-green-600 bg-green-100'
    },
    {
      title: 'Total Runs',
      value: totalRuns.toLocaleString(),
      change: '+23%',
      icon: TrendingUp,
      color: 'text-blue-600 bg-blue-100'
    },
    {
      title: 'Success Rate',
      value: `${successRate}%`,
      change: '+2.1%',
      icon: Users,
      color: 'text-indigo-600 bg-indigo-100'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Ansvar Security Dashboard</h1>
          <p className="text-gray-600 mt-2">Overview of your automated workflows and AI agent performance on our data-sovereign platform</p>
        </div>
        <div className="flex space-x-3">
          <button 
            onClick={() => window.dispatchEvent(new CustomEvent('navigate', { detail: 'workflow-builder' }))}
            className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg hover:shadow-lg transition-all duration-200"
          >
            Create Workflow
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-2">{stat.value}</p>
                  <p className="text-sm text-green-600 mt-1">{stat.change} from last month</p>
                </div>
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Recent Workflow Runs</h2>
              <div className="flex space-x-2">
                <button
                  onClick={() => setFilter('all')}
                  className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                    filter === 'all'
                      ? 'bg-purple-100 text-purple-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => setFilter('active')}
                  className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                    filter === 'active'
                      ? 'bg-purple-100 text-purple-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  Active
                </button>
                <button
                  onClick={() => setFilter('template')}
                  className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                    filter === 'template'
                      ? 'bg-purple-100 text-purple-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  Templates
                </button>
              </div>
            </div>

            <div className="space-y-4">
              {filteredWorkflows.map(workflow => (
                <div
                  key={workflow.id}
                  onClick={() => onWorkflowClick(workflow)}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                      <Activity className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">{workflow.name}</h3>
                      <p className="text-sm text-gray-600">{workflow.steps.length} steps</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <p className="text-sm text-gray-900">Last run: 2 hours ago</p>
                      <p className="text-xs text-green-600">Success</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      {workflow.isTemplate && (
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                          Template
                        </span>
                      )}
                      <button className="p-1 rounded hover:bg-gray-200">
                        <MoreVertical className="w-4 h-4 text-gray-600" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {/* Quick Actions */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button className="w-full flex items-center space-x-3 p-3 rounded-lg border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-colors">
                <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                  <Play className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-medium text-gray-700">Run Workflow</span>
              </button>
              <button className="w-full flex items-center space-x-3 p-3 rounded-lg border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-colors">
                <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-teal-500 rounded-lg flex items-center justify-center">
                  <Users className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-medium text-gray-700">Create Agent</span>
              </button>
              <button className="w-full flex items-center space-x-3 p-3 rounded-lg border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-colors">
                <div className="w-8 h-8 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg flex items-center justify-center">
                  <Activity className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-medium text-gray-700">View Analytics</span>
              </button>
            </div>
          </div>

          {/* System Status */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">API Status</span>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-green-600">Operational</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Queue Status</span>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-green-600">Normal</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Active Agents</span>
                <span className="text-sm text-gray-900">4/6</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Response Time</span>
                <span className="text-sm text-gray-900">1.2s avg</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}