import React, { useState, useEffect } from 'react';
import { Plus, Play, Save, ArrowRight, Bot, FileText, GitBranch, Target, Trash2, Settings } from 'lucide-react';
import { WorkflowStep, Agent, Workflow } from '../types';

interface WorkflowBuilderProps {
  agents?: Agent[];
}

export function WorkflowBuilder({ agents = [] }: WorkflowBuilderProps) {
  const [workflowName, setWorkflowName] = useState('New Workflow');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [steps, setSteps] = useState<WorkflowStep[]>([
    {
      id: 'input-step',
      type: 'input',
      name: 'Document Upload',
      description: 'Upload system documentation, architecture diagrams, and requirements',
      position: { x: 100, y: 200 },
      connections: []
    },
    {
      id: 'output-step',
      type: 'output',
      name: 'Final Results',
      description: 'Complete analysis results and generated reports',
      position: { x: 800, y: 200 },
      connections: []
    }
  ]);
  const [selectedStep, setSelectedStep] = useState<string | null>(null);
  const [draggedItem, setDraggedItem] = useState<any>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStart, setConnectionStart] = useState<string | null>(null);
  const [draggedStep, setDraggedStep] = useState<string | null>(null);
  const [dragStartPos, setDragStartPos] = useState({ x: 0, y: 0 });
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [showValidation, setShowValidation] = useState(false);
  const [canvasOffset, setCanvasOffset] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [panStartOffset, setPanStartOffset] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [showNavigationHelp, setShowNavigationHelp] = useState(false);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const step = 50; // pixels to move per arrow key press
      
      switch (e.key) {
        case 'ArrowUp':
          e.preventDefault();
          setCanvasOffset(prev => ({ ...prev, y: prev.y + step }));
          break;
        case 'ArrowDown':
          e.preventDefault();
          setCanvasOffset(prev => ({ ...prev, y: prev.y - step }));
          break;
        case 'ArrowLeft':
          e.preventDefault();
          setCanvasOffset(prev => ({ ...prev, x: prev.x + step }));
          break;
        case 'ArrowRight':
          e.preventDefault();
          setCanvasOffset(prev => ({ ...prev, x: prev.x - step }));
          break;
        case '=':
        case '+':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            setZoom(prev => Math.min(prev + 0.1, 2));
          }
          break;
        case '-':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            setZoom(prev => Math.max(prev - 0.1, 0.5));
          }
          break;
        case '0':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            setZoom(1);
            setCanvasOffset({ x: 0, y: 0 });
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.1, 2));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.1, 0.5));
  };

  const resetView = () => {
    setZoom(1);
    setCanvasOffset({ x: 0, y: 0 });
  };
  const validateWorkflow = () => {
    const errors = [];
    
    // Check for required Input and Output steps
    const inputSteps = steps.filter(step => step.type === 'input');
    const outputSteps = steps.filter(step => step.type === 'output');
    
    // Check for exactly one input step
    if (inputSteps.length === 0) {
      errors.push('Add exactly one Input step to start your workflow');
    } else if (inputSteps.length > 1) {
      errors.push('Only one Input step is allowed per workflow');
    }
    
    // Check for exactly one output step
    if (outputSteps.length === 0) {
      errors.push('Add exactly one Output step to complete your workflow');
    } else if (outputSteps.length > 1) {
      errors.push('Only one Output step is allowed per workflow');
    }
    
    // Check that output step has no outgoing connections (must be final)
    if (outputSteps.length === 1) {
      const outputStep = outputSteps[0];
      if (outputStep.connections.length > 0) {
        errors.push('Output step must be the final step (no outgoing connections)');
      }
    }
    
    // Check that there's a connected path from THE input to THE output
    if (inputSteps.length === 1 && outputSteps.length === 1) {
      const inputStep = inputSteps[0];
      const outputStep = outputSteps[0];
      
      // Check that input step has outgoing connections
      if (inputStep.connections.length === 0) {
        errors.push('Input step must connect to at least one other step');
      }
      
      // Check that output step has incoming connections
      const hasIncomingConnection = steps.some(step => 
        step.connections.includes(outputStep.id)
      );
      if (!hasIncomingConnection) {
        errors.push('Output step must have at least one incoming connection');
      }
      
      // Check that there's a path from input to output
      const visited = new Set();
      const canReachOutput = (stepId: string): boolean => {
        if (visited.has(stepId)) return false;
        visited.add(stepId);
        
        const step = steps.find(s => s.id === stepId);
        if (!step) return false;
        
        // If this is the output step, we found a path
        if (step.id === outputStep.id) return true;
        
        // Check if any connected step can reach output
        return step.connections.some(connId => canReachOutput(connId));
      };
      
      const hasValidPath = canReachOutput(inputStep.id);
      if (!hasValidPath) {
        errors.push('There must be a connected path from Input to Output');
      }
    }
    
    // Check for orphaned steps (steps not connected to the main flow)
    if (inputSteps.length === 1 && outputSteps.length === 1) {
      const inputStep = inputSteps[0];
      const outputStep = outputSteps[0];
      const connectedSteps = new Set();
      
      // Find all steps reachable from input
      const findConnectedSteps = (stepId: string) => {
        if (connectedSteps.has(stepId)) return;
        connectedSteps.add(stepId);
        
        const step = steps.find(s => s.id === stepId);
        if (step) {
          step.connections.forEach(connId => findConnectedSteps(connId));
        }
      };
      
      findConnectedSteps(inputStep.id);
      
      // Find steps that connect to output
      steps.forEach(step => {
        if (step.connections.includes(outputStep.id)) {
          connectedSteps.add(step.id);
        }
      });
      
      connectedSteps.add(outputStep.id);
      
      // Check for orphaned steps
      const orphanedSteps = steps.filter(step => !connectedSteps.has(step.id));
      if (orphanedSteps.length > 0) {
        errors.push(`${orphanedSteps.length} step(s) are not connected to the main workflow`);
      }
    }
    
    return errors;
  };

  const addAgentStep = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId);
    if (!agent) return;

    const newStep: WorkflowStep = {
      id: Date.now().toString(),
      type: 'agent',
      agentId: agentId,
      name: agent.name,
      description: agent.description,
      position: { x: 100 + steps.length * 250, y: 100 },
      connections: []
    };
    setSteps([...steps, newStep]);
  };

  const removeStep = (stepId: string) => {
    // Prevent removal of input and output steps
    if (stepId === 'input-step' || stepId === 'output-step') {
      return;
    }
    setSteps(prev => prev.filter(s => s.id !== stepId));
    // Remove connections to this step
    setSteps(prev => prev.map(step => ({
      ...step,
      connections: step.connections.filter(conn => conn !== stepId)
    })));
  };

  const updateStep = (stepId: string, updates: Partial<WorkflowStep>) => {
    setSteps(prev => prev.map(step => 
      step.id === stepId ? { ...step, ...updates } : step
    ));
  };

  const connectSteps = (fromId: string, toId: string) => {
    setSteps(prev => prev.map(step => 
      step.id === fromId 
        ? { ...step, connections: [...step.connections, toId] }
        : step
    ));
  };

  const handleDragStart = (e: React.DragEvent, item: any) => {
    setDraggedItem(item);
    setIsDragging(true);
    e.dataTransfer.effectAllowed = 'copy';
    
    // Calculate offset from mouse to element center
    const rect = e.currentTarget.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - rect.left - rect.width / 2,
      y: e.clientY - rect.top - rect.height / 2
    });
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (draggedItem) {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = Math.max(0, e.clientX - rect.left - dragOffset.x);
      const y = Math.max(0, e.clientY - rect.top - dragOffset.y);
      
      const newStep: WorkflowStep = {
        id: Date.now().toString(),
        type: 'agent',
        agentId: draggedItem.id,
        name: draggedItem.name,
        description: draggedItem.description,
        position: { x, y },
        connections: []
      };
      
      setSteps(prev => [...prev, newStep]);
      setDraggedItem(null);
      setIsDragging(false);
    }
  };

  const handleStepDragStart = (e: React.DragEvent, step: WorkflowStep) => {
    e.dataTransfer.effectAllowed = 'move';
    setDraggedItem({ ...step, isStep: true });
    setIsDragging(true);
    
    const rect = e.currentTarget.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - rect.left - rect.width / 2,
      y: e.clientY - rect.top - rect.height / 2
    });
  };

  const handleStepDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (draggedItem && draggedItem.isStep) {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = Math.max(0, e.clientX - rect.left - dragOffset.x - canvasOffset.x);
      const y = Math.max(0, e.clientY - rect.top - dragOffset.y - canvasOffset.y);
      
      updateStep(draggedItem.id, { position: { x, y } });
      setDraggedItem(null);
      setIsDragging(false);
    }
  };

  const saveWorkflow = () => {
    const validationErrors = validateWorkflow();
    if (validationErrors.length > 0) {
      setValidationErrors(validationErrors);
      setShowValidation(true);
      return;
    }
    
    const workflow: Workflow = {
      id: Date.now().toString(),
      name: workflowName,
      description: workflowDescription,
      steps,
      isTemplate: false,
      createdAt: new Date().toISOString()
    };
    
    // Dispatch event to save workflow
    window.dispatchEvent(new CustomEvent('saveWorkflow', { detail: workflow }));
    
    // Navigate back to workflows page
    window.dispatchEvent(new CustomEvent('navigate', { detail: 'workflows' }));
  };
  
  // Update validation errors whenever steps change
  React.useEffect(() => {
    if (steps.length > 0) {
      const errors = validateWorkflow();
      setValidationErrors(errors);
    } else {
      setValidationErrors([]);
    }
  }, [steps]);
  const startConnection = (fromStepId: string) => {
    setIsConnecting(true);
    setConnectionStart(fromStepId);
  };

  const completeConnection = (toStepId: string) => {
    if (connectionStart && connectionStart !== toStepId) {
      connectSteps(connectionStart, toStepId);
    }
    setIsConnecting(false);
    setConnectionStart(null);
  };

  const cancelConnection = () => {
    setIsConnecting(false);
    setConnectionStart(null);
  };

  const autoSortSteps = () => {
    if (steps.length === 0) return;
    
    // Separate Input and Output steps
    const inputSteps = steps.filter(step => step.type === 'input');
    const outputSteps = steps.filter(step => step.type === 'output');
    const otherSteps = steps.filter(step => step.type !== 'input' && step.type !== 'output');
    
    // Create a map to track step levels
    const stepLevels = new Map<string, number>();
    const visited = new Set<string>();
    const stepOrder = new Map<string, number>();
    
    // Preserve original creation order for steps at the same level
    otherSteps.forEach((step, index) => {
      stepOrder.set(step.id, index);
    });
    
    // Input steps are always level 0
    inputSteps.forEach((step, index) => {
      stepLevels.set(step.id, 0);
      stepOrder.set(step.id, index);
    });
    
    // BFS to assign levels
    const queue = [...inputSteps.map(s => s.id)];
    
    while (queue.length > 0) {
      const currentId = queue.shift()!;
      if (visited.has(currentId)) continue;
      visited.add(currentId);
      
      const currentStep = [...inputSteps, ...otherSteps].find(s => s.id === currentId);
      if (!currentStep) continue;
      
      const currentLevel = stepLevels.get(currentId) || 0;
      
      // Process connections
      currentStep.connections.forEach(connId => {
        const connectedStep = [...otherSteps, ...outputSteps].find(s => s.id === connId);
        if (!connectedStep) return;
        
        const existingLevel = stepLevels.get(connId);
        const newLevel = currentLevel + 1;
        
        if (existingLevel === undefined || newLevel > existingLevel) {
          stepLevels.set(connId, newLevel);
          queue.push(connId);
        }
      });
    }
    
    // Find the maximum level for output positioning
    const maxLevel = Math.max(...Array.from(stepLevels.values()), 0) + 1;
    
    // Output steps are always at the final level
    outputSteps.forEach((step, index) => {
      stepLevels.set(step.id, maxLevel);
      stepOrder.set(step.id, index);
    });
    
    // Group steps by level
    const levelGroups = new Map<number, string[]>();
    stepLevels.forEach((level, stepId) => {
      if (!levelGroups.has(level)) {
        levelGroups.set(level, []);
      }
      levelGroups.get(level)!.push(stepId);
    });
    
    // Sort steps within each level by their original creation order
    levelGroups.forEach((stepIds, level) => {
      stepIds.sort((a, b) => (stepOrder.get(a) || 0) - (stepOrder.get(b) || 0));
    });
    
    // Position steps
    const updatedSteps = [...inputSteps, ...otherSteps, ...outputSteps].map(step => {
      const level = stepLevels.get(step.id) || 0;
      const levelSteps = levelGroups.get(level) || [];
      const indexInLevel = levelSteps.indexOf(step.id);
      const totalInLevel = levelSteps.length;
      
      // Enhanced positioning with Input first, Output last
      const x = 100 + level * 300; // Increased horizontal spacing
      
      // Center multiple steps vertically within their level
      const baseY = 200; // Center point
      const stepHeight = 120; // Space per step
      const totalHeight = (totalInLevel - 1) * stepHeight;
      const startY = baseY - totalHeight / 2;
      const y = startY + indexInLevel * stepHeight;
      
      return {
        ...step,
        position: { x, y }
      };
    });
    
    setSteps(updatedSteps);
  };

  const handleStepMouseDown = (e: React.MouseEvent, stepId: string) => {
    if (e.button !== 0) return; // Only left mouse button
    
    setDraggedStep(stepId);
    setDragStartPos({
      x: e.clientX,
      y: e.clientY
    });
    
    e.preventDefault();
    e.stopPropagation();
  };

  const handleCanvasMouseMove = (e: React.MouseEvent) => {
    if (draggedStep) {
      const deltaX = e.clientX - dragStartPos.x;
      const deltaY = e.clientY - dragStartPos.y;
      
      const step = steps.find(s => s.id === draggedStep);
      if (step) {
        const newX = Math.max(0, step.position.x + deltaX);
        const newY = Math.max(0, step.position.y + deltaY);
        updateStep(draggedStep, { position: { x: newX, y: newY } });
        setDragStartPos({ x: e.clientX, y: e.clientY });
      }
    }
    
    if (isPanning) {
      const deltaX = e.clientX - panStart.x;
      const deltaY = e.clientY - panStart.y;
      
      setCanvasOffset({
        x: panStartOffset.x + deltaX,
        y: panStartOffset.y + deltaY
      });
    }
  };

  const handleCanvasMouseUp = () => {
    setDraggedStep(null);
    setIsPanning(false);
  };
  const testWorkflow = () => {
    console.log('Testing workflow with steps:', steps);
    // Here you would trigger a test run
  };

  const handleCanvasMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return; // Only left mouse button
    if (e.target !== e.currentTarget) return; // Only on canvas background
    
    setIsPanning(true);
    setPanStart({ x: e.clientX, y: e.clientY });
    setPanStartOffset({ ...canvasOffset });
    e.preventDefault();
  };


  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex-1 max-w-2xl">
          <input
            type="text"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="text-3xl font-bold text-gray-900 bg-transparent border-none focus:outline-none focus:ring-2 focus:ring-purple-500 rounded px-2 w-full"
            placeholder="Workflow Name"
          />
          <input
            type="text"
            value={workflowDescription}
            onChange={(e) => setWorkflowDescription(e.target.value)}
            className="text-gray-600 mt-2 bg-transparent border-none focus:outline-none focus:ring-2 focus:ring-purple-500 rounded px-2 w-full"
            placeholder="Workflow description..."
          />
        </div>
        <div className="flex space-x-3">
          <button 
            onClick={autoSortSteps}
            disabled={steps.length === 0}
            className="flex items-center space-x-2 bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
            </svg>
            <span>Auto Sort</span>
          </button>
          <div className="flex items-center space-x-2 bg-white border border-gray-300 rounded-lg px-3 py-2">
            <button
              onClick={handleZoomOut}
              className="p-1 rounded hover:bg-gray-100 text-gray-600"
              title="Zoom Out (Ctrl + -)"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            </button>
            <span className="text-sm text-gray-600 min-w-[3rem] text-center">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={handleZoomIn}
              className="p-1 rounded hover:bg-gray-100 text-gray-600"
              title="Zoom In (Ctrl + +)"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
            <button
              onClick={resetView}
              className="p-1 rounded hover:bg-gray-100 text-gray-600 ml-2"
              title="Reset View (Ctrl + 0)"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
          <button
            onClick={() => setShowNavigationHelp(!showNavigationHelp)}
            className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Help</span>
          </button>
          <button 
            onClick={testWorkflow}
            className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            <Play className="w-4 h-4" />
            <span>Test Run</span>
          </button>
          <button 
            onClick={saveWorkflow}
            disabled={validationErrors.length > 0}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 ${
              validationErrors.length > 0
                ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:shadow-lg'
            }`}
          >
            <Save className="w-4 h-4" />
            <span>{validationErrors.length > 0 ? 'Fix Issues to Save' : 'Save Workflow'}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-6">
        {/* Navigation Help Modal */}
        {showNavigationHelp && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
              <div className="flex items-center justify-between p-6 border-b border-gray-200">
                <h2 className="text-xl font-bold text-gray-900">Navigation Controls</h2>
                <button
                  onClick={() => setShowNavigationHelp(false)}
                  className="p-2 rounded-lg hover:bg-gray-100"
                >
                  ×
                </button>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Canvas Navigation</h3>
                    <div className="space-y-2 text-sm text-gray-600">
                      <div className="flex items-center justify-between">
                        <span>Move Up</span>
                        <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">↑</kbd>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Move Down</span>
                        <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">↓</kbd>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Move Left</span>
                        <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">←</kbd>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Move Right</span>
                        <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">→</kbd>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Zoom Controls</h3>
                    <div className="space-y-2 text-sm text-gray-600">
                      <div className="flex items-center justify-between">
                        <span>Zoom In</span>
                        <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">Ctrl + +</kbd>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Zoom Out</span>
                        <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">Ctrl + -</kbd>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Reset View</span>
                        <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">Ctrl + 0</kbd>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Workflow Building</h3>
                    <div className="space-y-1 text-sm text-gray-600">
                      <p>• Drag agents from the left panel to the canvas</p>
                      <p>• Click connection points to link steps</p>
                      <p>• Use Auto Sort to organize your workflow</p>
                      <p>• Input and Output steps cannot be deleted</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Validation Panel */}
        {validationErrors.length > 0 && (
          <div className="col-span-5 bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-yellow-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-medium text-yellow-800 mb-2">
                  Workflow Issues ({validationErrors.length})
                </h3>
                <ul className="text-sm text-yellow-700 space-y-1">
                  {validationErrors.map((error, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <span className="w-1 h-1 bg-yellow-600 rounded-full mt-2 flex-shrink-0"></span>
                      <span>{error}</span>
                    </li>
                  ))}
                </ul>
                <p className="text-xs text-yellow-600 mt-2">
                  Fix these issues to enable workflow saving
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Available Agents */}
        <div className="col-span-2 bg-white rounded-lg border border-gray-200 p-4 space-y-4">
          <h3 className="font-semibold text-gray-900 mb-4">Workflow Components</h3>
          <p className="text-sm text-gray-600 mb-4">Drag agents to build your workflow. Input and Output steps are already provided.</p>
          
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Available Agents</h4>
            <div className="grid grid-cols-1 gap-3 max-h-[600px] overflow-y-auto">
              {agents.map(agent => (
                <div
                  key={agent.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, agent)}
                  className="p-4 rounded-lg border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-colors cursor-grab active:cursor-grabbing"
                >
                  <div className="flex items-start space-x-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <h4 className="text-sm font-medium text-gray-900 mb-1">{agent.name}</h4>
                      <p className="text-xs text-gray-600 mb-2 line-clamp-2">{agent.description}</p>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded capitalize">
                          {agent.category}
                        </span>
                        <span className="text-xs text-gray-500">
                          {agent.provider}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Canvas */}
        <div className="col-span-3 bg-white rounded-lg border border-gray-200 p-6 max-h-[800px] overflow-hidden">
          <div 
            className={`relative min-h-[600px] h-auto bg-gray-50 rounded-lg overflow-visible workflow-canvas ${
              isPanning ? 'cursor-grabbing' : 'cursor-grab'
            }`}
            style={{ 
              minWidth: '1200px', 
              minHeight: '800px',
              transform: `scale(${zoom})`,
              transformOrigin: 'top left'
            }}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onMouseDown={handleCanvasMouseDown}
            onMouseMove={handleCanvasMouseMove}
            onMouseUp={handleCanvasMouseUp}
            onMouseLeave={handleCanvasMouseUp}
          >
            {/* Grid Pattern */}
            <svg className="absolute inset-0 w-full h-full">
              <defs>
                <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                  <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e5e7eb" strokeWidth="1"/>
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />
            </svg>

            {/* Drop Zone Message */}
            {steps.length === 2 && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Plus className="w-8 h-8 text-gray-400" />
                  </div>
                  <p className="text-gray-500 text-lg font-medium">Drag agents here to build your workflow</p>
                  <p className="text-gray-400 text-sm mt-1">Connect Input → Agents → Output to create your processing pipeline</p>
                </div>
              </div>
            )}

            {/* Workflow Steps */}
            {steps.map((step, index) => {
              const getStepIcon = (stepType: string) => {
                switch (stepType) {
                  case 'input': return FileText;
                  case 'output': return Target;
                  case 'agent': return Bot;
                  case 'condition': return GitBranch;
                  default: return Bot;
                }
              };
              
              const getStepColor = (stepType: string) => {
                switch (stepType) {
                  case 'input': return 'bg-green-500';
                  case 'output': return 'bg-blue-500';
                  case 'agent': return 'bg-purple-500';
                  case 'condition': return 'bg-yellow-500';
                  default: return 'bg-gray-500';
                }
              };
              
              const Icon = getStepIcon(step.type);
              const stepColor = getStepColor(step.type);
              const agent = step.agentId ? agents.find(a => a.id === step.agentId) : null;
              const isRemovable = step.id !== 'input-step' && step.id !== 'output-step';
              
              return (
                <div 
                  key={step.id} 
                  className="absolute"
                  style={{
                    left: `${step.position.x + canvasOffset.x}px`,
                    top: `${step.position.y + canvasOffset.y}px`
                  }}
                >
                  <div
                    onMouseDown={(e) => handleStepMouseDown(e, step.id)}
                    className={`bg-white rounded-lg border-2 p-3 w-44 shadow-sm hover:shadow-md transition-all duration-200 cursor-move select-none group ${
                      selectedStep === step.id ? 'border-purple-500' : 'border-gray-200'
                    } ${draggedStep === step.id ? 'shadow-xl scale-105 z-10 rotate-1' : 'hover:scale-102'}`}
                    style={{
                      transform: draggedStep === step.id ? 'scale(1.05) rotate(1deg)' : 'scale(1)',
                      zIndex: draggedStep === step.id ? 10 : 1
                    }}
                    onClick={() => setSelectedStep(step.id)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <div className={`w-6 h-6 rounded ${stepColor} flex items-center justify-center`}>
                          <Icon className="w-4 h-4 text-white" />
                        </div>
                        <h4 className="font-medium text-gray-900 text-xs truncate flex-1">{step.name}</h4>
                      </div>
                      {isRemovable && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            removeStep(step.id);
                          }}
                          className="p-1 rounded hover:bg-red-100 text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                    
                    <p className="text-xs text-gray-600 mb-2 line-clamp-2 leading-tight">{step.description}</p>
                    
                    {agent && (
                      <div className="text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded truncate">
                        {agent.provider} - {agent.settings.model}
                      </div>
                    )}
                    
                    {/* Connection points */}
                    <div 
                      className="absolute -right-2 top-1/2 w-4 h-4 bg-purple-500 rounded-full border-2 border-white cursor-pointer hover:bg-purple-600 hover:scale-110 transition-all duration-200"
                      onClick={() => {
                        if (isConnecting) {
                          completeConnection(step.id);
                        } else {
                          startConnection(step.id);
                        }
                      }}
                      title={isConnecting ? "Click to connect here" : "Click to start connection"}
                    ></div>
                    <div 
                      className="absolute -left-2 top-1/2 w-4 h-4 bg-gray-400 rounded-full border-2 border-white cursor-pointer hover:bg-gray-500 hover:scale-110 transition-all duration-200"
                      onClick={() => {
                        if (isConnecting) {
                          completeConnection(step.id);
                        }
                      }}
                      title={isConnecting ? "Click to connect here" : "Input connection point"}
                    ></div>
                  </div>
                </div>
              );
            })}
            
            {/* Connection Lines */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              {steps.map(step => 
                step.connections.map(connectionId => {
                  const targetStep = steps.find(s => s.id === connectionId);
                  if (!targetStep) return null;
                  
                  const startX = step.position.x + canvasOffset.x + 192; // 48 * 4 (w-48)
                  const startY = step.position.y + canvasOffset.y + 50; // Half height of step box
                  const endX = targetStep.position.x + canvasOffset.x;
                  const endY = targetStep.position.y + canvasOffset.y + 50;
                  
                  // Always use smooth curves for all connections
                  const connectionIndex = step.connections.indexOf(connectionId);
                  const totalConnections = step.connections.length;
                  
                  // Create smooth curved paths for all connections
                  const offsetY = totalConnections > 1 
                    ? (connectionIndex - (totalConnections - 1) / 2) * 60 
                    : 0;
                  
                  // Calculate distance for curve intensity
                  const distance = Math.abs(endX - startX);
                  const curveIntensity = Math.min(distance * 0.4, 120); // Max 120px curve
                  
                  // Use cubic bezier for all connections with adaptive curves
                  const controlX1 = startX + curveIntensity;
                  const controlY1 = startY + offsetY * 0.3;
                  const controlX2 = endX - curveIntensity;
                  const controlY2 = endY + offsetY * 0.3;
                  
                  const pathData = `M ${startX} ${startY} C ${controlX1} ${controlY1}, ${controlX2} ${controlY2}, ${endX} ${endY}`;
                  
                  return (
                    <path
                      key={`${step.id}-${connectionId}`}
                      d={pathData}
                      stroke="#7c3aed"
                      strokeWidth="2.5"
                      fill="none"
                      markerEnd="url(#arrowhead)"
                      className="drop-shadow-sm hover:stroke-purple-600 transition-colors duration-200"
                      style={{
                        filter: 'drop-shadow(0 2px 4px rgba(124, 58, 237, 0.2))'
                      }}
                    />
                  );
                })
              )}
              <defs>
                <marker
                  id="arrowhead"
                  markerWidth="12"
                  markerHeight="8"
                  refX="11"
                  refY="4"
                  orient="auto"
                >
                  <polygon
                    points="0 0, 12 4, 0 8"
                    fill="#7c3aed"
                    className="drop-shadow-sm"
                  />
                </marker>
              </defs>
            </svg>
          </div>

          {/* Connection Mode Indicator */}
          {isConnecting && (
            <div className="fixed top-20 left-4 bg-purple-600 text-white px-4 py-2 rounded-lg shadow-lg z-20">
              <p className="text-sm">Connection Mode: Click on another step to connect</p>
              <p className="text-xs opacity-75">You can connect one step to multiple outputs (fork)</p>
              <button onClick={cancelConnection} className="text-xs underline ml-2">Cancel</button>
            </div>
          )}

          {/* Workflow Status */}
          <div className="fixed top-20 right-4 bg-white border border-gray-200 rounded-lg p-3 shadow-sm z-20">
            <div className="text-xs space-y-1">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-600 font-medium">Workflow Status</span>
                <div className={`w-2 h-2 rounded-full ${
                  validationErrors.length === 0 ? 'bg-green-500' : 'bg-yellow-500'
                }`}></div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Zoom:</span>
                <span className="font-medium text-blue-600">{Math.round(zoom * 100)}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Pan X:</span>
                <span className="font-medium text-gray-600">{canvasOffset.x}px</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Pan Y:</span>
                <span className="font-medium text-gray-600">{canvasOffset.y}px</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Input steps:</span>
                <span className={`font-medium ${steps.filter(s => s.type === 'input').length > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {steps.filter(s => s.type === 'input').length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Output steps:</span>
                <span className={`font-medium ${steps.filter(s => s.type === 'output').length > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {steps.filter(s => s.type === 'output').length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Connections:</span>
                <span className="font-medium text-blue-600">
                  {steps.reduce((total, step) => total + step.connections.length, 0)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Connected flow:</span>
                <span className={`font-medium ${validationErrors.some(e => e.includes('path from Input to Output')) ? 'text-red-600' : 'text-green-600'}`}>
                  {validationErrors.some(e => e.includes('path from Input to Output')) ? 'No' : 'Yes'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Issues:</span>
                <span className={`font-medium ${validationErrors.length === 0 ? 'text-green-600' : 'text-yellow-600'}`}>
                  {validationErrors.length}
                </span>
              </div>
            </div>
          </div>

          {/* Step Properties Panel */}
          {selectedStep && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-900">Step Properties</h4>
                <button
                  onClick={() => setSelectedStep(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              
              {(() => {
                const step = steps.find(s => s.id === selectedStep);
                if (!step) return null;
                
                return (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                      <input
                        type="text"
                        value={step.name}
                        onChange={(e) => updateStep(step.id, { name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                      <select
                        value={step.type}
                        disabled={step.id === 'input-step' || step.id === 'output-step'}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                      >
                        <option value="input">Input</option>
                        <option value="agent">Agent</option>
                        <option value="condition">Condition</option>
                        <option value="output">Output</option>
                      </select>
                    </div>
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                      <textarea
                        value={step.description}
                        onChange={(e) => updateStep(step.id, { description: e.target.value })}
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                      />
                    </div>
                    {step.type === 'agent' && (
                      <div className="col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Agent</label>
                        <select
                          value={step.agentId || ''}
                          onChange={(e) => updateStep(step.id, { agentId: e.target.value || undefined })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                        >
                          <option value="">Select an agent...</option>
                          {agents.map(agent => (
                            <option key={agent.id} value={agent.id}>{agent.name}</option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}
        </div>
      </div>

      {/* Validation Modal */}
      {showValidation && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <h2 className="text-xl font-bold text-gray-900">Workflow Issues</h2>
              </div>
              <button
                onClick={() => setShowValidation(false)}
                className="p-2 rounded-lg hover:bg-gray-100"
              >
                ×
              </button>
            </div>
            <div className="p-6">
              <p className="text-gray-600 mb-4">
                Please fix the following issues before saving your workflow:
              </p>
              <ul className="space-y-2">
                {validationErrors.map((error, index) => (
                  <li key={index} className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2 flex-shrink-0"></div>
                    <span className="text-sm text-gray-700">{error}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="flex items-center justify-end p-6 border-t border-gray-200 bg-gray-50">
              <button
                onClick={() => setShowValidation(false)}
                className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-2 rounded-lg hover:shadow-lg transition-all duration-200"
              >
                Got It
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}