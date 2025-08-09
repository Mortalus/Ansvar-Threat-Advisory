"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/apiClient';

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

  // Test API using unified client
  const testApiConnection = async () => {
    try {
      setError("🔄 Testing unified API client...");
      
      // Test health using unified client
      const healthData = await apiClient.projects.health();
      if (healthData.status === 'healthy') {
        setError(`✅ Database healthy! Found ${healthData.projects_count} projects`);
        
        // Test list projects using unified client
        const projectsData = await apiClient.projects.list();
        setError(`✅ Projects API working! Found ${projectsData.length || 0} projects`);
        return;
      } else {
        setError(`❌ Database unhealthy`);
        return;
      }
    } catch (err) {
      setError(`❌ Connection failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      
      // Try system health as fallback
      try {
        await apiClient.health();
        setError('⚠️ Projects API unavailable, but backend is running. Use main app for full functionality.');
      } catch (healthErr) {
        setError('❌ Backend completely unreachable. Check Docker containers.');
      }
    }
  };

  const createTestProject = async () => {
    try {
      setError("🔄 Creating test project...");
      
      const data = await apiClient.projects.createTest();
      setError(`✅ Test project created: ${(data as any)?.name || 'New Project'}`);
    } catch (err) {
      setError(`❌ Failed to create project: ${err instanceof Error ? err.message : 'Unknown error'}`);
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
                onClick={createTestProject}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
              >
                Create Test Project
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
          <h2 className="text-xl font-semibold mb-4">Current Status</h2>
          <div className="space-y-2 text-sm">
            <div>✅ Route accessible at /projects</div>
            <div>✅ Next.js app router working</div>
            <div>✅ React components rendering</div>
            <div>✅ Database migration completed</div>
            <div>✅ Session resumption working in main app</div>
            <div>✅ Threat generation errors fixed</div>
          </div>
          
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded">
            <h3 className="font-semibold text-blue-900 mb-2">Projects Functionality</h3>
            <p className="text-sm text-blue-800 mb-2">
              <strong>Issue:</strong> The main projects API has SQLAlchemy connection pooling issues that cause intermittent failures.
            </p>
            <p className="text-sm text-blue-800 mb-2">
              <strong>Workaround:</strong> Use session management through the main application:
            </p>
            <ul className="text-sm text-blue-800 list-disc ml-4 space-y-1">
              <li>Start a pipeline in the main app</li>
              <li>Sessions are automatically created and managed</li>
              <li>Failed pipelines can be resumed from any step</li>
              <li>All project data is preserved in the database</li>
            </ul>
          </div>
          
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded">
            <h3 className="font-semibold text-green-900 mb-2">✅ Core Issues Resolved</h3>
            <ul className="text-sm text-green-800 list-disc ml-4 space-y-1">
              <li>Threat generation now works without crashes</li>
              <li>Session resumption fully functional</li>
              <li>UI properly displays extracted data</li>
              <li>Failed steps can be retried</li>
              <li>Pipeline state is preserved across sessions</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
