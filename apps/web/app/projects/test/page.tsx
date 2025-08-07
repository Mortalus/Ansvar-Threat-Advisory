"use client";

export default function TestProjectsPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          🛡️ Project Management Test Page
        </h1>
        <p className="text-gray-600 mb-6">
          This is a test page to verify the /projects route is working.
        </p>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Route Status</h2>
          <div className="space-y-2 text-sm">
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 bg-green-500 rounded-full"></span>
              <span>✅ Route accessible at /projects</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 bg-green-500 rounded-full"></span>
              <span>✅ Next.js app router working</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 bg-green-500 rounded-full"></span>
              <span>✅ React components rendering</span>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded">
            <p className="text-blue-800 text-sm">
              If you can see this page, the routing is working correctly. 
              The issue may be with the component imports or API connections.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
