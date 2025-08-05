// apps/web/app/test-upload/page.tsx
'use client'

import { useState, useRef } from 'react'

export default function TestUpload() {
  const [file, setFile] = useState<File | null>(null)
  const [method, setMethod] = useState<string>('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Method 1: Using ref and click()
  const handleMethod1Click = () => {
    console.log('Method 1: Clicking via ref')
    setMethod('Method 1: ref.click()')
    fileInputRef.current?.click()
  }

  // Method 2: Using label htmlFor
  const handleMethod2 = () => {
    console.log('Method 2: Label clicked')
    setMethod('Method 2: Label htmlFor')
  }

  // Method 3: Direct button inside label
  const handleMethod3 = () => {
    console.log('Method 3: Direct label wrap')
    setMethod('Method 3: Direct label wrap')
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    console.log('File input changed:', e.target.files)
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      console.log('File selected:', selectedFile.name, selectedFile.type, selectedFile.size)
    }
  }

  const resetFile = () => {
    setFile(null)
    setMethod('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-3xl font-bold mb-8">File Upload Test Page</h1>
      
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Current Status */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Current Status:</h2>
          <p>Selected File: {file ? file.name : 'None'}</p>
          <p>Last Method Used: {method || 'None'}</p>
          {file && (
            <button 
              onClick={resetFile}
              className="mt-4 px-4 py-2 bg-red-600 rounded hover:bg-red-700"
            >
              Reset
            </button>
          )}
        </div>

        {/* Method 1: useRef with click() */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Method 1: useRef + click()</h2>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileChange}
            className="hidden"
            accept=".txt,.pdf,.docx"
          />
          <button
            onClick={handleMethod1Click}
            className="px-6 py-3 bg-blue-600 rounded hover:bg-blue-700 transition"
          >
            Choose File (Method 1)
          </button>
        </div>

        {/* Method 2: Label with htmlFor */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Method 2: Label htmlFor</h2>
          <input
            id="file-input-method2"
            type="file"
            onChange={(e) => {
              handleMethod2()
              handleFileChange(e)
            }}
            className="hidden"
            accept=".txt,.pdf,.docx"
          />
          <label 
            htmlFor="file-input-method2"
            className="inline-block px-6 py-3 bg-green-600 rounded hover:bg-green-700 transition cursor-pointer"
          >
            Choose File (Method 2)
          </label>
        </div>

        {/* Method 3: Button wrapped in label */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Method 3: Label Wrapped Button</h2>
          <label className="inline-block cursor-pointer">
            <input
              type="file"
              onChange={(e) => {
                handleMethod3()
                handleFileChange(e)
              }}
              className="hidden"
              accept=".txt,.pdf,.docx"
            />
            <span className="inline-block px-6 py-3 bg-purple-600 rounded hover:bg-purple-700 transition">
              Choose File (Method 3)
            </span>
          </label>
        </div>

        {/* Method 4: Visible input for testing */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Method 4: Visible Input (Debug)</h2>
          <input
            type="file"
            onChange={(e) => {
              setMethod('Method 4: Direct visible input')
              handleFileChange(e)
            }}
            className="block w-full p-2 border border-gray-600 rounded bg-gray-700"
            accept=".txt,.pdf,.docx"
          />
        </div>

        {/* Method 5: Simple HTML button with onClick handler */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Method 5: Document.getElementById</h2>
          <input
            id="file-input-method5"
            type="file"
            onChange={(e) => {
              setMethod('Method 5: getElementById')
              handleFileChange(e)
            }}
            className="hidden"
            accept=".txt,.pdf,.docx"
          />
          <button
            onClick={() => {
              console.log('Method 5: Using getElementById')
              const input = document.getElementById('file-input-method5') as HTMLInputElement
              if (input) {
                input.click()
              } else {
                console.error('Could not find input element')
              }
            }}
            className="px-6 py-3 bg-orange-600 rounded hover:bg-orange-700 transition"
          >
            Choose File (Method 5)
          </button>
        </div>

        {/* Console Log Display */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Instructions:</h2>
          <ol className="list-decimal list-inside space-y-2">
            <li>Open browser console (F12 or right-click → Inspect → Console)</li>
            <li>Try each method above</li>
            <li>Check console for any errors or logs</li>
            <li>Report which methods work and which don't</li>
          </ol>
        </div>
      </div>
    </div>
  )
}