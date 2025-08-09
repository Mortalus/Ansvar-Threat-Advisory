import React, { useState, useRef, useEffect } from 'react';
import { 
  Upload, 
  FileText, 
  Send, 
  Download, 
  Trash2, 
  Bot, 
  User, 
  Settings,
  MessageSquare,
  File,
  Zap,
  Clock,
  Copy,
  Check,
  Database,
  Plus
} from 'lucide-react';
import { ChatSession, ChatMessage, UploadedDocument, LLMProvider, ContextSource } from '../types';

interface ChatWithDocumentProps {
  providers: LLMProvider[];
  contextSources: ContextSource[];
  chatSettings: {
    enabledProviders: string[];
    defaultModel: string;
    maxTokens: number;
    temperature: number;
  };
}

export function ChatWithDocument({ providers, contextSources, chatSettings }: ChatWithDocumentProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [showKnowledgeSources, setShowKnowledgeSources] = useState(false);
  const [selectedModel, setSelectedModel] = useState(chatSettings.defaultModel);
  const [selectedProvider, setSelectedProvider] = useState('');
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Get enabled providers and models
  const enabledProviders = providers.filter(p => 
    p.isActive && chatSettings.enabledProviders.includes(p.id)
  );

  const availableModels = enabledProviders.flatMap(provider => 
    provider.configuration.models?.map(model => ({
      provider: provider.name,
      providerId: provider.id,
      model,
      displayName: `${provider.name} - ${model}`
    })) || []
  );

  useEffect(() => {
    if (availableModels.length > 0 && !selectedProvider) {
      const defaultModel = availableModels.find(m => m.model === chatSettings.defaultModel) || availableModels[0];
      setSelectedModel(defaultModel.model);
      setSelectedProvider(defaultModel.providerId);
    }
  }, [availableModels, chatSettings.defaultModel]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeSession?.messages]);

  const estimateTokens = (text: string): number => {
    // Rough estimation: ~4 characters per token for English text
    return Math.ceil(text.length / 4);
  };

  const createNewSession = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      name: `Chat Session ${sessions.length + 1}`,
      documents: [],
      knowledgeSources: [],
      messages: [],
      model: selectedModel,
      provider: selectedProvider,
      totalTokens: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    setSessions(prev => [...prev, newSession]);
    setActiveSession(newSession);
  };

  const handleFileUpload = async (files: FileList) => {
    if (!activeSession) {
      // Create new session if none exists
      createNewSession();
    }

    const targetSession = activeSession || sessions[sessions.length - 1];
    if (!targetSession) return;

    const newDocuments: UploadedDocument[] = [];

    for (const file of Array.from(files)) {
      const content = await readFileContent(file);
      const tokenCount = estimateTokens(content);

      const document: UploadedDocument = {
        id: Date.now().toString() + Math.random(),
        name: file.name,
        size: file.size,
        type: file.type,
        content,
        tokenCount,
        uploadedAt: new Date().toISOString()
      };

      newDocuments.push(document);
    }

    const updatedSession = {
      ...targetSession,
      documents: [...targetSession.documents, ...newDocuments],
      updatedAt: new Date().toISOString()
    };

    setActiveSession(updatedSession);
    setSessions(prev => prev.map(s => s.id === targetSession.id ? updatedSession : s));
    setShowUpload(false);
  };

  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target?.result as string);
      reader.onerror = reject;
      reader.readAsText(file);
    });
  };

  const removeDocument = (documentId: string) => {
    if (!activeSession) return;

    const updatedSession = {
      ...activeSession,
      documents: activeSession.documents.filter(d => d.id !== documentId),
      updatedAt: new Date().toISOString()
    };

    setActiveSession(updatedSession);
    setSessions(prev => prev.map(s => s.id === activeSession.id ? updatedSession : s));
  };

  const sendMessage = async () => {
    if (!message.trim() || !activeSession || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message.trim(),
      timestamp: new Date().toISOString(),
      tokenCount: estimateTokens(message.trim())
    };

    const updatedMessages = [...activeSession.messages, userMessage];
    setMessage('');
    setIsLoading(true);

    // Update session with user message
    const sessionWithUserMessage = {
      ...activeSession,
      messages: updatedMessages,
      totalTokens: activeSession.totalTokens + (userMessage.tokenCount || 0),
      updatedAt: new Date().toISOString()
    };

    setActiveSession(sessionWithUserMessage);
    setSessions(prev => prev.map(s => s.id === activeSession.id ? sessionWithUserMessage : s));

    // Simulate AI response
    setTimeout(() => {
      const aiResponse = generateAIResponse(userMessage.content, activeSession.documents);
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: aiResponse,
        timestamp: new Date().toISOString(),
        tokenCount: estimateTokens(aiResponse)
      };

      const finalSession = {
        ...sessionWithUserMessage,
        messages: [...updatedMessages, assistantMessage],
        totalTokens: sessionWithUserMessage.totalTokens + (assistantMessage.tokenCount || 0),
        updatedAt: new Date().toISOString()
      };

      setActiveSession(finalSession);
      setSessions(prev => prev.map(s => s.id === activeSession.id ? finalSession : s));
      setIsLoading(false);
    }, 1500);
  };

  const generateAIResponse = (userMessage: string, documents: UploadedDocument[]): string => {
    // Simulate AI response based on documents and user message
    const knowledgeSourcesText = activeSession?.knowledgeSources.length 
      ? ` I also have access to ${activeSession.knowledgeSources.length} knowledge source(s) for additional context.`
      : '';
    
    if (documents.length === 0) {
      return `I don't have any documents to reference. Please upload some documents first so I can help you analyze their content.${knowledgeSourcesText}`;
    }

    const documentNames = documents.map(d => d.name).join(', ');
    const totalTokens = documents.reduce((sum, d) => sum + d.tokenCount, 0);

    if (userMessage.toLowerCase().includes('summary') || userMessage.toLowerCase().includes('summarize')) {
      return `Based on the uploaded documents (${documentNames}), here's a summary:\n\nThe documents contain approximately ${totalTokens} tokens of content. The main topics appear to cover various aspects related to your query. Key points include:\n\n• Document analysis and processing\n• Content structure and organization\n• Relevant information extraction\n\n${knowledgeSourcesText}\n\nWould you like me to focus on any specific aspect of these documents?`;
    }

    if (userMessage.toLowerCase().includes('what') && userMessage.toLowerCase().includes('document')) {
      return `You have uploaded ${documents.length} document(s): ${documentNames}. The total content is approximately ${totalTokens} tokens.${knowledgeSourcesText} I can help you analyze, summarize, or answer questions about the content in these documents.`;
    }

    return `I've analyzed your question in the context of the uploaded documents (${documentNames}). Based on the content, I can provide insights and answer questions about the material. The documents contain ${totalTokens} tokens of information that I can reference to help you.${knowledgeSourcesText}\n\nCould you be more specific about what aspect of the documents you'd like me to focus on?`;
  };

  const exportConversation = () => {
    if (!activeSession) return;

    const exportData = {
      sessionName: activeSession.name,
      model: `${selectedProvider} - ${activeSession.model}`,
      documents: activeSession.documents.map(d => ({
        name: d.name,
        size: d.size,
        tokenCount: d.tokenCount
      })),
      messages: activeSession.messages.map(m => ({
        role: m.role,
        content: m.content,
        timestamp: new Date(m.timestamp).toLocaleString(),
        tokenCount: m.tokenCount
      })),
      totalTokens: activeSession.totalTokens,
      exportedAt: new Date().toLocaleString()
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-session-${activeSession.name.replace(/\s+/g, '-').toLowerCase()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const copyMessage = (messageId: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedMessageId(messageId);
    setTimeout(() => setCopiedMessageId(null), 2000);
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Chat with Documents</h1>
          <p className="text-gray-600 mt-2">Upload documents and have intelligent conversations about their content</p>
        </div>
        <div className="flex space-x-3">
          {activeSession && (
            <>
              <button
                onClick={exportConversation}
                className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span>Export Chat</span>
              </button>
          </>
          )}
          <button
            onClick={createNewSession}
            className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-2 rounded-lg hover:shadow-lg transition-all duration-200"
          >
            New Chat Session
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sessions Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="font-semibold text-gray-900 mb-4">Chat Sessions</h3>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {sessions.map(session => (
                <div
                  key={session.id}
                  onClick={() => setActiveSession(session)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    activeSession?.id === session.id
                      ? 'bg-purple-100 border border-purple-300'
                      : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-1">
                    <MessageSquare className="w-4 h-4 text-purple-600" />
                    <span className="font-medium text-sm text-gray-900 truncate">{session.name}</span>
                  </div>
                  <div className="text-xs text-gray-600">
                    <div>{session.documents.length} docs • {session.messages.length} messages</div>
                    <div>{session.totalTokens.toLocaleString()} tokens</div>
                  </div>
                </div>
              ))}
              {sessions.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <MessageSquare className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  <p className="text-sm">No chat sessions yet</p>
                  <p className="text-xs">Create a new session to start</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="lg:col-span-3">
          {activeSession ? (
            <div 
              className={`bg-white rounded-xl border-2 flex flex-col h-[700px] transition-all duration-200 ${
                dragActive ? 'border-purple-500 bg-purple-50' : 'border-gray-200'
              }`}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              {/* Chat Header */}
              <div className="flex items-center justify-between p-4 border-b border-gray-200">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{activeSession.name}</h3>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span>{activeSession.documents.length} documents</span>
                      <span>{activeSession.totalTokens.toLocaleString()} tokens</span>
                      <div className="flex items-center space-x-1">
                        <Zap className="w-3 h-3" />
                        <span>{availableModels.find(m => m.model === activeSession.model)?.displayName || activeSession.model}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <select
                    value={selectedModel}
                    onChange={(e) => {
                      const selected = availableModels.find(m => m.model === e.target.value);
                      if (selected) {
                        setSelectedModel(selected.model);
                        setSelectedProvider(selected.providerId);
                      }
                    }}
                    className="text-sm border border-gray-300 rounded px-2 py-1"
                  >
                    {availableModels.map(model => (
                      <option key={`${model.providerId}-${model.model}`} value={model.model}>
                        {model.displayName}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Documents Bar */}
              {activeSession.documents.length > 0 && (
                <div className="p-3 border-b border-gray-200 bg-gray-50">
                  <div className="flex items-center space-x-2 mb-2">
                    <File className="w-4 h-4 text-gray-600" />
                    <span className="text-sm font-medium text-gray-700">Uploaded Documents</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {activeSession.documents.map(doc => (
                      <div key={doc.id} className="flex items-center space-x-2 bg-white px-3 py-1 rounded-lg border border-gray-200">
                        <FileText className="w-3 h-3 text-blue-500" />
                        <span className="text-xs text-gray-700">{doc.name}</span>
                        <span className="text-xs text-gray-500">({doc.tokenCount.toLocaleString()} tokens)</span>
                        <button
                          onClick={() => removeDocument(doc.id)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {activeSession.documents.length === 0 ? (
                  <div 
                    className={`text-center py-12 border-2 border-dashed rounded-lg transition-all duration-200 ${
                      dragActive ? 'border-purple-500 bg-purple-100' : 'border-gray-300'
                    }`}
                    onClick={() => setShowUpload(true)}
                  >
                    <Upload className={`w-16 h-16 mx-auto mb-4 ${dragActive ? 'text-purple-500' : 'text-gray-300'}`} />
                    <p className={`text-lg font-medium mb-2 ${dragActive ? 'text-purple-700' : 'text-gray-500'}`}>
                      {dragActive ? 'Drop your documents here' : 'Upload documents to start chatting'}
                    </p>
                    <p className={`text-sm ${dragActive ? 'text-purple-600' : 'text-gray-400'}`}>
                      {dragActive 
                        ? 'Release to upload your files'
                        : 'Drag & drop files here or click to browse'
                      }
                    </p>
                    <p className="text-xs text-gray-500 mt-2">
                      Supported: TXT, PDF, DOC, DOCX, MD, JSON, CSV
                    </p>
                  </div>
                ) : activeSession.messages.length === 0 ? (
                  <div className="text-center py-12">
                    <Bot className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500 mb-2">Start a conversation about your documents</p>
                    <p className="text-sm text-gray-400">
                      Ask questions about the uploaded documents
                    </p>
                  </div>
                ) : (
                  activeSession.messages.map(msg => (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-2' : 'order-1'}`}>
                        <div className={`flex items-start space-x-2 ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            msg.role === 'user' ? 'bg-purple-500' : 'bg-gray-500'
                          }`}>
                            {msg.role === 'user' ? (
                              <User className="w-4 h-4 text-white" />
                            ) : (
                              <Bot className="w-4 h-4 text-white" />
                            )}
                          </div>
                          <div className={`rounded-lg p-3 ${
                            msg.role === 'user' 
                              ? 'bg-purple-600 text-white' 
                              : 'bg-gray-100 text-gray-900'
                          }`}>
                            <div className="whitespace-pre-wrap">{msg.content}</div>
                            <div className={`flex items-center justify-between mt-2 text-xs ${
                              msg.role === 'user' ? 'text-purple-200' : 'text-gray-500'
                            }`}>
                              <span>{new Date(msg.timestamp).toLocaleTimeString()}</span>
                              <div className="flex items-center space-x-2">
                                {msg.tokenCount && <span>{msg.tokenCount} tokens</span>}
                                <button
                                  onClick={() => copyMessage(msg.id, msg.content)}
                                  className={`hover:${msg.role === 'user' ? 'text-white' : 'text-gray-700'}`}
                                >
                                  {copiedMessageId === msg.id ? (
                                    <Check className="w-3 h-3" />
                                  ) : (
                                    <Copy className="w-3 h-3" />
                                  )}
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="flex items-start space-x-2">
                      <div className="w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                      <div className="bg-gray-100 rounded-lg p-3">
                        <div className="flex items-center space-x-2">
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                          </div>
                          <span className="text-sm text-gray-600">Thinking...</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Message Input */}
              <div className="p-4 border-t border-gray-200">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder={activeSession.documents.length === 0 ? "Upload documents first..." : "Ask about your documents..."}
                    disabled={isLoading}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-100"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={!message.trim() || isLoading}
                    className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div 
              className={`bg-white rounded-xl border-2 border-dashed p-12 text-center transition-all duration-200 ${
                dragActive ? 'border-purple-500 bg-purple-50' : 'border-gray-300'
              }`}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              <Upload className={`w-20 h-20 mx-auto mb-6 ${dragActive ? 'text-purple-500' : 'text-gray-300'}`} />
              <h3 className={`text-2xl font-semibold mb-2 ${dragActive ? 'text-purple-700' : 'text-gray-900'}`}>
                {dragActive ? 'Drop Documents to Start' : 'Upload Documents to Begin'}
              </h3>
              <p className={`mb-6 ${dragActive ? 'text-purple-600' : 'text-gray-600'}`}>
                {dragActive 
                  ? 'Release to upload and create a new chat session'
                  : 'Upload documents first, then start an intelligent conversation about their content'
                }
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => setShowUpload(true)}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-8 py-3 rounded-lg hover:shadow-lg transition-all duration-200 mr-3"
                >
                  Choose Files
                </button>
                <button
                  onClick={createNewSession}
                  className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Create Empty Session
                </button>
              </div>
              <p className="text-sm text-gray-500 mt-4">
                Drag & drop files anywhere or use the upload button
              </p>
              <p className="text-xs text-gray-400 mt-2">
                Supported formats: TXT, PDF, DOC, DOCX, MD, JSON, CSV
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Upload Modal */}
      {showUpload && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">Upload Documents</h2>
              <button
                onClick={() => setShowUpload(false)}
                className="p-2 rounded-lg hover:bg-gray-100"
              >
                ×
              </button>
            </div>
            <div className="p-6">
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-purple-500 hover:bg-purple-50 transition-colors cursor-pointer"
              >
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium text-gray-900 mb-2">Upload Documents</p>
                <p className="text-sm text-gray-600 mb-4">
                  Drag and drop files here or click to browse
                </p>
                <p className="text-xs text-gray-500">
                  Supported formats: TXT, PDF, DOC, DOCX, MD, JSON, CSV
                </p>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".txt,.pdf,.doc,.docx,.md,.json,.csv"
                onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
                className="hidden"
              />
            </div>
          </div>
        </div>
      )}

      {/* Knowledge Sources Modal */}
      {showKnowledgeSources && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">Add Knowledge Sources</h2>
              <button
                onClick={() => setShowKnowledgeSources(false)}
                className="p-2 rounded-lg hover:bg-gray-100"
              >
                ×
              </button>
            </div>
            <div className="flex-1 p-6 overflow-y-auto">
              <p className="text-gray-600 mb-4">
                Select knowledge sources to provide additional context for your chat session.
              </p>
              
              <div className="space-y-3">
                {contextSources.filter(source => source.isActive).map(source => {
                  const Icon = getContextSourceIcon(source.type);
                  const isSelected = activeSession?.knowledgeSources.includes(source.id) || false;
                  
                  return (
                    <div
                      key={source.id}
                      onClick={() => {
                        if (isSelected) {
                          removeKnowledgeSource(source.id);
                        } else {
                          addKnowledgeSource(source.id);
                        }
                      }}
                      className={`flex items-center space-x-3 p-4 rounded-lg border transition-colors cursor-pointer ${
                        isSelected 
                          ? 'border-purple-300 bg-purple-50' 
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className={`w-10 h-10 ${getContextSourceColor(source.type)} rounded-lg flex items-center justify-center`}>
                        <Icon className="w-5 h-5 text-white" />
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{source.name}</h4>
                        <p className="text-sm text-gray-600 capitalize">{source.type.replace('_', ' ')}</p>
                        <p className="text-xs text-gray-500 mt-1">{source.description}</p>
                      </div>
                      <div className={`w-5 h-5 rounded border-2 ${
                        isSelected ? 'bg-purple-600 border-purple-600' : 'border-gray-300'
                      }`}>
                        {isSelected && (
                          <div className="w-full h-full flex items-center justify-center">
                            <div className="w-2 h-2 rounded-full bg-white"></div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
                
                {contextSources.filter(source => source.isActive).length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <Database className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p className="text-lg font-medium mb-2">No Knowledge Sources Available</p>
                    <p className="text-sm">Configure knowledge sources in Settings to use them in chat sessions.</p>
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
              <div className="text-sm text-gray-600">
                {activeSession?.knowledgeSources.length || 0} knowledge source(s) selected
              </div>
              <button
                onClick={() => setShowKnowledgeSources(false)}
                className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-2 rounded-lg hover:shadow-lg transition-all duration-200"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}