// src/pages/Chat.jsx
import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../hooks/useAuth';
import useWebSocket from '../hooks/useWebSocket';
import chatService from '../services/chatService';
import ReactMarkdown from 'react-markdown';
import EventCard from '../components/EventCard';
import ConfirmationPrompt from '../components/ConfirmationPrompt';
import LedgerList from '../components/LedgerList';
import LedgerCard from '../components/LedgerCard';
import { 
  Send, 
  Trash2, 
  Wifi, 
  WifiOff, 
  Loader2,
  Bot,
  User,
  AlertCircle,
  Calendar,
  CalendarClock,
  CalendarCheck,
  Clock
} from 'lucide-react';

export default function Chat() {
  const { user, token } = useAuth();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Handle WebSocket messages
  function handleWebSocketMessage(data) {
    switch (data.type) {
      case 'history':
        setMessages(data.messages || []);
        break;
      
      case 'message':
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          role: data.role,
          content: data.content,
          timestamp: data.timestamp,
          intent: data.intent,
          message_type: data.message_type,
          metadata: data.metadata
        }]);
        setIsTyping(false);
        break;
      
      case 'typing':
        setIsTyping(data.is_typing);
        break;
      
      case 'error':
        setError(data.message);
        setIsTyping(false);
        break;
      
      default:
        console.log('Unknown message type:', data.type);
    }
  }

  // WebSocket connection
  const wsUrl = token ? chatService.createWebSocketUrl(token) : null;
  
  const {
    connectionStatus,
    lastMessage,
    error: wsError,
    sendMessage,
    isConnected
  } = useWebSocket(wsUrl, {
    onMessage: handleWebSocketMessage
  });

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Utility function to format timestamps
  const formatTimestamp = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
      });
    } catch (error) {
      console.error('Error formatting timestamp:', error);
      return 'Invalid time';
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle WebSocket errors
  useEffect(() => {
    if (wsError) {
      setError(wsError);
    }
  }, [wsError]);

  // Load chat history on component mount
  useEffect(() => {
    const loadChatHistory = async () => {
      if (!token) return;
      
      try {
        setIsLoading(true);
        const history = await chatService.getChatHistory();
        setMessages(history.messages || []);
      } catch (err) {
        console.error('Error loading chat history:', err);
        setError('Failed to load chat history');
      } finally {
        setIsLoading(false);
      }
    };

    loadChatHistory();
  }, [token]);

  // Handle event card actions
  const handleEventAction = (action, event) => {
    // For now, just send a text message about the action
    let message = '';
    switch (action) {
      case 'view':
        message = `Show details for "${event.summary}"`;
        break;
      case 'reschedule':
        message = `Reschedule "${event.summary}" to when?`;
        break;
      case 'cancel':
        message = `Cancel "${event.summary}"?`;
        break;
      default:
        return;
    }
    
    setInputMessage(message);
    inputRef.current?.focus();
  };

  // Handle confirmation prompt actions
  const handleConfirmation = (result) => {
    // Send confirmation result back via WebSocket
    let message = '';
    if (result.action === 'choose_slot') {
      // Option numbers start from 2 (since 1 is "Create anyway")
      // Backend expects "2", "3", "4", etc. or "choose option 2", "option 3"
      const optionNumber = result.option || (result.slotIndex + 2);
      message = `${optionNumber}`; // Simple number, backend will parse it
    } else if (result.action === 'confirm_anyway') {
      // Backend expects "1", "confirm", "yes", or "ok"
      message = '1'; // Option 1 = Create anyway
    }
    
    const success = sendMessage(message);
    if (!success) {
      setError('Failed to send confirmation');
    }
  };

  const handleConfirmationCancel = () => {
    const success = sendMessage('Cancel');
    if (!success) {
      setError('Failed to send cancellation');
    }
  };

  // Handle sending messages
  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || !isConnected) return;
    
    const messageText = inputMessage.trim();
    setInputMessage('');
    
    // Add user message to UI immediately
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    
    // Send via WebSocket
    const success = sendMessage(messageText);
    if (!success) {
      setError('Failed to send message');
    }
  };

  // Handle clearing chat history
  const handleClearChat = async () => {
    if (!window.confirm('Are you sure you want to clear all chat history?')) {
      return;
    }
    
    try {
      await chatService.clearChatHistory();
      setMessages([]);
      setError(null);
    } catch (err) {
      console.error('Error clearing chat history:', err);
      setError('Failed to clear chat history');
    }
  };

  // Connection status indicator
  const getConnectionStatus = () => {
    switch (connectionStatus) {
      case 'connected':
        return { icon: Wifi, color: 'text-green-600', text: 'Connected' };
      case 'connecting':
        return { icon: Loader2, color: 'text-yellow-600', text: 'Connecting...' };
      case 'error':
        return { icon: WifiOff, color: 'text-red-600', text: 'Connection Error' };
      default:
        return { icon: WifiOff, color: 'text-gray-600', text: 'Disconnected' };
    }
  };

  const connectionStatusInfo = getConnectionStatus();
  const StatusIcon = connectionStatusInfo.icon;

  // Quick action suggestions
  const quickActions = [
    { icon: Calendar, label: "Today's Schedule", message: "What's on my calendar today?" },
    { icon: CalendarClock, label: "Next Meeting", message: "What's my next meeting?" },
    { icon: Clock, label: "Free Time", message: "When am I free today?" },
    { icon: CalendarCheck, label: "This Week", message: "Show me this week's schedule" }
  ];

  // Handle quick action click
  const handleQuickAction = (message) => {
    setInputMessage(message);
    inputRef.current?.focus();
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="minimal-heading minimal-heading-lg mb-2">Authentication Required</h2>
          <p className="minimal-text-secondary">Please log in to access the chat.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-gray-50 flex flex-col max-h-screen">
      <div className="flex-1 flex flex-col min-h-0">
        {/* Header */}
        <div className="mb-4 flex-shrink-0 px-6 pt-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-3 mb-2">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-lg sm:text-2xl font-bold text-gray-900">
                    AI Assistant Chat
                  </h1>
                  <p className="text-gray-600 text-xs sm:text-sm hidden sm:block">
                    Chat with your AI assistant for calendar, Tally, and other tasks
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2 sm:space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2 px-2 py-1 sm:px-3 sm:py-2 bg-white rounded-lg border border-gray-200 shadow-sm">
                <StatusIcon className={`w-4 h-4 ${connectionStatusInfo.color} ${
                  connectionStatus === 'connecting' ? 'animate-spin' : ''
                }`} />
                <span className={`text-xs sm:text-sm font-medium ${connectionStatusInfo.color} hidden sm:inline`}>
                  {connectionStatusInfo.text}
                </span>
              </div>
              
              {/* Clear Chat Button */}
              <button
                onClick={handleClearChat}
                className="px-2 py-1 sm:px-4 sm:py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-1 sm:space-x-2 shadow-sm"
                disabled={messages.length === 0}
              >
                <Trash2 className="w-4 h-4" />
                <span className="hidden sm:inline">Clear Chat</span>
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl shadow-sm flex-shrink-0 mx-6">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-600 mr-3 flex-shrink-0" />
              <p className="text-red-700 font-medium">{error}</p>
            </div>
          </div>
        )}

        {/* Chat Container */}
        <div className="flex-1 bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden flex flex-col mx-6 mb-6 min-h-0 max-h-full">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 max-h-[60vh]">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
                  <p className="text-gray-600 font-medium">Loading chat history...</p>
                </div>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Bot className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Welcome to AI Chat</h3>
                  <p className="text-gray-600 mb-4">Start a conversation with your AI assistant</p>
                  
                  {/* Quick Actions */}
                  <div className="mt-6">
                    <p className="text-xs text-gray-500 mb-3 font-medium">Quick Actions:</p>
                    <div className="grid grid-cols-2 gap-2 max-w-md mx-auto">
                      {quickActions.map((action, idx) => {
                        const Icon = action.icon;
                        return (
                          <button
                            key={idx}
                            onClick={() => handleQuickAction(action.message)}
                            className="group px-4 py-3 bg-white border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all duration-200 flex flex-col items-center space-y-1 text-center"
                          >
                            <Icon className="w-5 h-5 text-gray-600 group-hover:text-blue-600 transition-colors" />
                            <span className="text-xs font-medium text-gray-700 group-hover:text-blue-600 transition-colors">
                              {action.label}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div className="mt-6 text-sm text-gray-500">
                    <p>Or try asking:</p>
                    <ul className="mt-2 space-y-1">
                      <li>• "What's on my calendar today?"</li>
                      <li>• "Show my profile"</li>
                      <li>• "Help me with Tally"</li>
                    </ul>
                  </div>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-4 animate-fadeIn`}
                  style={{
                    animation: 'fadeIn 0.3s ease-in'
                  }}
                >
                  <div
                    className={`max-w-xs lg:max-w-lg px-4 py-3 rounded-2xl shadow-sm ${
                      message.role === 'user'
                        ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white'
                        : 'bg-white border border-gray-200 text-gray-900'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      {message.role === 'assistant' && (
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                          <Bot className="w-4 h-4 text-white" />
                        </div>
                      )}
                      {message.role === 'user' && (
                        <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center flex-shrink-0">
                          <User className="w-4 h-4 text-white" />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        {message.role === 'assistant' ? (
                          <>
                            {/* Render confirmation prompt if available */}
                            {message.message_type === 'confirmation' && message.metadata && (
                              <ConfirmationPrompt
                                prompt={message.metadata}
                                onConfirm={handleConfirmation}
                                onCancel={handleConfirmationCancel}
                              />
                            )}
                            
                            {/* Render event card if available */}
                            {message.message_type === 'event_card' && message.metadata?.event && (
                              <EventCard
                                event={message.metadata.event}
                                onAction={handleEventAction}
                              />
                            )}
                            
                            {/* Render event list if available */}
                            {message.message_type === 'event_list' && message.metadata?.events && (
                              <div className="space-y-2">
                                {message.metadata.events.map((event, idx) => (
                                  <EventCard
                                    key={idx}
                                    event={event}
                                    onAction={handleEventAction}
                                  />
                                ))}
                              </div>
                            )}
                            
                            {/* Render ledger card (single ledger) if available */}
                            {message.message_type === 'ledger_card' && message.metadata?.ledger && (
                              <LedgerCard
                                ledger={message.metadata.ledger}
                                onAction={(ledger) => {
                                  // When user clicks, could show more details or refresh
                                  const ledgerName = ledger.name;
                                  setInputMessage(`Show detailed balance for ${ledgerName}`);
                                  inputRef.current?.focus();
                                }}
                              />
                            )}
                            
                            {/* Render ledger list (multiple ledgers) if available */}
                            {message.message_type === 'ledger_list' && message.metadata?.ledgers && (
                              <LedgerList
                                ledgers={message.metadata.ledgers}
                                searchTerm={message.metadata.search_term || ''}
                                onLedgerClick={(ledger) => {
                                  // When user clicks on a ledger, ask for its balance
                                  const ledgerName = ledger.name;
                                  setInputMessage(`Show balance for ${ledgerName}`);
                                  inputRef.current?.focus();
                                }}
                              />
                            )}
                            
                            {/* Default markdown rendering for text - skip if structured component is present */}
                            {!['confirmation', 'event_card', 'event_list', 'ledger_list', 'ledger_card'].includes(message.message_type) && (
                              <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-code:text-gray-800 prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-50 prose-pre:border prose-pre:border-gray-200">
                              <ReactMarkdown
                              components={{
                                a: ({ href, children }) => (
                                  <a 
                                    href={href} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:text-blue-800 underline decoration-2 underline-offset-2 hover:decoration-blue-800 transition-colors"
                                  >
                                    {children}
                                  </a>
                                ),
                                code: ({ children, className }) => {
                                  const isInline = !className;
                                  return isInline ? (
                                    <code className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-sm font-mono">
                                      {children}
                                    </code>
                                  ) : (
                                    <code className={className}>{children}</code>
                                  );
                                },
                                ul: ({ children }) => (
                                  <ul className="list-disc list-inside space-y-1 my-2">
                                    {children}
                                  </ul>
                                ),
                                ol: ({ children }) => (
                                  <ol className="list-decimal list-inside space-y-1 my-2">
                                    {children}
                                  </ol>
                                ),
                                li: ({ children }) => (
                                  <li className="text-gray-700">{children}</li>
                                ),
                                p: ({ children }) => (
                                  <p className="text-gray-700 leading-relaxed my-2">{children}</p>
                                ),
                                strong: ({ children }) => (
                                  <strong className="font-semibold text-gray-900">{children}</strong>
                                ),
                                em: ({ children }) => (
                                  <em className="italic text-gray-600">{children}</em>
                                ),
                                blockquote: ({ children }) => (
                                  <blockquote className="border-l-4 border-blue-200 pl-4 py-2 bg-blue-50 my-2 rounded-r">
                                    {children}
                                  </blockquote>
                                ),
                                h1: ({ children }) => (
                                  <h1 className="text-lg font-bold text-gray-900 my-2">{children}</h1>
                                ),
                                h2: ({ children }) => (
                                  <h2 className="text-base font-semibold text-gray-900 my-2">{children}</h2>
                                ),
                                h3: ({ children }) => (
                                  <h3 className="text-sm font-semibold text-gray-900 my-2">{children}</h3>
                                )
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                            </div>
                            )}
                          </>
                        ) : (
                          <p className="text-white leading-relaxed">{message.content}</p>
                        )}
                        <div className={`text-xs mt-2 flex items-center space-x-2 ${
                          message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                        }`}>
                          <span>{formatTimestamp(message.timestamp)}</span>
                          {message.intent && message.role === 'assistant' && (
                            <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs">
                              {message.intent.replace('_', ' ')}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex justify-start mb-4">
                <div className="bg-white border border-gray-200 text-gray-900 px-4 py-3 rounded-2xl shadow-sm">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-sm text-gray-500 ml-2">AI is typing...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4 bg-gray-50 flex-shrink-0">
            <form onSubmit={handleSendMessage} className="flex space-x-3">
              <div className="flex-1 relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder={isConnected ? "Type your message..." : "Connecting..."}
                  disabled={!isConnected || isLoading}
                  className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-500 transition-colors"
                />
                {isLoading && (
                  <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                    <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                  </div>
                )}
              </div>
              <button
                type="submit"
                disabled={!isConnected || !inputMessage.trim() || isLoading}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-2xl hover:from-blue-700 hover:to-blue-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2 shadow-sm"
              >
                <Send className="w-4 h-4" />
                <span className="hidden sm:inline">Send</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
