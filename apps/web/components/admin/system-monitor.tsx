'use client'

import { Card } from '@/components/ui/card'

export default function SystemMonitor() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">System Monitor</h1>
        <p className="text-gray-600">Monitor system performance and health metrics</p>
      </div>

      {/* Coming Soon */}
      <Card className="p-8 text-center">
        <div className="text-gray-400 text-4xl mb-4">⚙️</div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">System Monitoring</h2>
        <p className="text-gray-600 mb-4">
          Real-time monitoring, resource usage, and performance metrics coming soon.
        </p>
        <div className="text-sm text-gray-500">
          Features to include:
          <ul className="mt-2 space-y-1">
            <li>• CPU and Memory Usage</li>
            <li>• LLM Provider Health Status</li>
            <li>• Database Connection Pool Stats</li>
            <li>• Pipeline Execution Metrics</li>
            <li>• Error Rates and Alerts</li>
          </ul>
        </div>
      </Card>
    </div>
  )
}