'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  CheckCircle, 
  Clock, 
  FileText, 
  AlertCircle, 
  Eye, 
  Edit3,
  Download,
  Play,
  Settings
} from 'lucide-react';

export function ExistingStyleWorkflowMockup() {
  const [currentStep, setCurrentStep] = useState(2);
  
  const steps = [
    {
      id: 1,
      name: 'Document Upload',
      description: 'Architecture documents and system requirements uploaded',
      status: 'completed',
      completedAt: '2 hours ago',
      confidence: 95,
      results: '12 files processed, 847 pages analyzed'
    },
    {
      id: 2,
      name: 'Data Flow Analysis',
      description: 'Analyzing system components and data flows',
      status: 'in_progress',
      startedAt: '15 minutes ago',
      confidence: 87,
      progress: 67
    },
    {
      id: 3,
      name: 'Threat Identification',
      description: 'STRIDE-based threat analysis and risk assessment',
      status: 'pending',
      estimatedDuration: '25 minutes'
    },
    {
      id: 4,
      name: 'Report Generation',
      description: 'Comprehensive security analysis report',
      status: 'pending',
      estimatedDuration: '10 minutes'
    }
  ];

  const threats = [
    { id: 1, type: 'Spoofing', severity: 'High', component: 'Authentication Service' },
    { id: 2, type: 'Tampering', severity: 'Medium', component: 'User Database' },
    { id: 3, type: 'Information Disclosure', severity: 'High', component: 'API Gateway' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-semibold text-gray-900">
                Threat Modeling Pipeline
              </h1>
              <p className="text-gray-600 mt-1">E-Commerce Platform Security Analysis</p>
            </div>
            <div className="flex items-center space-x-3">
              <Badge variant="secondary" className="bg-blue-100 text-blue-800 border-blue-200">
                Step {currentStep} of {steps.length}
              </Badge>
              <Button variant="outline" size="sm">
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </Button>
            </div>
          </div>
          
          {/* Progress Section */}
          <div className="mt-6 bg-gray-50 rounded-lg p-4">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Overall Progress</span>
              <span>{Math.round((currentStep / steps.length) * 100)}% Complete</span>
            </div>
            <Progress value={(currentStep / steps.length) * 100} className="h-2" />
            <p className="text-xs text-gray-500 mt-2">
              Estimated completion: 35 minutes remaining
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Workflow */}
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Workflow Steps</h2>
            
            {steps.map((step) => (
              <Card key={step.id} className="border border-gray-200 shadow-sm">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <div className="pt-1">
                        {step.status === 'completed' ? (
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        ) : step.status === 'in_progress' ? (
                          <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Clock className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                      <div className="flex-1">
                        <CardTitle className="text-lg text-gray-900">
                          {step.name}
                        </CardTitle>
                        <p className="text-sm text-gray-600 mt-1">
                          {step.description}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {step.confidence && (
                        <Badge 
                          variant="outline" 
                          className={
                            step.confidence >= 90 ? 'border-green-500 text-green-700 bg-green-50' :
                            step.confidence >= 75 ? 'border-yellow-500 text-yellow-700 bg-yellow-50' :
                            'border-red-500 text-red-700 bg-red-50'
                          }
                        >
                          {step.confidence}% Confidence
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent className="pt-0">
                  {step.status === 'completed' && (
                    <div className="space-y-3">
                      <div className="text-sm text-gray-600 bg-green-50 border border-green-200 rounded p-3">
                        <strong>Results:</strong> {step.results}
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-500">
                          Completed {step.completedAt}
                        </span>
                        <div className="flex space-x-2">
                          <Button size="sm" variant="outline">
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
                          </Button>
                          <Button size="sm" variant="outline">
                            <Edit3 className="w-4 h-4 mr-2" />
                            Edit
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {step.status === 'in_progress' && (
                    <div className="space-y-3">
                      <Progress value={step.progress} className="h-2" />
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">
                          Started {step.startedAt}
                        </span>
                        <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white">
                          <Play className="w-4 h-4 mr-2" />
                          Continue
                        </Button>
                      </div>
                    </div>
                  )}
                  
                  {step.status === 'pending' && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500">
                        Estimated duration: {step.estimatedDuration}
                      </span>
                      <Button size="sm" variant="outline" disabled>
                        Waiting for previous step
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Project Summary */}
            <Card className="border border-gray-200 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg text-gray-900 flex items-center">
                  <FileText className="w-5 h-5 mr-2 text-blue-600" />
                  Project Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Project Type:</span>
                    <span className="font-medium">Web Application</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Components:</span>
                    <span className="font-medium">15 identified</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Data Stores:</span>
                    <span className="font-medium">4 databases</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Trust Boundaries:</span>
                    <span className="font-medium">6 boundaries</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Threat Preview */}
            <Card className="border border-gray-200 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg text-gray-900 flex items-center">
                  <AlertCircle className="w-5 h-5 mr-2 text-red-600" />
                  Threats Identified
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {threats.map((threat) => (
                    <div key={threat.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {threat.type}
                        </p>
                        <p className="text-xs text-gray-600">
                          {threat.component}
                        </p>
                      </div>
                      <Badge 
                        variant={threat.severity === 'High' ? 'destructive' : 'secondary'}
                        className={
                          threat.severity === 'High' 
                            ? 'bg-red-100 text-red-800 border-red-200'
                            : 'bg-yellow-100 text-yellow-800 border-yellow-200'
                        }
                      >
                        {threat.severity}
                      </Badge>
                    </div>
                  ))}
                </div>
                <Button 
                  size="sm" 
                  variant="outline" 
                  className="w-full mt-4"
                  disabled
                >
                  View All Threats (Available after analysis)
                </Button>
              </CardContent>
            </Card>

            {/* Export Options */}
            <Card className="border border-gray-200 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg text-gray-900 flex items-center">
                  <Download className="w-5 h-5 mr-2 text-green-600" />
                  Export Options
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <FileText className="w-4 h-4 mr-2" />
                    PDF Report
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <FileText className="w-4 h-4 mr-2" />
                    Excel Spreadsheet
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <FileText className="w-4 h-4 mr-2" />
                    JSON Data
                  </Button>
                </div>
                <p className="text-xs text-gray-500 mt-3">
                  Reports will be available after workflow completion
                </p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Action Footer */}
        <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button variant="outline">
                Save Progress
              </Button>
              <Button variant="outline">
                View Detailed Logs
              </Button>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button variant="outline" className="text-red-600 border-red-300 hover:bg-red-50">
                Pause Analysis
              </Button>
              <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                Continue Workflow
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}