'use client'

import { useState } from 'react'
import { api } from '@/lib/api'
import { Card } from '@/components/ui/card'

interface ReportOptions {
  format: 'pdf' | 'json' | 'csv' | 'excel'
  includeExecutiveSummary: boolean
  includeTechnicalDetails: boolean
  includeRiskMatrix: boolean
  includeDFD: boolean
  includeThreats: boolean
  includeRecommendations: boolean
  includeAppendices: boolean
}

interface ExportJob {
  id: string
  pipeline_id: string
  pipeline_name: string
  format: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  created_at: string
  completed_at?: string
  download_url?: string
  error_message?: string
  file_size?: number
}

export default function ReportExporter() {
  const [reportOptions, setReportOptions] = useState<ReportOptions>({
    format: 'pdf',
    includeExecutiveSummary: true,
    includeTechnicalDetails: true,
    includeRiskMatrix: true,
    includeDFD: true,
    includeThreats: true,
    includeRecommendations: true,
    includeAppendices: false
  })
  
  const [selectedPipeline, setSelectedPipeline] = useState('')
  const [exportJobs, setExportJobs] = useState<ExportJob[]>([])
  const [loading, setLoading] = useState(false)
  const [availablePipelines, setAvailablePipelines] = useState<any[]>([])

  // Simulate available pipelines (in real implementation, fetch from API)
  useState(() => {
    const pipelines = [
      { id: 'pipe-123', name: 'E-commerce App Threat Model', status: 'completed', created_at: '2025-08-08T05:00:00Z' },
      { id: 'pipe-456', name: 'API Security Analysis', status: 'completed', created_at: '2025-08-08T03:00:00Z' },
      { id: 'pipe-789', name: 'Mobile App Security Review', status: 'completed', created_at: '2025-08-07T15:00:00Z' }
    ]
    setAvailablePipelines(pipelines)
    if (pipelines.length > 0) {
      setSelectedPipeline(pipelines[0].id)
    }
  })

  const generateReport = async () => {
    if (!selectedPipeline) {
      alert('Please select a pipeline to export')
      return
    }

    try {
      setLoading(true)
      
      // Simulate API call to generate report
      const jobId = `job-${Date.now()}`
      const selectedPipelineData = availablePipelines.find(p => p.id === selectedPipeline)
      
      const newJob: ExportJob = {
        id: jobId,
        pipeline_id: selectedPipeline,
        pipeline_name: selectedPipelineData?.name || selectedPipeline,
        format: reportOptions.format,
        status: 'processing',
        created_at: new Date().toISOString(),
        file_size: Math.floor(Math.random() * 5000000) + 1000000 // 1-6MB
      }
      
      setExportJobs(prev => [newJob, ...prev])
      
      // Simulate processing time
      setTimeout(() => {
        setExportJobs(prev => prev.map(job => 
          job.id === jobId 
            ? { 
                ...job, 
                status: 'completed', 
                completed_at: new Date().toISOString(),
                download_url: `/api/reports/download/${jobId}.${reportOptions.format}`
              }
            : job
        ))
      }, 3000)
      
    } catch (error) {
      console.error('Failed to generate report:', error)
      alert('Failed to generate report. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const downloadReport = (job: ExportJob) => {
    if (job.status === 'completed' && job.download_url) {
      // In real implementation, this would trigger actual file download
      alert(`Download would start for: ${job.pipeline_name} (${job.format.toUpperCase()})`)
    }
  }

  const formatFileSize = (bytes: number) => {
    const mb = bytes / 1024 / 1024
    return `${mb.toFixed(1)} MB`
  }

  const getStatusColor = (status: ExportJob['status']) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100'
      case 'processing': return 'text-blue-600 bg-blue-100'
      case 'queued': return 'text-yellow-600 bg-yellow-100'
      case 'failed': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Report Generator</h1>
        <p className="text-gray-600">Generate comprehensive PDF reports and export threat model data</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Report Configuration */}
        <div className="space-y-6">
          <Card className="p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Report Configuration</h2>
            
            {/* Pipeline Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Pipeline
              </label>
              <select
                value={selectedPipeline}
                onChange={(e) => setSelectedPipeline(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Choose a completed pipeline...</option>
                {availablePipelines.map((pipeline) => (
                  <option key={pipeline.id} value={pipeline.id}>
                    {pipeline.name} ({new Date(pipeline.created_at).toLocaleDateString()})
                  </option>
                ))}
              </select>
            </div>

            {/* Format Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Export Format
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { value: 'pdf', label: 'PDF Report', icon: '📄' },
                  { value: 'json', label: 'JSON Data', icon: '📋' },
                  { value: 'csv', label: 'CSV Export', icon: '📊' },
                  { value: 'excel', label: 'Excel Report', icon: '📈' }
                ].map((format) => (
                  <button
                    key={format.value}
                    onClick={() => setReportOptions({...reportOptions, format: format.value as any})}
                    className={`p-3 text-left border rounded-md transition-colors ${
                      reportOptions.format === format.value
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center">
                      <span className="text-lg mr-2">{format.icon}</span>
                      <span className="font-medium">{format.label}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Content Options (for PDF) */}
            {reportOptions.format === 'pdf' && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Report Sections
                </label>
                <div className="space-y-2">
                  {[
                    { key: 'includeExecutiveSummary', label: 'Executive Summary' },
                    { key: 'includeTechnicalDetails', label: 'Technical Details' },
                    { key: 'includeRiskMatrix', label: 'Risk Assessment Matrix' },
                    { key: 'includeDFD', label: 'Data Flow Diagrams' },
                    { key: 'includeThreats', label: 'Threat Analysis' },
                    { key: 'includeRecommendations', label: 'Security Recommendations' },
                    { key: 'includeAppendices', label: 'Technical Appendices' }
                  ].map((option) => (
                    <label key={option.key} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={reportOptions[option.key as keyof ReportOptions] as boolean}
                        onChange={(e) => setReportOptions({
                          ...reportOptions,
                          [option.key]: e.target.checked
                        })}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700">{option.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Generate Button */}
            <button
              onClick={generateReport}
              disabled={loading || !selectedPipeline}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-3 rounded-md font-medium transition-colors"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Generating Report...
                </div>
              ) : (
                `Generate ${reportOptions.format.toUpperCase()} Report`
              )}
            </button>
          </Card>

          {/* Report Templates */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Report Templates</h3>
            <div className="space-y-3">
              {[
                { name: 'Executive Summary', description: 'High-level overview for stakeholders' },
                { name: 'Technical Deep Dive', description: 'Detailed technical analysis and findings' },
                { name: 'Compliance Report', description: 'Regulatory compliance assessment' },
                { name: 'Quick Assessment', description: 'Streamlined report for rapid reviews' }
              ].map((template) => (
                <button
                  key={template.name}
                  className="w-full text-left p-3 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
                >
                  <div className="font-medium text-gray-900">{template.name}</div>
                  <div className="text-sm text-gray-500">{template.description}</div>
                </button>
              ))}
            </div>
          </Card>
        </div>

        {/* Export History */}
        <div>
          <Card className="p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Export History</h2>
            
            {exportJobs.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">📄</div>
                <p>No exports generated yet</p>
                <p className="text-sm">Generate your first report to see it here</p>
              </div>
            ) : (
              <div className="space-y-4">
                {exportJobs.map((job) => (
                  <div key={job.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="font-medium text-gray-900">{job.pipeline_name}</h4>
                        <p className="text-sm text-gray-500">
                          {job.format.toUpperCase()} • {new Date(job.created_at).toLocaleString()}
                        </p>
                      </div>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                        {job.status}
                      </span>
                    </div>
                    
                    {job.status === 'processing' && (
                      <div className="mb-3">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                        </div>
                      </div>
                    )}
                    
                    <div className="flex justify-between items-center">
                      <div className="text-sm text-gray-500">
                        {job.file_size && `${formatFileSize(job.file_size)}`}
                        {job.completed_at && ` • Completed ${new Date(job.completed_at).toLocaleString()}`}
                      </div>
                      
                      {job.status === 'completed' && (
                        <button
                          onClick={() => downloadReport(job)}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm font-medium"
                        >
                          📥 Download
                        </button>
                      )}
                      
                      {job.status === 'failed' && (
                        <button
                          onClick={() => alert('Retry functionality would be implemented here')}
                          className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded text-sm font-medium"
                        >
                          🔄 Retry
                        </button>
                      )}
                    </div>
                    
                    {job.error_message && (
                      <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                        <span className="font-medium">Error:</span> {job.error_message}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}