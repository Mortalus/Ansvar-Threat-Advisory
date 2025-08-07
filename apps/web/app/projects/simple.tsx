"use client";

import { useRouter } from 'next/navigation';

export default function SimpleProjectsPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          🛡️ Project Management (Simple)
        </h1>
        
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Debug Information</h2>
          <div className="space-y-2 text-sm">
            <div>✅ Route accessible at /projects/simple</div>
            <div>✅ Next.js app router working</div>
            <div>✅ React components rendering</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-4">
            <button 
              onClick={() => router.push('/')}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              ← Back to Main Application
            </button>
            
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded">
              <h3 className="font-medium text-yellow-800 mb-2">Debug Steps:</h3>
              <ol className="text-sm text-yellow-700 list-decimal list-inside space-y-1">
                <li>Check if API server is running on port 8000</li>
                <li>Verify frontend server is running on port 3000</li>
                <li>Test API endpoints: /api/projects</li>
                <li>Check browser console for errors</li>
                <li>Verify database migration completed</li>
              </ol>
            </div>

            <div className="p-4 bg-blue-50 border border-blue-200 rounded">
              <h3 className="font-medium text-blue-800 mb-2">Current Status:</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>✅ Database migration completed</li>
                <li>✅ Project models created</li>
                <li>✅ API endpoints implemented</li>
                <li>✅ Frontend components created</li>
                <li>❓ Need to verify API connectivity</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
