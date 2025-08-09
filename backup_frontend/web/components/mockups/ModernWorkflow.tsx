'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  CheckCircle2, 
  Circle, 
  Upload, 
  FileText, 
  Shield, 
  AlertTriangle, 
  Eye, 
  Edit3,
  Clock,
  Bot,
  ArrowRight
} from 'lucide-react';

export function ModernWorkflowMockup() {
  const [currentStep, setCurrentStep] = useState(2);
  
  const steps = [
    {
      id: 1,
      name: 'Document Upload',
      description: 'Upload architectural documents and requirements',
      icon: Upload,
      status: 'completed',
      confidence: 95,
      agent: 'Document Processing Agent'
    },
    {
      id: 2,
      name: 'DFD Generation',
      description: 'Generate Data Flow Diagram from documents',
      icon: FileText,
      status: 'active',
      confidence: 87,
      agent: 'DFD Generation Agent'
    },
    {
      id: 3,
      name: 'Threat Analysis',
      description: 'Identify security threats using STRIDE methodology',
      icon: Shield,
      status: 'pending',
      confidence: null,
      agent: 'Threat Analysis Agent'
    },
    {
      id: 4,
      name: 'Report Generation',
      description: 'Generate comprehensive security report',
      icon: AlertTriangle,
      status: 'pending',
      confidence: null,
      agent: 'Report Generation Agent'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-blue-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            Threat Modeling Workflow
          </h1>
          <p className="text-blue-200">Modern Agent-Based Security Analysis</p>
        </div>

        {/* Progress Bar */}
        <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 mb-8">
          <div className="flex justify-between text-sm text-blue-200 mb-2">
            <span>Step {currentStep} of {steps.length}</span>
            <span>{Math.round((currentStep / steps.length) * 100)}% Complete</span>
          </div>
          <Progress 
            value={(currentStep / steps.length) * 100} 
            className="h-3 bg-blue-900/30"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Workflow Steps */}
          <div className="lg:col-span-2 space-y-6">
            {steps.map((step, index) => (
              <Card 
                key={step.id} 
                className={`transition-all duration-500 hover:scale-105 ${
                  step.status === 'active' 
                    ? 'bg-gradient-to-r from-blue-900/50 to-purple-900/50 border-blue-400 shadow-lg shadow-blue-400/25' 
                    : step.status === 'completed'
                    ? 'bg-gradient-to-r from-green-900/30 to-blue-900/30 border-green-400'
                    : 'bg-white/5 border-gray-600'
                } backdrop-blur-md border`}
              >
                <CardHeader className="flex flex-row items-center space-y-0 pb-2">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-full ${
                      step.status === 'completed' ? 'bg-green-500/20' :
                      step.status === 'active' ? 'bg-blue-500/20' :
                      'bg-gray-500/20'
                    }`}>
                      {step.status === 'completed' ? (
                        <CheckCircle2 className="w-6 h-6 text-green-400" />
                      ) : step.status === 'active' ? (
                        <step.icon className="w-6 h-6 text-blue-400 animate-pulse" />
                      ) : (
                        <Circle className="w-6 h-6 text-gray-400" />
                      )}
                    </div>
                    <div>
                      <CardTitle className="text-white text-lg">
                        {step.name}
                      </CardTitle>
                      <p className="text-sm text-gray-300">
                        {step.description}
                      </p>
                    </div>
                  </div>
                  <div className="ml-auto flex items-center space-x-2">
                    <Badge variant="secondary" className="bg-purple-500/20 text-purple-200 border-purple-400">
                      <Bot className="w-3 h-3 mr-1" />
                      AI Agent
                    </Badge>
                    {step.confidence && (
                      <Badge 
                        variant="outline" 
                        className={`${
                          step.confidence >= 90 ? 'border-green-400 text-green-400' :
                          step.confidence >= 75 ? 'border-yellow-400 text-yellow-400' :
                          'border-red-400 text-red-400'
                        }`}
                      >
                        {step.confidence}% Confidence
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-sm text-gray-400">
                      <Clock className="w-4 h-4" />
                      <span>{step.agent}</span>
                    </div>
                    <div className="flex space-x-2">
                      {step.status === 'completed' && (
                        <>
                          <Button size="sm" variant="outline" className="bg-white/10 border-gray-600 text-white hover:bg-white/20">
                            <Eye className="w-4 h-4 mr-1" />
                            View Results
                          </Button>
                          <Button size="sm" variant="outline" className="bg-white/10 border-gray-600 text-white hover:bg-white/20">
                            <Edit3 className="w-4 h-4 mr-1" />
                            Edit
                          </Button>
                        </>
                      )}
                      {step.status === 'active' && (
                        <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white">
                          <ArrowRight className="w-4 h-4 mr-1" />
                          Continue
                        </Button>
                      )}
                    </div>
                  </div>
                  {step.status === 'active' && (
                    <div className="mt-4">
                      <Progress value={67} className="h-2 bg-blue-900/30" />
                      <p className="text-xs text-blue-300 mt-1">Processing documents... 67% complete</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Side Panel */}
          <div className="space-y-6">
            {/* Current Status */}
            <Card className="bg-white/10 backdrop-blur-md border border-gray-600">
              <CardHeader>
                <CardTitle className="text-white text-lg flex items-center">
                  <FileText className="w-5 h-5 mr-2 text-blue-400" />
                  Current Status
                </CardTitle>
              </CardHeader>
              <CardContent className="text-gray-300">
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span>Project:</span>
                    <span className="text-white">E-Commerce Platform</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Started:</span>
                    <span className="text-white">2 hours ago</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Est. Completion:</span>
                    <span className="text-white">45 minutes</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Threats Found:</span>
                    <Badge variant="destructive" className="bg-red-500/20 text-red-400 border-red-500">
                      3 High Risk
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Automation Controls */}
            <Card className="bg-white/10 backdrop-blur-md border border-gray-600">
              <CardHeader>
                <CardTitle className="text-white text-lg flex items-center">
                  <Bot className="w-5 h-5 mr-2 text-purple-400" />
                  Automation Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm">Auto-approve high confidence</span>
                  <div className="w-10 h-6 bg-blue-600 rounded-full relative">
                    <div className="w-4 h-4 bg-white rounded-full absolute top-1 right-1"></div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm">Real-time notifications</span>
                  <div className="w-10 h-6 bg-blue-600 rounded-full relative">
                    <div className="w-4 h-4 bg-white rounded-full absolute top-1 right-1"></div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm">Expert review required</span>
                  <div className="w-10 h-6 bg-gray-600 rounded-full relative">
                    <div className="w-4 h-4 bg-white rounded-full absolute top-1 left-1"></div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card className="bg-white/10 backdrop-blur-md border border-gray-600">
              <CardHeader>
                <CardTitle className="text-white text-lg">Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex items-start space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5" />
                    <div>
                      <p className="text-white">Document analysis completed</p>
                      <p className="text-gray-400 text-xs">15 minutes ago</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <Clock className="w-4 h-4 text-blue-400 mt-0.5" />
                    <div>
                      <p className="text-white">DFD generation in progress</p>
                      <p className="text-gray-400 text-xs">Now</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Action Bar */}
        <div className="mt-8 flex justify-between items-center bg-white/10 backdrop-blur-md rounded-lg p-4 border border-gray-600">
          <div className="flex items-center space-x-4">
            <Button variant="outline" className="bg-white/10 border-gray-600 text-white hover:bg-white/20">
              Export Progress
            </Button>
            <Button variant="outline" className="bg-white/10 border-gray-600 text-white hover:bg-white/20">
              View Logs
            </Button>
          </div>
          <div className="flex items-center space-x-4">
            <Button variant="outline" className="bg-red-500/20 border-red-500 text-red-400 hover:bg-red-500/30">
              Pause Workflow
            </Button>
            <Button className="bg-green-600 hover:bg-green-700 text-white">
              Continue to Next Step
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}