import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

interface MermaidViewerProps {
  chart: string;
  className?: string;
}

export function MermaidViewer({ chart, className = '' }: MermaidViewerProps) {
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose',
      fontFamily: 'Inter, system-ui, sans-serif',
      fontSize: 14,
      flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis'
      }
    });
  }, []);

  useEffect(() => {
    if (elementRef.current && chart) {
      // Clear previous content
      elementRef.current.innerHTML = '';
      
      // Generate unique ID for this diagram
      const id = `mermaid-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      
      try {
        mermaid.render(id, chart).then(({ svg }) => {
          if (elementRef.current) {
            elementRef.current.innerHTML = svg;
          }
        }).catch((error) => {
          console.error('Mermaid rendering error:', error);
          if (elementRef.current) {
            elementRef.current.innerHTML = `
              <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p class="text-red-700 font-medium">Diagram Rendering Error</p>
                <p class="text-red-600 text-sm mt-1">Unable to render the Mermaid diagram. Please check the syntax.</p>
                <details class="mt-2">
                  <summary class="text-red-600 text-sm cursor-pointer">Error Details</summary>
                  <pre class="text-xs text-red-500 mt-1 whitespace-pre-wrap">${error.message}</pre>
                </details>
              </div>
            `;
          }
        });
      } catch (error) {
        console.error('Mermaid error:', error);
        if (elementRef.current) {
          elementRef.current.innerHTML = `
            <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p class="text-red-700 font-medium">Diagram Error</p>
              <p class="text-red-600 text-sm">Invalid Mermaid syntax</p>
            </div>
          `;
        }
      }
    }
  }, [chart]);

  return (
    <div 
      ref={elementRef} 
      className={`mermaid-container ${className}`}
      style={{ minHeight: '200px' }}
    />
  );
}