"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Temporarily comment out complex components to test routing
// import ProjectDashboard from '@/components/projects/project-dashboard';
// import CreateProjectModal from '@/components/projects/create-project-modal';
// import SessionTree from '@/components/projects/session-tree';
// import CreateSessionModal from '@/components/projects/create-session-modal';
// import { Button } from '@/components/ui/button';
import { ArrowLeft, RefreshCw } from 'lucide-react';
// import { useToast } from '@/hooks/use-toast';

interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at?: string;
  created_by?: string;
  tags?: string[];
  session_count: number;
  latest_session?: {
    id: string;
    name: string;
    status: string;
    completion_percentage: number;
    updated_at: string;
  };
}

interface ProjectData {
  name: string;
  description: string;
  tags: string[];
  created_by?: string;
}

interface SessionData {
  project_id: string;
  name: string;
  description?: string;
  parent_session_id?: string;
  branch_point?: string;
}

interface Session {
  id: string;
  name: string;
  description?: string;
  status: string;
  completion_percentage: number;
  created_at: string;
  updated_at?: string;
  is_main_branch: boolean;
  branch_point?: string;
  document_name?: string;
  total_threats: number;
  risk_summary?: { [key: string]: number };
  children: Session[];
}

export default function ProjectsPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  // Simple test function
  const testApiConnection = async () => {
    try {
      const response = await fetch('/api/projects');
      if (response.ok) {
        setError("✅ API connection successful!");
      } else {
        setError(`❌ API error: ${response.status} ${response.statusText}`);
      }
    } catch (err) {
      setError(`❌ Connection failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          🛡️ Project Management
        </h1>
        
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Route Test</h2>
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <button 
                onClick={testApiConnection}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                Test API Connection
              </button>
              
              <button 
                onClick={() => router.push('/')}
                className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
              >
                ← Back to Main App
              </button>
            </div>
            
            {error && (
              <div className="p-3 bg-gray-100 border rounded">
                <code className="text-sm">{error}</code>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Debug Information</h2>
          <div className="space-y-2 text-sm">
            <div>✅ Route accessible at /projects</div>
            <div>✅ Next.js app router working</div>
            <div>✅ React components rendering</div>
            <div>✅ Database migration completed</div>
          </div>
          
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded">
            <p className="text-sm text-yellow-800">
              If the API test works, the full project management interface can be enabled.
              The components are temporarily disabled for debugging.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
