'use client'

import { useEffect, useRef, useState } from 'react'
import mermaid from 'mermaid'
import { ZoomIn, ZoomOut, Maximize, Download, RotateCcw, Move } from 'lucide-react'

interface InteractiveMermaidProps {
  chart: string
  title?: string
}

export function InteractiveMermaid({ chart, title = "DFD Diagram" }: InteractiveMermaidProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGElement | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [renderError, setRenderError] = useState<string | null>(null)

  // Initialize Mermaid
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'base',
      themeVariables: {
        background: '#0a0a0f',
        primaryColor: '#8b5cf6',
        primaryTextColor: '#ffffff',
        primaryBorderColor: '#6d28d9',
        lineColor: '#9ca3af',
        secondaryColor: '#374151',
        tertiaryColor: '#1f2937',
        mainBkg: '#374151',
        secondBkg: '#4b5563',
        tertiaryColor: '#6b7280',
        primaryBorderColor: '#8b5cf6',
        primaryTextColor: '#ffffff',
        lineColor: '#9ca3af',
        sectionBkgColor: '#1f2937',
        altSectionBkgColor: '#374151',
        gridColor: '#4b5563',
        c0: '#ff6b6b', // External entities - red
        c1: '#4c6ef5', // Processes - blue  
        c2: '#37b24d', // Assets - green
        c3: '#ffd43b', // Trust boundaries - yellow
        fontSize: '14px',
        fontFamily: 'ui-sans-serif, system-ui, sans-serif'
      },
      flowchart: {
        useMaxWidth: false,
        htmlLabels: true,
        curve: 'basis'
      }
    })
  }, [])

  // Render diagram when chart changes
  useEffect(() => {
    if (!chart || !containerRef.current) return

    const renderDiagram = async () => {
      try {
        setRenderError(null)
        // Clear previous diagram
        if (containerRef.current) {
          containerRef.current.innerHTML = ''
        }

        // Validate and render
        const { svg } = await mermaid.render(`mermaid-${Date.now()}`, chart)
        
        if (containerRef.current) {
          containerRef.current.innerHTML = svg
          
          // Get SVG element reference
          const svgElement = containerRef.current.querySelector('svg')
          if (svgElement) {
            svgRef.current = svgElement
            
            // Style the SVG
            svgElement.style.width = '100%'
            svgElement.style.height = '100%'
            svgElement.style.maxWidth = 'none'
            svgElement.style.maxHeight = 'none'
            
            // Reset transform
            setTransform({ x: 0, y: 0, scale: 1 })
            applyTransform(svgElement, { x: 0, y: 0, scale: 1 })
          }
        }
      } catch (error) {
        console.error('Mermaid render error:', error)
        setRenderError(error instanceof Error ? error.message : 'Failed to render diagram')
      }
    }

    renderDiagram()
  }, [chart])

  const applyTransform = (element: SVGElement, newTransform: typeof transform) => {
    element.style.transform = `translate(${newTransform.x}px, ${newTransform.y}px) scale(${newTransform.scale})`
    element.style.transformOrigin = 'center center'
  }

  const handleZoomIn = () => {
    if (!svgRef.current) return
    const newTransform = { ...transform, scale: Math.min(transform.scale * 1.2, 3) }
    setTransform(newTransform)
    applyTransform(svgRef.current, newTransform)
  }

  const handleZoomOut = () => {
    if (!svgRef.current) return
    const newTransform = { ...transform, scale: Math.max(transform.scale / 1.2, 0.1) }
    setTransform(newTransform)
    applyTransform(svgRef.current, newTransform)
  }

  const handleReset = () => {
    if (!svgRef.current) return
    const newTransform = { x: 0, y: 0, scale: 1 }
    setTransform(newTransform)
    applyTransform(svgRef.current, newTransform)
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true)
    setDragStart({ x: e.clientX - transform.x, y: e.clientY - transform.y })
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !svgRef.current) return
    
    const newTransform = {
      ...transform,
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    }
    setTransform(newTransform)
    applyTransform(svgRef.current, newTransform)
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  // Handle wheel events with proper passive handling
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault()
      if (!svgRef.current) return
      
      const delta = e.deltaY > 0 ? 0.9 : 1.1
      const newScale = Math.min(Math.max(transform.scale * delta, 0.1), 3)
      
      setTransform(prev => {
        const newTransform = { ...prev, scale: newScale }
        if (svgRef.current) {
          applyTransform(svgRef.current, newTransform)
        }
        return newTransform
      })
    }

    container.addEventListener('wheel', handleWheel, { passive: false })
    
    return () => {
      container.removeEventListener('wheel', handleWheel)
    }
  }, [transform.scale])

  const handleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  const handleExport = async () => {
    if (!svgRef.current) return

    try {
      // Create canvas for export
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      // Get SVG dimensions
      const bbox = svgRef.current.getBBox()
      canvas.width = bbox.width + 40
      canvas.height = bbox.height + 40

      // Convert SVG to image
      const svgData = new XMLSerializer().serializeToString(svgRef.current)
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })
      const svgUrl = URL.createObjectURL(svgBlob)
      
      const img = new Image()
      img.onload = () => {
        ctx.fillStyle = '#0a0a0f'
        ctx.fillRect(0, 0, canvas.width, canvas.height)
        ctx.drawImage(img, 20, 20)
        
        // Download
        const link = document.createElement('a')
        link.download = `${title.replace(/\s+/g, '_')}.png`
        link.href = canvas.toDataURL('image/png')
        link.click()
        
        URL.revokeObjectURL(svgUrl)
      }
      img.src = svgUrl
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  if (renderError) {
    return (
      <div className="h-full flex items-center justify-center bg-red-500/10 border border-red-500/30 rounded-xl">
        <div className="text-center p-6">
          <div className="text-red-500 text-lg font-semibold mb-2">Diagram Render Error</div>
          <div className="text-red-400 text-sm">{renderError}</div>
          <div className="text-gray-400 text-xs mt-2">Check your JSON syntax and component references</div>
        </div>
      </div>
    )
  }

  return (
    <div className={`relative ${isFullscreen ? 'fixed inset-0 z-50 bg-[#0a0a0f]' : 'h-full'}`}>
      {/* Controls */}
      <div className="absolute top-4 right-4 z-10 flex gap-2 bg-[#1a1a2e]/90 backdrop-blur rounded-lg p-2">
        <button
          onClick={handleZoomIn}
          className="p-2 hover:bg-purple-600/20 rounded-lg transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4 text-gray-400" />
        </button>
        
        <button
          onClick={handleZoomOut}
          className="p-2 hover:bg-purple-600/20 rounded-lg transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4 text-gray-400" />
        </button>
        
        <button
          onClick={handleReset}
          className="p-2 hover:bg-purple-600/20 rounded-lg transition-colors"
          title="Reset View"
        >
          <RotateCcw className="w-4 h-4 text-gray-400" />
        </button>
        
        <div className="w-px bg-gray-600 my-1" />
        
        <button
          onClick={handleFullscreen}
          className="p-2 hover:bg-purple-600/20 rounded-lg transition-colors"
          title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
        >
          <Maximize className="w-4 h-4 text-gray-400" />
        </button>
        
        <button
          onClick={handleExport}
          className="p-2 hover:bg-purple-600/20 rounded-lg transition-colors"
          title="Export PNG"
        >
          <Download className="w-4 h-4 text-gray-400" />
        </button>
      </div>

      {/* Info Panel */}
      <div className="absolute top-4 left-4 z-10 bg-[#1a1a2e]/90 backdrop-blur rounded-lg p-3 text-sm">
        <div className="flex items-center gap-2 text-gray-400 mb-1">
          <Move className="w-3 h-3" />
          <span>Drag to pan • Scroll to zoom</span>
        </div>
        <div className="text-xs text-gray-500">
          Scale: {(transform.scale * 100).toFixed(0)}%
        </div>
      </div>

      {/* Diagram Container */}
      <div 
        ref={containerRef}
        className="h-full w-full overflow-hidden cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ 
          background: '#0a0a0f',
          userSelect: 'none'
        }}
      />

      {/* Fullscreen overlay */}
      {isFullscreen && (
        <div 
          className="absolute inset-0 bg-black/50"
          onClick={handleFullscreen}
        />
      )}
    </div>
  )
}