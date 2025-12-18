// src/services/chatService.js
import API from './api';

const chatService = {
  /**
   * Get chat history for the current user
   * @param {number} limit - Maximum number of messages to retrieve
   * @param {string|null} date - Optional date filter (YYYY-MM-DD)
   * @returns {Promise<Object>} Chat history with messages array
   */
  async getChatHistory(limit = 50, date = null) {
    try {
      const params = { limit };
      if (date) {
        params.date = date;
      }

      const response = await API.get('/chat/history', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching chat history:', error);
      throw new Error('Failed to fetch chat history');
    }
  },

  /**
   * Get available chat dates
   * @returns {Promise<Object>} List of dates with message counts
   */
  async getChatDates() {
    try {
      const response = await API.get('/chat/dates');
      return response.data;
    } catch (error) {
      console.error('Error fetching chat dates:', error);
      throw new Error('Failed to fetch chat dates');
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
  },

  /**
   * Upload audio file for transcription
   * @param {File} audioFile - Audio file to transcribe
   * @returns {Promise<string>} Transcribed text
   */
  async uploadAudio(audioFile) {
    try {
      const formData = new FormData();
      formData.append('file', audioFile);

      const response = await API.post('/media/upload-audio', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data.transcript || '';
    } catch (error) {
      console.error('Error uploading audio:', error);
      throw new Error('Failed to transcribe audio');
    }
  }
};

export default chatService;
