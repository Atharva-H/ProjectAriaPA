// src/pages/Chat.jsx
import { useState, useEffect, useRef } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import useWebSocket from '../hooks/useWebSocket';
import chatService from '../services/chatService';
import ReactMarkdown from 'react-markdown';
import EventCard from '../components/EventCard';
import TaskCard from '../components/TaskCard';
import ConfirmationPrompt from '../components/ConfirmationPrompt';
import LedgerList from '../components/LedgerList';
import LedgerCard from '../components/LedgerCard';
import {
  Send,
  Loader2,
  Mic,
  Square
} from 'lucide-react';

export default function Chat() {
  const { user, token } = useAuth();
  const { selectedDate } = useOutletContext(); // Use context from DashboardLayout
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const mediaStreamRef = useRef(null);
  const isRecordingRef = useRef(false);
  const mimeTypeRef = useRef('audio/webm');

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

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle WebSocket errors
  useEffect(() => {
    if (wsError) {
      setError(wsError);
    }
  }, [wsError]);

  // Load chat history when selectedDate changes
  useEffect(() => {
    const loadChatHistory = async () => {
      if (!token) return;

      try {
        setIsLoading(true);
        // If selectedDate is provided, we fetch history.
        if (selectedDate) {
          const history = await chatService.getChatHistory(50, selectedDate);
          setMessages(history.messages || []);
        } else {
          setMessages([]);
        }
      } catch (err) {
        console.error('Error loading chat history:', err);
        setError('Failed to load chat history');
      } finally {
        setIsLoading(false);
      }
    };

    loadChatHistory();
  }, [token, selectedDate]);


  // Handle event card actions
  const handleEventAction = (action, event) => {
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

  // Handle task card actions
  const handleTaskAction = (action, task) => {
    let message = '';
    switch (action) {
      case 'mark_done':
        message = `Mark task "${task.title}" as done`;
        break;
      default:
        return;
    }
    // Optimistically update the UI or just send the message
    // For now, we just send the message and expect the backend to confirm
    setInputMessage(message);
    inputRef.current?.focus();
    // Alternatively, we could auto-send:
    // sendMessage(message);
  };

  // Handle confirmation prompt actions
  const handleConfirmation = (result) => {
    let message = '';
    if (result.action === 'choose_slot') {
      const optionNumber = result.option || (result.slotIndex + 2);
      message = `${optionNumber}`;
    } else if (result.action === 'confirm_anyway') {
      message = '1';
    }
    sendMessage(message);
  };

  const handleConfirmationCancel = () => {
    sendMessage('Cancel');
  };

  // Handle sending messages
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || !isConnected) return;

    const messageText = inputMessage.trim();
    setInputMessage('');

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    const success = sendMessage(messageText);
    if (!success) {
      setError('Failed to send message');
    }
  };

  // Handle audio recording
  const startRecording = async () => {
    if (isRecording || mediaRecorderRef.current) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, sampleRate: 44100 }
      });
      mediaStreamRef.current = stream;

      let mimeType = 'audio/webm';
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4';
      }

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const wasRecording = isRecordingRef.current;
        isRecordingRef.current = false;
        setIsRecording(false);

        if (mediaStreamRef.current) {
          mediaStreamRef.current.getTracks().forEach(track => track.stop());
          mediaStreamRef.current = null;
        }
        mediaRecorderRef.current = null;

        if (!wasRecording || audioChunksRef.current.length === 0) return;

        const savedMimeType = mimeTypeRef.current;
        const audioBlob = new Blob(audioChunksRef.current, { type: savedMimeType });

        let extension = 'webm';
        let finalMimeType = 'audio/webm';
        if (savedMimeType.includes('mp4')) {
          extension = 'm4a';
          finalMimeType = 'audio/mp4';
        }

        const audioFile = new File([audioBlob], `recording.${extension}`, { type: finalMimeType });

        setIsTranscribing(true);
        try {
          const transcript = await chatService.uploadAudio(audioFile);
          if (transcript && transcript.trim()) {
            setInputMessage(transcript);
            inputRef.current?.focus();
            setError(null);
          }
        } catch (err) {
          console.error('Error transcribing audio:', err);
          setError('Failed to transcribe audio.');
        } finally {
          setIsTranscribing(false);
          audioChunksRef.current = [];
        }
      };

      mimeTypeRef.current = mimeType;
      mediaRecorder.start(1000);
      isRecordingRef.current = true;
      setIsRecording(true);
      setError(null);
    } catch (err) {
      console.error('Error starting recording:', err);
      setError('Failed to access microphone.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  };

  // Cleanup
  useEffect(() => {
    return () => {
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  if (!user) return null;

  return (
    <div className="flex flex-col h-full relative font-sans text-sm bg-white dark:bg-[#343541]">
      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar relative px-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full px-4 text-center">
            <div className="bg-white dark:bg-white/10 p-4 rounded-full mb-6 shadow-sm">
              {/* Logo or Icon */}
              <div className="w-10 h-10 bg-[#10a37f] rounded-sm flex items-center justify-center">
                <span className="text-white font-bold text-xl">A</span>
              </div>
            </div>
            <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-8">
              How can I help you today?
            </h2>
          </div>
        ) : (
          <div className="flex flex-col pb-32 pt-6 gap-6 max-w-3xl mx-auto w-full">
            {messages.map((message, index) => {
              const isUser = message.role === 'user';
              return (
                <div
                  key={message.id || index}
                  className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex max-w-[85%] gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                    {/* Avatar */}
                    <div className="flex-shrink-0 flex flex-col justify-end">
                      <div className={`w-8 h-8 rounded-sm flex items-center justify-center shadow-sm ${isUser ? 'bg-[#5436DA]' : 'bg-[#10a37f]'
                        }`}>
                        {isUser ? (
                          <span className="text-white text-xs">You</span>
                        ) : (
                          <span className="text-white text-xs">AI</span>
                        )}
                      </div>
                    </div>

                    {/* Content Bubble */}
                    <div className={`relative px-5 py-3.5 shadow-sm ${isUser
                        ? 'bg-[#10a37f] text-white rounded-2xl rounded-tr-sm'
                        : 'bg-gray-100 dark:bg-[#444654] text-gray-800 dark:text-gray-100 rounded-2xl rounded-tl-sm'
                      }`}>
                      {isUser ? (
                        <div className="whitespace-pre-wrap leading-relaxed">
                          {message.content}
                        </div>
                      ) : (
                        <div className="prose prose-slate dark:prose-invert max-w-none leading-relaxed">
                          {/* Render specific message types */}
                          {message.message_type === 'confirmation' && message.metadata ? (
                            <ConfirmationPrompt
                              prompt={message.metadata}
                              onConfirm={handleConfirmation}
                              onCancel={handleConfirmationCancel}
                            />
                          ) : message.message_type === 'event_card' && message.metadata?.event ? (
                            <div className="mt-2">
                              <EventCard event={message.metadata.event} onAction={handleEventAction} />
                            </div>
                          ) : message.message_type === 'event_list' && message.metadata?.events ? (
                            <div className="space-y-3 mt-2">
                              {message.metadata.events.map((event, idx) => (
                                <EventCard key={idx} event={event} onAction={handleEventAction} />
                              ))}
                            </div>
                          ) : message.message_type === 'task_card' && message.metadata?.task ? (
                            <div className="mt-2">
                              <TaskCard task={message.metadata.task} onAction={handleTaskAction} />
                            </div>
                          ) : message.message_type === 'ledger_card' && message.metadata?.ledger ? (
                            <div className="mt-2">
                              <LedgerCard ledger={message.metadata.ledger} onAction={() => { }} />
                            </div>
                          ) : message.message_type === 'ledger_list' && message.metadata?.ledgers ? (
                            <div className="mt-2">
                              <LedgerList ledgers={message.metadata.ledgers} searchTerm="" onLedgerClick={() => { }} />
                            </div>
                          ) : (
                            <ReactMarkdown>{message.content}</ReactMarkdown>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {isTyping && (
              <div className="flex w-full justify-start">
                <div className="flex max-w-[85%] gap-3">
                  <div className="flex-shrink-0 flex flex-col justify-end">
                    <div className="w-8 h-8 bg-[#10a37f] rounded-sm flex items-center justify-center shadow-sm">
                      <span className="text-white text-xs">AI</span>
                    </div>
                  </div>
                  <div className="bg-gray-100 dark:bg-[#444654] px-5 py-4 rounded-2xl rounded-tl-sm shadow-sm flex items-center">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-pulse mr-1"></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-pulse mr-1 delay-75"></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-150"></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-white via-white to-transparent dark:from-[#343541] dark:via-[#343541] pt-10 pb-6">
        <div className="max-w-3xl mx-auto px-4">
          {error && (
            <div className="mb-2 text-center text-red-500 text-sm bg-red-50 dark:bg-red-900/20 p-2 rounded-md border border-red-200 dark:border-red-800">
              {error}
            </div>
          )}
          <div className="relative flex items-center w-full p-3 bg-white dark:bg-[#40414f] border border-black/10 dark:border-gray-900/50 rounded-xl shadow-md dark:shadow-none overflow-hidden ring-offset-2 focus-within:ring-2 ring-blue-500/50">
            {/* Recording Button */}
            <button
              type="button"
              onClick={isRecording ? stopRecording : startRecording}
              className={`p-2 mr-2 rounded-md transition-colors ${isRecording
                ? 'text-red-500 bg-red-50 dark:bg-red-900/20 animate-pulse'
                : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-200'
                }`}
              disabled={!isConnected || isLoading || isTranscribing}
            >
              {isRecording ? <Square className="w-5 h-5 fill-current" /> : <Mic className="w-5 h-5" />}
            </button>

            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage(e);
                }
              }}
              placeholder={isTranscribing ? "Transcribing..." : "Send a message..."}
              className="flex-1 max-h-[200px] py-2 pr-2 bg-transparent border-none focus:ring-0 resize-none text-base text-gray-800 dark:text-gray-100 placeholder-gray-400 outline-none overflow-y-auto"
              rows={1}
              style={{ minHeight: '24px' }}
              disabled={!isConnected || isLoading || isRecording || isTranscribing}
            />

            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || !isConnected || isLoading}
              className={`p-2 rounded-md transition-colors ${inputMessage.trim()
                ? 'bg-[#19c37d] text-white hover:bg-[#1a7f64]'
                : 'text-gray-400 bg-transparent cursor-not-allowed'
                }`}
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>
          <div className="text-center mt-2">
            <span className="text-[10px] text-gray-400 dark:text-gray-500">
              Free Research Preview. ChatGPT may produce inaccurate information about people, places, or facts.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
