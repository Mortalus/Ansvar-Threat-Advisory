'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { Card } from '@/components/ui/card'

interface Task {
  task_id: string
  name: string
  status: string
  started_at: string
  pipeline_id?: string
}

export default function TaskMonitor() {
  const [activeTasks, setActiveTasks] = useState<Task[]>([])
  const [isExpanded, setIsExpanded] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadActiveTasks()
    
    // Poll for task updates every 5 seconds
    const interval = setInterval(loadActiveTasks, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadActiveTasks = async () => {
    try {
      setLoading(true)
      const tasks = await api.listActiveTasks()
      setActiveTasks(tasks)
    } catch (error) {
      console.error('Failed to load active tasks:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'running':
      case 'in_progress':
        return 'bg-blue-100 text-blue-800'
      case 'completed':
      case 'success':
        return 'bg-green-100 text-green-800'
      case 'failed':
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return '⏳'
      case 'running':
      case 'in_progress':
        return '🔄'
      case 'completed':
      case 'success':
        return '✅'
      case 'failed':
      case 'error':
        return '❌'
      default:
        return '❓'
    }
  }

  if (activeTasks.length === 0) {
    return null // Don't show the component if there are no active tasks
  }

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <h3 className="text-lg font-medium text-gray-900">Active Tasks</h3>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            {activeTasks.length}
          </span>
          {loading && (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          )}
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          {isExpanded ? 'Collapse' : 'Expand'}
        </button>
      </div>

      {!isExpanded && activeTasks.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {activeTasks.slice(0, 3).map((task) => (
            <div
              key={task.task_id}
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}
            >
              <span className="mr-1">{getStatusIcon(task.status)}</span>
              {task.name}
            </div>
          ))}
          {activeTasks.length > 3 && (
            <span className="text-xs text-gray-500">+{activeTasks.length - 3} more</span>
          )}
        </div>
      )}

      {isExpanded && (
        <div className="mt-4 space-y-2">
          {activeTasks.map((task) => (
            <div key={task.task_id} className="border border-gray-200 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-lg">{getStatusIcon(task.status)}</span>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{task.name}</p>
                    <p className="text-xs text-gray-500">
                      Started: {new Date(task.started_at).toLocaleString()}
                    </p>
                    {task.pipeline_id && (
                      <p className="text-xs text-gray-400">Pipeline: {task.pipeline_id}</p>
                    )}
                  </div>
                </div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                  {task.status}
                </span>
              </div>
            </div>
          ))}
          <div className="flex justify-end">
            <button
              onClick={loadActiveTasks}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Refresh
            </button>
          </div>
        </div>
      )}
    </Card>
  )
}