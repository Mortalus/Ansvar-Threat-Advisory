import React, { Suspense, lazy } from 'react';

// Lazy load the MermaidViewer to avoid loading mermaid in the main bundle
const MermaidViewer = lazy(() => import('./MermaidViewer'));

interface LazyMermaidProps {
  chart: string;
  className?: string;
}

const MermaidLoadingFallback = () => (
  <div className="flex items-center justify-center p-8 border border-gray-200 rounded-lg bg-gray-50">
    <div className="text-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto mb-2"></div>
      <p className="text-gray-600 text-sm">Loading diagram...</p>
    </div>
  </div>
);

export function LazyMermaid({ chart, className }: LazyMermaidProps) {
  return (
    <Suspense fallback={<MermaidLoadingFallback />}>
      <MermaidViewer chart={chart} className={className} />
    </Suspense>
  );
}