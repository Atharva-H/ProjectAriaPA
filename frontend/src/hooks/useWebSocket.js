// src/hooks/useWebSocket.js
import { useState, useEffect, useRef, useCallback } from 'react';

const useWebSocket = (url, options = {}) => {
  const [socket, setSocket] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = options.maxReconnectAttempts || 5;
  const reconnectInterval = options.reconnectInterval || 5000; // Increased to 5 seconds
  const lastConnectionAttempt = useRef(0);

  const connect = useCallback(() => {
    if (!url) {
      console.log('WebSocket URL not provided');
      setConnectionStatus('disconnected');
      return;
    }

    if (socket && socket.readyState === WebSocket.OPEN) {
      return;
    }

    // Rate limiting: prevent rapid connection attempts
    const now = Date.now();
    if (now - lastConnectionAttempt.current < 2000) { // 2 second minimum between attempts
      console.log('Rate limiting: too soon to reconnect');
      return;
    }
    lastConnectionAttempt.current = now;

    try {
      console.log('Connecting to WebSocket:', url);
      const ws = new WebSocket(url);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
        setError(null);
        reconnectAttempts.current = 0;
        setSocket(ws);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          options.onMessage?.(data);
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
          setError('Failed to parse message');
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setConnectionStatus('disconnected');
        setSocket(null);
        
        // Don't attempt to reconnect for certain close codes
        if (event.code === 1000 || event.code === 4000 || event.code === 4001 || event.code === 4002 || event.code === 4003) {
          console.log('WebSocket closed normally or due to authentication error, not reconnecting');
          return;
        }
        
        // Attempt to reconnect if not a manual close
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          console.log(`Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts})...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          setError('Failed to reconnect after multiple attempts');
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
        setConnectionStatus('error');
      };

    } catch (err) {
      console.error('Error creating WebSocket:', err);
      setError('Failed to create WebSocket connection');
    }
  }, [url, options, maxReconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.close(1000, 'Manual disconnect');
    }
    setSocket(null);
    setConnectionStatus('disconnected');
  }, [socket]);

  const sendMessage = useCallback((message) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      try {
        const messageData = {
          type: 'message',
          content: message,
          timestamp: new Date().toISOString()
        };
        socket.send(JSON.stringify(messageData));
        return true;
      } catch (err) {
        console.error('Error sending message:', err);
        setError('Failed to send message');
        return false;
      }
    } else {
      console.warn('WebSocket is not connected');
      setError('WebSocket is not connected');
      return false;
    }
  }, [socket]);

  // Auto-connect on mount
  useEffect(() => {
    if (url) {
      // Add a small delay to prevent rapid connections
      const timeoutId = setTimeout(() => {
        connect();
      }, 100);
      
      return () => {
        clearTimeout(timeoutId);
      };
    }
  }, [url]); // Remove connect and disconnect from dependencies

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socket) {
        socket.close();
      }
    };
  }, []); // Empty dependency array - only run on unmount

  return {
    socket,
    connectionStatus,
    lastMessage,
    error,
    connect,
    disconnect,
    sendMessage,
    isConnected: connectionStatus === 'connected'
  };
};

export default useWebSocket;
