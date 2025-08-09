'use client';

import { useState } from 'react';
import { ModernWorkflowMockup } from '@/components/mockups/ModernWorkflow';
import { ExistingStyleWorkflowMockup } from '@/components/mockups/ExistingStyleWorkflow';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Monitor, 
  Palette, 
  Eye, 
  GitCompare,
  Sparkles,
  FileText,
  Check
} from 'lucide-react';

type ViewMode = 'modern' | 'existing' | 'comparison';

export default function PreviewPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('comparison');

  const features = {
    modern: [
      'Dark gradient background with glass morphism',
      'Animated progress indicators and hover effects',
      'Real-time confidence scoring displays',
      'Modern card layouts with backdrop blur',
      'Color-coded status indicators',
      'Interactive automation controls',
      'Professional gradient color scheme'
    ],
    existing: [
      'Clean white background with subtle shadows',
      'Professional card-based layout structure',
      'Clear data tables and summary statistics',
      'Traditional button and form styling',
      'Structured information hierarchy',
      'Export options clearly displayed',
      'Familiar enterprise interface design'
    ]
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Control Header */}
      <div className="bg-white border-b border-gray-200 p-6 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Agent Workflow UI Preview
              </h1>
              <p className="text-gray-600">
                Compare modern and existing design styles for the threat modeling workflow interface
              </p>
            </div>
            
            <Badge variant="secondary" className="bg-blue-100 text-blue-800 border-blue-200">
              UI Mockup Preview
            </Badge>
          </div>

          {/* View Mode Controls */}
          <div className="flex items-center space-x-2">
            <Button
              onClick={() => setViewMode('modern')}
              variant={viewMode === 'modern' ? 'default' : 'outline'}
              size="sm"
              className="flex items-center"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Modern Style
            </Button>
            
            <Button
              onClick={() => setViewMode('existing')}
              variant={viewMode === 'existing' ? 'default' : 'outline'}
              size="sm"
              className="flex items-center"
            >
              <FileText className="w-4 h-4 mr-2" />
              Existing Style
            </Button>
            
            <Button
              onClick={() => setViewMode('comparison')}
              variant={viewMode === 'comparison' ? 'default' : 'outline'}
              size="sm"
              className="flex items-center"
            >
              <GitCompare className="w-4 h-4 mr-2" />
              Side by Side
            </Button>
          </div>
        </div>
      </div>

      {/* Feature Comparison */}
      {viewMode === 'comparison' && (
        <div className="max-w-7xl mx-auto p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Modern Style Features */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center text-lg">
                  <Sparkles className="w-5 h-5 mr-2 text-purple-600" />
                  Modern Style Features
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {features.modern.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <Check className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded">
                  <p className="text-sm text-purple-700">
                    <strong>Best for:</strong> Modern tech companies, startups, and organizations 
                    that value cutting-edge design and interactive user experiences.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Existing Style Features */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center text-lg">
                  <FileText className="w-5 h-5 mr-2 text-blue-600" />
                  Existing Style Features
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {features.existing.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <Check className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                  <p className="text-sm text-blue-700">
                    <strong>Best for:</strong> Enterprise organizations, government agencies, 
                    and businesses that prefer traditional, proven interface designs.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Mockup Display */}
      <div className={viewMode === 'comparison' ? 'grid grid-cols-1 xl:grid-cols-2' : ''}>
        {(viewMode === 'modern' || viewMode === 'comparison') && (
          <div className={viewMode === 'comparison' ? 'border-r border-gray-300' : ''}>
            {viewMode === 'comparison' && (
              <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-4 text-center">
                <h2 className="text-lg font-semibold flex items-center justify-center">
                  <Sparkles className="w-5 h-5 mr-2" />
                  Modern Style
                </h2>
              </div>
            )}
            <ModernWorkflowMockup />
          </div>
        )}
        
        {(viewMode === 'existing' || viewMode === 'comparison') && (
          <div>
            {viewMode === 'comparison' && (
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4 text-center">
                <h2 className="text-lg font-semibold flex items-center justify-center">
                  <FileText className="w-5 h-5 mr-2" />
                  Existing Style
                </h2>
              </div>
            )}
            <ExistingStyleWorkflowMockup />
          </div>
        )}
      </div>

      {/* Decision Helper */}
      {viewMode === 'comparison' && (
        <div className="max-w-7xl mx-auto p-6">
          <Card className="bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
            <CardHeader>
              <CardTitle className="flex items-center text-lg text-green-800">
                <Eye className="w-5 h-5 mr-2" />
                Ready to Choose?
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-green-700 mb-4">
                Both styles support the same functionality - the difference is in visual design and user experience. 
                Consider your organization's brand, user preferences, and existing design systems.
              </p>
              <div className="flex items-center space-x-4">
                <Button className="bg-purple-600 hover:bg-purple-700 text-white">
                  Choose Modern Style
                </Button>
                <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                  Choose Existing Style
                </Button>
                <Button variant="outline">
                  Need More Time to Decide
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}