// src/services/chatService.js
import API from './api';

const chatService = {
  /**
   * Get chat history for the current user
   * @param {number} limit - Maximum number of messages to retrieve
   * @returns {Promise<Object>} Chat history with messages array
   */
  async getChatHistory(limit = 50) {
    try {
      const response = await API.get('/chat/history', {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching chat history:', error);
      throw new Error('Failed to fetch chat history');
    }
  },

  /**
   * Clear chat history for the current user
   * @returns {Promise<Object>} Result with deleted count
   */
  async clearChatHistory() {
    try {
      const response = await API.delete('/chat/history');
      return response.data;
    } catch (error) {
      console.error('Error clearing chat history:', error);
      throw new Error('Failed to clear chat history');
    }
  },

  /**
   * Get user context including connected integrations
   * @returns {Promise<Object>} User context information
   */
  async getUserContext() {
    try {
      const response = await API.get('/chat/context');
      return response.data;
    } catch (error) {
      console.error('Error fetching user context:', error);
      throw new Error('Failed to fetch user context');
    }
  },

  /**
   * Create WebSocket URL with authentication token
   * @param {string} token - JWT authentication token
   * @returns {string} WebSocket URL with token parameter
   */
  createWebSocketUrl(token) {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const wsUrl = baseUrl.replace('http', 'ws');
    return `${wsUrl}/ws/chat?token=${encodeURIComponent(token)}`;
  }
};

export default chatService;
