# app/routes/chat_routes.py
"""
Chat routes for WebSocket and REST API endpoints.
Provides real-time chat functionality and chat history management.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, Query
from fastapi.websockets import WebSocketDisconnect
from sqlalchemy.orm import Session

from app.db import get_db, crud
from app.core.security import decode_jwt
from app.core.logging_config import user_context
from app.services.chat_handler import process_message, get_user_context

router = APIRouter()
logger = logging.getLogger("ProjectAria.Chat")


class ConnectionManager:
    """Manages WebSocket connections for chat."""
    
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.connecting_users: set = set()  # Track users currently connecting
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept a WebSocket connection and store it."""
        # Check if user is already connecting or connected
        if user_id in self.connecting_users:
            logger.warning(f"User {user_id} is already connecting, rejecting duplicate connection")
            await websocket.close(code=4004, reason="Connection already in progress")
            return False
            
        if user_id in self.active_connections:
            logger.warning(f"User {user_id} is already connected, closing old connection")
            try:
                await self.active_connections[user_id].close(code=4005, reason="New connection established")
            except:
                pass
            del self.active_connections[user_id]
        
        self.connecting_users.add(user_id)
        try:
            await websocket.accept()
            self.active_connections[user_id] = websocket
            logger.info(f"WebSocket connected for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to accept WebSocket for user {user_id}: {e}")
            return False
        finally:
            self.connecting_users.discard(user_id)
    
    def disconnect(self, user_id: int):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user {user_id}")
        self.connecting_users.discard(user_id)
    
    async def send_personal_message(self, message: str, user_id: int):
        """Send a message to a specific user."""
        if user_id in self.active_connections:
            try:
                # Check if connection is still open
                websocket = self.active_connections[user_id]
                if websocket.client_state.name == "CONNECTED":
                    await websocket.send_text(message)
                else:
                    logger.warning(f"WebSocket for user {user_id} is not connected, removing from active connections")
                    self.disconnect(user_id)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                self.disconnect(user_id)


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.
    Authenticates user via JWT token and maintains persistent connection.
    """
    user_id = None
    db = None
    
    try:
        # Get token from query parameters first
        token = websocket.query_params.get("token")
        if not token:
            await websocket.accept()
            await websocket.send_json({"type": "error", "message": "Token required"})
            await websocket.close(code=4000, reason="Token required")
            return
        
        # Authenticate user via JWT token
        payload = decode_jwt(token)
        if not payload:
            await websocket.accept()
            await websocket.send_json({"type": "error", "message": "Invalid token"})
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # Get user from database
        user_email = payload.get("sub")
        if not user_email:
            await websocket.accept()
            await websocket.send_json({"type": "error", "message": "Invalid token payload"})
            await websocket.close(code=4002, reason="Invalid token payload")
            return
        
        # Get database session
        db = next(get_db())
        user = crud.get_user_by_email(db, user_email)
        if not user:
            await websocket.accept()
            await websocket.send_json({"type": "error", "message": "User not found"})
            await websocket.close(code=4003, reason="User not found")
            return
        
        user_id = user.id
        user_context.set(user.email)
        
        # Connect to WebSocket with improved connection management
        connection_success = await manager.connect(websocket, user_id)
        if not connection_success:
            return
        
        # Load recent chat history
        chat_history = crud.get_chat_history(db, user_id, limit=20)
        
        # Send chat history to client
        if chat_history:
            history_data = {
                "type": "history",
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.created_at.isoformat() + "Z",
                        "intent": msg.intent,
                        "message_type": msg.message_type,
                        "metadata": msg.message_metadata
                    }
                    for msg in chat_history
                ]
            }
            await websocket.send_text(json.dumps(history_data))
        
        # Send welcome message
        welcome_data = {
            "type": "message",
            "role": "assistant",
            "content": "👋 Hello! I'm your AI assistant. How can I help you today?",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "intent": "welcome"
        }
        await websocket.send_text(json.dumps(welcome_data))
        
        # Listen for messages
        while True:
            try:
                # Check if connection is still open
                if websocket.client_state.name != "CONNECTED":
                    logger.info(f"WebSocket connection closed for user {user_id}")
                    break
                    
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                if message_data.get("type") == "message":
                    user_message = message_data.get("content", "").strip()
                    
                    if not user_message:
                        continue
                    
                    # Note: User message saving is handled by process_message to avoid duplicates
                    # especially for confirmation responses which need special handling
                    
                    # Send typing indicator
                    typing_data = {
                        "type": "typing",
                        "is_typing": True
                    }
                    try:
                        await websocket.send_text(json.dumps(typing_data))
                    except Exception as e:
                        logger.warning(f"Failed to send typing indicator: {e}")
                        break
                    
                    # Process message through AI
                    async def send_response(content: str, message_type: str = "text", metadata: dict = None):
                        try:
                            response_data = {
                                "type": "message",
                                "role": "assistant",
                                "content": content,
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "message_type": message_type,
                                "metadata": metadata
                            }
                            await websocket.send_text(json.dumps(response_data))
                        except Exception as e:
                            logger.warning(f"Failed to send response: {e}")
                    
                    result = await process_message(user_id, user_message, db, send_response)
                    
                    # Send stop typing indicator
                    typing_data["is_typing"] = False
                    try:
                        await websocket.send_text(json.dumps(typing_data))
                    except Exception as e:
                        logger.warning(f"Failed to send stop typing indicator: {e}")
                        break
                    
                    logger.info(f"Processed message for user {user_id}: {result.get('status')}")
            
            except json.JSONDecodeError:
                error_data = {
                    "type": "error",
                    "message": "Invalid message format"
                }
                try:
                    await websocket.send_text(json.dumps(error_data))
                except Exception as e:
                    logger.warning(f"Failed to send error message: {e}")
                    break
            
            except Exception as e:
                # Handle manual disconnects gracefully
                if "Manual disconnect" in str(e) or "1000" in str(e):
                    logger.info(f"User {user_id} manually disconnected")
                    break
                elif "websocket.close" in str(e):
                    logger.info(f"WebSocket connection closed for user {user_id}")
                    break
                else:
                    logger.error(f"Error processing message for user {user_id}: {e}")
                    error_data = {
                        "type": "error",
                        "message": "Error processing your message"
                    }
                    try:
                        await websocket.send_text(json.dumps(error_data))
                    except Exception as send_error:
                        logger.warning(f"Failed to send error message: {send_error}")
                        break
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        if user_id:
            manager.disconnect(user_id)


# ------------------------
# REST API Endpoints
# ------------------------

@router.get("/chat/history")
async def get_chat_history(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get chat history for the authenticated user."""
    try:
        # Get user from JWT token (this would need to be implemented in a dependency)
        # For now, we'll use a placeholder
        user_id = 1  # This should be extracted from JWT token
        
        messages = crud.get_chat_history(db, user_id, limit)
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat() + "Z",
                    "intent": msg.intent,
                    "message_type": msg.message_type,
                    "metadata": msg.message_metadata
                }
                for msg in messages
            ],
            "count": len(messages)
        }
    
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat history")


@router.delete("/chat/history")
async def clear_chat_history(db: Session = Depends(get_db)):
    """Clear chat history for the authenticated user."""
    try:
        user_id = 1  # This should be extracted from JWT token
        
        deleted_count = crud.delete_chat_history(db, user_id)
        
        return {
            "message": "Chat history cleared",
            "deleted_count": deleted_count
        }
    
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear chat history")


@router.get("/chat/context")
async def get_chat_context(db: Session = Depends(get_db)):
    """Get user context including connected integrations."""
    try:
        user_id = 1  # This should be extracted from JWT token
        
        context = get_user_context(user_id, db)
        
        if "error" in context:
            raise HTTPException(status_code=500, detail=context["error"])
        
        return context
    
    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user context")
