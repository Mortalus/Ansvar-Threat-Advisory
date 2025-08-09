'use client';

import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  ArrowRight, 
  Play, 
  Settings, 
  History, 
  GitBranch,
  Zap,
  Eye,
  Users,
  Shield,
  Activity,
  CheckCircle2,
  Clock
} from 'lucide-react';

export default function WorkflowDemoPage() {
  return (
    <div className="container mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold">Workflow System Demo</h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Complete UX flow demonstration for the modular workflow engine with real-time execution tracking
        </p>
        <Badge variant="outline" className="text-lg px-4 py-2">
          Phase 3: Complete Implementation
        </Badge>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-center space-x-2">
              <CheckCircle2 className="h-8 w-8 text-green-600" />
              <div className="text-center">
                <div className="text-2xl font-bold text-green-900">API Backend</div>
                <div className="text-sm text-green-700">Phase 2 & 3 Complete</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-center space-x-2">
              <Activity className="h-8 w-8 text-blue-600" />
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-900">Real-time UI</div>
                <div className="text-sm text-blue-700">WebSocket Integration</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-purple-200 bg-purple-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-center space-x-2">
              <Shield className="h-8 w-8 text-purple-600" />
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-900">Navigation</div>
                <div className="text-sm text-purple-700">Complete UX Flow</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Workflow Paths */}
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold text-center">Available UX Paths</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Main Workflows Hub */}
          <Link href="/workflows">
            <Card className="hover:shadow-lg transition-all cursor-pointer border-blue-200 hover:border-blue-400">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <GitBranch className="h-8 w-8 text-blue-600" />
                    <div>
                      <CardTitle className="text-blue-900">Main Workflows Hub</CardTitle>
                      <CardDescription>Central navigation for all workflow features</CardDescription>
                    </div>
                  </div>
                  <ArrowRight className="h-5 w-5 text-blue-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm text-gray-600">
                  <div>• Template gallery and quick actions</div>
                  <div>• Recent activity overview</div>
                  <div>• Navigation to all workflow sections</div>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Phase 3 Portal */}
          <Link href="/workflows/phase3">
            <Card className="hover:shadow-lg transition-all cursor-pointer border-green-200 hover:border-green-400">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Zap className="h-8 w-8 text-green-600" />
                    <div>
                      <CardTitle className="text-green-900">Phase 3 Portal</CardTitle>
                      <CardDescription>Advanced workflow execution interface</CardDescription>
                    </div>
                  </div>
                  <ArrowRight className="h-5 w-5 text-green-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm text-gray-600">
                  <div>• Real-time workflow execution</div>
                  <div>• Live progress tracking</div>
                  <div>• WebSocket status updates</div>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Live Demo */}
          <Link href="/workflows/phase3/demo">
            <Card className="hover:shadow-lg transition-all cursor-pointer border-yellow-200 hover:border-yellow-400">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Play className="h-8 w-8 text-yellow-600" />
                    <div>
                      <CardTitle className="text-yellow-900">Live Demo</CardTitle>
                      <CardDescription>Interactive workflow execution demo</CardDescription>
                    </div>
                  </div>
                  <ArrowRight className="h-5 w-5 text-yellow-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm text-gray-600">
                  <div>• Create and execute demo workflows</div>
                  <div>• WebSocket connection status</div>
                  <div>• Real-time event logging</div>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Template Management */}
          <Link href="/workflows/templates">
            <Card className="hover:shadow-lg transition-all cursor-pointer border-purple-200 hover:border-purple-400">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Settings className="h-8 w-8 text-purple-600" />
                    <div>
                      <CardTitle className="text-purple-900">Template Management</CardTitle>
                      <CardDescription>Create and manage workflow templates</CardDescription>
                    </div>
                  </div>
                  <ArrowRight className="h-5 w-5 text-purple-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm text-gray-600">
                  <div>• Browse and search templates</div>
                  <div>• Category filtering</div>
                  <div>• Template status management</div>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Execution History */}
          <Link href="/workflows/history">
            <Card className="hover:shadow-lg transition-all cursor-pointer border-indigo-200 hover:border-indigo-400">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <History className="h-8 w-8 text-indigo-600" />
                    <div>
                      <CardTitle className="text-indigo-900">Execution History</CardTitle>
                      <CardDescription>View and analyze past executions</CardDescription>
                    </div>
                  </div>
                  <ArrowRight className="h-5 w-5 text-indigo-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm text-gray-600">
                  <div>• Execution timeline and status</div>
                  <div>• Performance analytics</div>
                  <div>• Error logs and debugging</div>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Admin Interface */}
          <Link href="/admin">
            <Card className="hover:shadow-lg transition-all cursor-pointer border-red-200 hover:border-red-400">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Users className="h-8 w-8 text-red-600" />
                    <div>
                      <CardTitle className="text-red-900">Admin Interface</CardTitle>
                      <CardDescription>Administrative tools and settings</CardDescription>
                    </div>
                  </div>
                  <ArrowRight className="h-5 w-5 text-red-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm text-gray-600">
                  <div>• System configuration</div>
                  <div>• Agent management</div>
                  <div>• Workflow builder tools</div>
                </div>
              </CardContent>
            </Card>
          </Link>
        </div>
      </div>

      {/* Technical Implementation Notes */}
      <Card className="bg-gray-50">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Eye className="h-5 w-5" />
            <span>Implementation Status</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-2 text-green-800">✅ Completed Features</h4>
              <ul className="space-y-1 text-sm text-gray-700">
                <li>• Phase 2: Workflow execution engine</li>
                <li>• Phase 3: Real-time UI with WebSockets</li>
                <li>• Complete navigation structure</li>
                <li>• Breadcrumb navigation</li>
                <li>• Template management interface</li>
                <li>• Execution history with filtering</li>
                <li>• Artifact viewer components</li>
                <li>• Mobile-responsive design</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2 text-blue-800">🔧 API Endpoints Available</h4>
              <ul className="space-y-1 text-sm font-mono text-gray-700">
                <li>• GET /api/phase2/workflow/templates</li>
                <li>• POST /api/phase2/workflow/runs/start</li>
                <li>• GET /api/phase3/workflow/status</li>
                <li>• WS /api/ws/workflow/[runId]</li>
                <li>• GET /api/phase2/workflow/runs</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Start Guide */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="text-blue-900">🚀 Quick Start</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <p className="text-blue-800">
              <strong>Best Starting Point:</strong> Try the <Link href="/workflows/phase3/demo" className="underline hover:text-blue-600">Live Demo</Link> to see real-time workflow execution with WebSocket updates.
            </p>
            <div className="flex flex-wrap gap-2">
              <Link href="/workflows/phase3/demo">
                <Button size="sm">
                  <Play className="mr-2 h-4 w-4" />
                  Start Demo
                </Button>
              </Link>
              <Link href="/workflows">
                <Button variant="outline" size="sm">
                  <GitBranch className="mr-2 h-4 w-4" />
                  Browse All
                </Button>
              </Link>
              <Link href="/workflows/templates">
                <Button variant="outline" size="sm">
                  <Settings className="mr-2 h-4 w-4" />
                  Manage Templates
                </Button>
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}