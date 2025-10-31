# app/services/chat_handler.py
"""
Shared message processing logic for both WhatsApp and WebSocket chat.
Extracts common functionality from WhatsApp webhook to be reused.
"""

import logging
import json
import re
import pytz
import dateparser
from dateutil.parser import isoparse
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.services.ai_service import interpret_message
from app.services.conversation_manager import add_user_message, add_assistant_message, get_recent_chat
from app.db import crud

# Import handlers
from app.routes.whatsapp.handlers import calendar_handler, profile_handler, help_handler, tally_handler

logger = logging.getLogger("ProjectAria.ChatHandler")


async def process_message(
    user_id: int,
    message: str,
    db: Session,
    response_callback: callable = None
) -> Dict[str, Any]:
    """
    Process a user message through AI and execute appropriate handlers.
    
    Args:
        user_id: ID of the user sending the message
        message: The user's message content
        db: Database session
        response_callback: Optional callback to send response (for WebSocket)
    
    Returns:
        Dict with status and response content
    """
    try:
        # Get user object
        user = crud.get_user_by_id(db, user_id)
        if not user:
            return {"content": "❌ User not found", "status": "error"}
        
        # Check if this is a confirmation response
        pending_action = crud.get_pending_action(db, user_id)
        if pending_action and pending_action.context:
            # User has a pending action, check if their message is a response to it
            context = json.loads(pending_action.context)
            
            # Check for confirmation response patterns
            msg_lower = message.lower().strip()
            if any(keyword in msg_lower for keyword in ['option', 'choose', 'select', 'confirm', 'yes', 'ok', '1', '2', '3', '4', '5']):
                # This looks like a confirmation response
                logger.info(f"Detected confirmation response: {message}")
                
                # Clear the pending action
                crud.clear_pending_action(db, user_id)
                
                # Handle the confirmation
                if pending_action.action_type == "calendar_conflict":
                    # Handle calendar event creation with conflict resolution
                    action = context.get("action", "create_calendar_event")
                    title = context.get("title")
                    datetime_str = context.get("datetime")
                    description = context.get("description", "")
                    duration_minutes = context.get("duration_minutes", 60)
                    color = context.get("color", "default")
                    
                    # Determine which option they chose
                    if "1" in msg_lower or "confirm" in msg_lower or "yes" in msg_lower:
                        # Create anyway - skip conflict check since user confirmed
                        from app.services.calendar_service import create_event_for_user
                        event = await create_event_for_user(
                            user=user,
                            title=title,
                            description=description,
                            datetime_str=datetime_str,
                            duration_minutes=duration_minutes,
                            color=color,
                            skip_conflict_check=True  # User confirmed, create anyway
                        )
                        if "error" in event:
                            response_content = event["error"]
                        elif event.get("status") == "conflict":
                            # Still got conflict even though we skipped check - shouldn't happen, but handle it
                            response_content = f"❌ Could not create event: {event.get('message', 'Conflict detected')}"
                        elif event.get("status") == "success":
                            response_content = f"✅ Event created: {title}"
                        else:
                            response_content = f"✅ Event created: {title}"
                    elif any(str(i) in msg_lower for i in range(2, 6)) or "choose" in msg_lower or "different" in msg_lower:
                        # Choose a different slot
                        # Extract slot index from message (e.g., "2", "3", "option 2", "choose 2")
                        slot_match = re.search(r'(?:option\s*)?(\d)', msg_lower)
                        if slot_match:
                            slot_number = int(slot_match.group(1))
                            # Options displayed start from 2 (since 1 is "Create anyway")
                            slot_idx = slot_number - 2  # Convert to 0-based index
                            
                            free_slots_raw = context.get("free_slots_raw", [])
                            if slot_idx >= 0 and slot_idx < len(free_slots_raw):
                                # User selected a valid free slot - get the datetime
                                selected_slot = free_slots_raw[slot_idx]
                                slot_start_iso = selected_slot.get("start")
                                
                                # Create event at the selected slot time
                                from app.services.calendar_service import create_event_for_user
                                
                                # Convert ISO datetime to natural language format for create_event_for_user
                                from dateutil import parser as dateutil_parser
                                slot_start_dt = dateutil_parser.parse(slot_start_iso)
                                # Format as natural language like "Wednesday 6:30pm"
                                slot_datetime_str = slot_start_dt.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%A %I:%M %p").lower()
                                
                                event = await create_event_for_user(
                                    user=user,
                                    title=title,
                                    description=description,
                                    datetime_str=slot_datetime_str,
                                    duration_minutes=duration_minutes,
                                    color=color,
                                    skip_conflict_check=True  # Already a free slot, no need to check
                                )
                                
                                if "error" in event:
                                    response_content = f"❌ Could not create event: {event['error']}"
                                elif event.get("status") == "success":
                                    response_content = f"✅ Event created: {title} at {slot_datetime_str}"
                                else:
                                    response_content = f"✅ Event created: {title}"
                            else:
                                response_content = f"❌ Invalid slot selection. Please choose a number between 2 and {len(free_slots_raw) + 1}"
                        else:
                            response_content = "❌ Please specify which slot to use (e.g., '2', 'option 2', 'choose 2')"
                    else:
                        response_content = "❌ Event creation cancelled"
                    
                    # Determine message type and metadata for successful event creation
                    message_type = "text"
                    metadata = None
                    if "✅ Event created" in response_content:
                        message_type = "event_card"
                        # Fetch the created event details for metadata
                        try:
                            from app.services.calendar_service import fetch_upcoming_events_for_user
                            events_list, _ = await fetch_upcoming_events_for_user(user, days=1)
                            if events_list:
                                # Find the most recent event with matching title
                                for event_item in events_list:
                                    if event_item.get("summary") == title:
                                        # Get full event details
                                        from app.services.calendar_service import fetch_event_details_for_user
                                        event_details = await fetch_event_details_for_user(user, event_item.get("id"))
                                        if "error" not in event_details:
                                            _, formatted_event = _format_event_details_response(event_details)
                                            metadata = {"event": formatted_event}
                                        break
                        except Exception as e:
                            logger.warning(f"Failed to fetch event details for metadata: {e}")
                    
                    # Save user message and assistant response to database
                    crud.create_chat_message(db, user_id, "user", message, intent="confirmation")
                    crud.create_chat_message(db, user_id, "assistant", response_content, intent="create_calendar_event")
                    
                    # Send response
                    if response_callback:
                        await response_callback(response_content, message_type, metadata)
                    
                    return {
                        "content": response_content,
                        "status": "success",
                        "saved_to_db": True,
                        "message_type": message_type,
                        "metadata": metadata
                    }
        
        # Add user message to conversation history (if not already saved by confirmation handler)
        add_user_message(user_id, message)
        
        # Process through AI service (no history to avoid confusion)
        ai_result = await interpret_message(message, None)
        intent = ai_result.get("intent", "unknown")
        params = ai_result.get("params", {})
        
        logger.info(f"AI interpreted message for user {user_id}: intent={intent}")
        
        # Route to appropriate handler based on intent
        if intent.startswith("get_tally_") or intent.startswith("create_tally_"):
            # Handle Tally intents
            response = await handle_tally_intent(intent, params, user, db, response_callback)
            
        elif (intent.startswith("get_") or intent.startswith("create_") or intent.startswith("reschedule_") or 
              intent.startswith("cancel_") or intent.startswith("find_") or intent in ["get_next_meeting", "get_weekly_meetings"]):
            # Handle calendar intents
            response = await handle_calendar_intent(intent, params, user, db, response_callback, user_id)
            
        elif intent == "get_user_profile":
            # Handle profile intents
            response = await handle_profile_intent(user, db, response_callback)
            
        elif intent == "get_help":
            # Handle help intents
            response = await handle_help_intent(db, response_callback)
        
        elif intent == "chat":
            # AI wants to chat directly - just send the content
            response_content = ai_result.get("content", "I'm here to help!")
            
            response = {
                "content": response_content,
                "intent": "chat",
                "status": "success"
            }
            
            # Add assistant response to conversation
            add_assistant_message(user_id, response_content)
            
            # Send response via callback if available
            if response_callback:
                await response_callback(response_content)
            
            # Save to database
            crud.create_chat_message(db, user_id, "assistant", response_content, "chat")
            
        else:
            # Unknown intent - check if there's an error from AI
            if ai_result.get("error"):
                error_msg = ai_result.get("error", "Unknown error")
                response_content = f"⚠️ {error_msg}"
            else:
                response_content = "🤖 Sorry, I didn't understand that. Try 'Show my meetings today' or 'outstanding of ABC Company'."
            
            response = {
                "content": response_content,
                "intent": "unknown",
                "status": "success"
            }
            
            # Add assistant response to conversation
            add_assistant_message(user_id, response_content)
            
            # Send response via callback if available
            if response_callback:
                await response_callback(response_content)
            
            # Save to database
            crud.create_chat_message(db, user_id, "assistant", response_content, "unknown")
        
        # Save assistant response to database if not already saved by handler
        if response.get("status") == "success" and response.get("content"):
            # Check if message was already saved by the handler
            if not response.get("saved_to_db", False):
                crud.create_chat_message(
                    db, 
                    user_id, 
                    "assistant", 
                    response["content"], 
                    intent
                )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing message for user {user_id}: {str(e)}")
        error_response = "❌ Sorry, I encountered an error processing your request. Please try again."
        
        # Add error to conversation
        add_assistant_message(user_id, error_response)
        crud.create_chat_message(db, user_id, "assistant", error_response, "error")
        
        return {
            "content": error_response,
            "intent": "error",
            "status": "error"
        }


def get_user_context(user_id: int, db: Session) -> Dict[str, Any]:
    """
    Get user context including connected integrations and recent activity.
    
    Args:
        user_id: ID of the user
        db: Database session
    
    Returns:
        Dict with user context information
    """
    try:
        user = crud.get_user_by_id(db, user_id)
        if not user:
            return {"error": "User not found"}
        
        context = {
            "user_id": user_id,
            "name": user.name,
            "email": user.email,
            "integrations": {
                "google_calendar": bool(user.google_calendar_token),
                "google_gmail": bool(user.google_gmail_token),
                "tally": user.tally_connected,
                "whatsapp": bool(user.whatsapp_no and user.whatsapp_verified)
            },
            "tally_info": {
                "connected": user.tally_connected,
                "company_name": user.tally_company_name,
                "database_name": user.tally_database_name
            } if user.tally_connected else None
        }
        
        return context
        
    except Exception as e:
        logger.error(f"Error getting user context for user {user_id}: {str(e)}")
        return {"error": "Failed to get user context"}


# ------------------------
# Handler Wrapper Functions
# ------------------------

def _format_event_details_response(event_data: Dict[str, Any]) -> tuple:
    """Helper to format event details into a response string and metadata."""
    summary = event_data.get("summary", "Untitled Event")
    start_iso = event_data.get("start", {}).get("dateTime") or event_data.get("start", {}).get("date")
    end_iso = event_data.get("end", {}).get("dateTime") or event_data.get("end", {}).get("date")
    
    # Parse and format datetime
    from dateutil import parser as dateutil_parser
    try:
        start_dt = dateutil_parser.parse(start_iso)
        if end_iso:
            end_dt = dateutil_parser.parse(end_iso)
            if "T" in start_iso:
                time_display = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p on %A, %d %b %Y')}"
            else:
                time_display = f"All-day: {start_dt.strftime('%A, %d %b %Y')}"
        else:
            time_display = start_dt.strftime('%A, %d %b %Y at %I:%M %p')
    except:
        time_display = f"{start_iso} - {end_iso}" if end_iso else start_iso
    
    organizer = event_data.get("organizer", {})
    organizer_display = organizer.get("displayName") if isinstance(organizer, dict) else str(organizer)
    if not organizer_display:
        organizer_display = organizer.get("email", "Unknown") if isinstance(organizer, dict) else "Unknown"
    
    attendees = event_data.get("attendees", [])
    attendee_list = []
    for a in attendees:
        if isinstance(a, dict):
            if not a.get("self"):
                attendee_list.append(a.get("displayName") or a.get("email", ""))
        else:
            attendee_list.append(str(a))
    attendees_str = ", ".join([a for a in attendee_list if a]) if attendee_list else "None"
    
    description = event_data.get("description", "")
    location = event_data.get("location", "")
    hangout_link = event_data.get("hangoutLink", "")
    
    response_content = (
        f"📅 *{summary}*\n\n"
        f"⏰ {time_display}\n"
        f"👤 Organizer: {organizer_display}\n"
        f"👥 Attendees: {attendees_str}"
    )
    
    if location:
        response_content += f"\n📍 Location: {location}"
    if description:
        response_content += f"\n📝 Description: {description}"
    if hangout_link:
        response_content += f"\n🔗 Meeting Link: {hangout_link}"
    
    # Format metadata for frontend - ensure attendees is an array of strings
    formatted_event = {
        "id": event_data.get("id"),
        "summary": summary,
        "start": start_iso,
        "end": end_iso,
        "organizer": organizer_display,
        "attendees": [a for a in attendee_list if a],  # Array of strings
        "description": description,
        "location": location,
        "hangoutLink": hangout_link,
    }
    
    return response_content, formatted_event


async def handle_calendar_intent(intent, params, user, db, response_callback=None, user_id=None):
    """Wrapper for calendar handler that works with both WhatsApp and WebSocket."""
    try:
        # Import calendar service directly to avoid WhatsApp dependency
        from app.services.calendar_service import (
            fetch_today_events_for_user, 
            fetch_upcoming_events_for_user,
            create_event_for_user,
            get_next_single_meeting,
            get_weekly_schedule,
            cancel_event_for_user,
            check_availability_at_time,
            find_best_free_slots,
            check_conflicts_for_user,
            format_event_list,
            fetch_event_details_for_user
        )
        import json
        
        response_content = ""
        message_type = "text"  # Default message type
        metadata = None
        
        if intent == "get_today_events":
            events, message = await fetch_today_events_for_user(user)
            if not events:
                response_content = "📭 You have no events scheduled for today."
            else:
                response_content = f"📅 Today's events:\n\n{message}"
                message_type = "event_list"
                metadata = {"events": events}
                
        elif intent == "get_upcoming_events":
            days = int(params.get("days", 7))
            events, message = await fetch_upcoming_events_for_user(user, days)
            if not events:
                response_content = f"📭 You have no events scheduled for the next {days} days."
            else:
                response_content = f"📅 Upcoming events (next {days} days):\n\n{message}"
                message_type = "event_list"
                metadata = {"events": events}
                
        elif intent == "get_next_meeting":
            event, message = await get_next_single_meeting(user)
            response_content = message
            if event:
                message_type = "event_card"
                metadata = {"event": event}
                
        elif intent == "get_weekly_meetings":
            events, message = await get_weekly_schedule(user)
            response_content = message
            if events:
                message_type = "event_list"
                metadata = {"events": events}
                
        elif intent == "get_event_details":
            event_id = params.get("event_id")
            
            if not event_id:
                response_content = "❌ Please specify which event to show details for (by title or event ID)."
            else:
                # Check if event_id looks like a Google Calendar event ID (long alphanumeric string)
                # If not, treat it as a title and search for the event
                if len(event_id) > 30 and event_id.replace("-", "").replace("_", "").isalnum():
                    # Looks like an actual event ID
                    result = await fetch_event_details_for_user(user, event_id)
                    if "error" in result:
                        response_content = f"❌ {result['error']}"
                        metadata = None
                    else:
                        response_content, event_data = _format_event_details_response(result)
                        message_type = "event_card"
                        metadata = {"event": event_data}
                else:
                    # Looks like a title, search for the event
                    # Search in upcoming events (next 30 days)
                    events_list, _ = await fetch_upcoming_events_for_user(user, days=30)
                    
                    if not events_list:
                        response_content = f"❌ Could not find event '{event_id}' in your upcoming events."
                        metadata = None
                    else:
                        # Find matching event by title (events_list is a list of formatted events)
                        matching_event = None
                        event_title_lower = event_id.lower().strip()
                        
                        for event in events_list:
                            event_summary = event.get("summary", "")
                            if event_summary and (event_summary.lower() == event_title_lower or event_title_lower in event_summary.lower()):
                                matching_event = event
                                break
                        
                        if not matching_event:
                            response_content = f"❌ Could not find event '{event_id}' in your upcoming events."
                            metadata = None
                        else:
                            # Found it, fetch full details using the event ID
                            actual_event_id = matching_event.get("id")
                            if not actual_event_id:
                                response_content = f"❌ Could not get event ID for '{event_id}'."
                                metadata = None
                            else:
                                result = await fetch_event_details_for_user(user, actual_event_id)
                                
                                if "error" in result:
                                    response_content = f"❌ {result['error']}"
                                    metadata = None
                                else:
                                    response_content, event_data = _format_event_details_response(result)
                                    message_type = "event_card"
                                    metadata = {"event": event_data}
                
        elif intent == "find_free_time":
            datetime_str = params.get("datetime", "")
            target_date = params.get("target_date", "")
            duration_minutes = params.get("duration_minutes", 60)
            
            # Determine if this is a date-only query (e.g., "tomorrow", "Friday") vs specific time
            is_date_only_query = False
            date_to_find = None
            
            # Check target_date parameter first
            if target_date:
                is_date_only_query = True
                date_to_find = target_date
            elif datetime_str:
                # Check if datetime_str is just a date (no time component)
                datetime_lower = datetime_str.lower()
                # Common date-only patterns
                date_only_keywords = ["tomorrow", "today", "friday", "monday", "tuesday", "wednesday", "thursday", "saturday", "sunday"]
                has_time_keywords = any(keyword in datetime_lower for keyword in ["am", "pm", ":", "at", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"])
                
                # If it's a date keyword without time indicators, treat as date-only
                if any(keyword in datetime_lower for keyword in date_only_keywords) and not has_time_keywords:
                    is_date_only_query = True
                    date_to_find = datetime_str
                # Check if it's just a date format (YYYY-MM-DD)
                elif len(datetime_str) == 10 and datetime_str.count("-") == 2:
                    is_date_only_query = True
                    date_to_find = datetime_str
            
            if is_date_only_query and date_to_find:
                # Find free slots for specific date
                # Parse the target date to get start/end of that day
                try:
                    parsed_date = None
                    
                    # First, try parsing as ISO date format (YYYY-MM-DD)
                    if len(date_to_find) == 10 and date_to_find.count("-") == 2:
                        try:
                            from datetime import date as date_class
                            date_obj = date_class.fromisoformat(date_to_find)
                            # Convert to datetime at start of day in IST
                            ist = pytz.timezone("Asia/Kolkata")
                            parsed_date = ist.localize(datetime.combine(date_obj, datetime.min.time()))
                        except ValueError:
                            pass
                    
                    # If ISO parsing failed, try natural language parsing
                    if not parsed_date:
                        parsed_date = dateparser.parse(
                            date_to_find,
                            settings={
                                "TIMEZONE": "Asia/Kolkata",
                                "PREFER_DATES_FROM": "future",
                                "DATE_ORDER": "DMY",
                                "RELATIVE_BASE": datetime.now(pytz.timezone("Asia/Kolkata"))
                            }
                        )
                        if parsed_date and parsed_date.tzinfo is None:
                            parsed_date = pytz.timezone("Asia/Kolkata").localize(parsed_date)
                    
                    if parsed_date:
                        # Get slots for that specific date
                        slots_result = await find_best_free_slots(
                            user, 
                            days=1, 
                            min_duration_minutes=duration_minutes,
                            start_date=parsed_date.date()
                        )
                        
                        # Get formatted slots - since we're querying for exactly 1 day with start_date,
                        # all returned slots should be for that date, so no need to filter
                        if isinstance(slots_result, dict):
                            filtered_slots = slots_result.get("formatted", [])
                        else:
                            filtered_slots = slots_result if isinstance(slots_result, list) else []
                        
                        if filtered_slots:
                            date_display = parsed_date.strftime("%A, %B %d, %Y")
                            response_content = f"📅 *Available slots on {date_display}:*\n\n" + "\n".join([f"• {slot}" for slot in filtered_slots])
                        else:
                            date_display = parsed_date.strftime("%A, %B %d, %Y")
                            response_content = f"📭 No free slots available on {date_display}."
                    else:
                        response_content = f"❌ Could not parse date: {date_to_find}"
                except Exception as e:
                    logger.error(f"Error finding free slots for date: {e}")
                    response_content = f"❌ Error finding free slots for {date_to_find}"
            elif datetime_str:
                # Check specific time
                result = await check_availability_at_time(user, datetime_str, duration_minutes)
                if result.get("available"):
                    # Get the formatted time from the result
                    available_time = result.get("time", datetime_str)
                    response_content = f"✅ Yes, you're free at {available_time}"
                else:
                    conflict = result.get("conflict", "another meeting")
                    response_content = f"❌ You're busy at {datetime_str} - you have '{conflict}'"
            else:
                # Find general free slots (next few days)
                slots_result = await find_best_free_slots(user, days=3, min_duration_minutes=duration_minutes)
                # Handle both old (list) and new (dict) return formats
                if isinstance(slots_result, dict):
                    slots = slots_result.get("formatted", [])
                else:
                    slots = slots_result
                if slots:
                    response_content = f"📅 *Available free slots (next 3 days):*\n\n" + "\n".join([f"• {slot}" for i, slot in enumerate(slots)])
                else:
                    response_content = "📭 No free slots found in the next few days."
                    
        elif intent == "cancel_calendar_event":
            event_id = params.get("event_id")
            title = params.get("title", "this event")
            
            if event_id:
                result = await cancel_event_for_user(user, event_id)
                if result.get("status") == "success":
                    response_content = f"✅ Cancelled event: {title}"
                else:
                    response_content = result.get("error", "Failed to cancel event")
            elif title and title != "this event":
                # Try to find event by title - look for next upcoming event with matching title
                from app.services.calendar_service import get_next_single_meeting
                upcoming_event, _ = await get_next_single_meeting(user)
                if upcoming_event and upcoming_event.get("summary") == title:
                    event_id_to_cancel = upcoming_event.get("id")
                    result = await cancel_event_for_user(user, event_id_to_cancel)
                    if result.get("status") == "success":
                        response_content = f"✅ Cancelled event: {title}"
                    else:
                        response_content = result.get("error", "Failed to cancel event")
                else:
                    response_content = f"❌ Could not find event '{title}' in your upcoming meetings."
            else:
                response_content = "❌ Please specify which event to cancel (by title or event ID)."
                
        elif intent == "reschedule_calendar_event":
            event_id = params.get("event_id")
            title = params.get("title", "")
            new_datetime = params.get("new_datetime", "")
            duration_minutes = params.get("duration_minutes", 60)
            
            if not new_datetime:
                response_content = "❌ Please provide the new date and time for rescheduling."
            elif not event_id and not title:
                response_content = "❌ Please specify which event to reschedule (provide event_id or event title)."
            else:
                from app.services.calendar_service import update_event_time
                
                # Check if "same time" is mentioned in the new_datetime string
                new_datetime_lower = new_datetime.lower()
                preserve_time = "same time" in new_datetime_lower or ("same" in new_datetime_lower and "time" in new_datetime_lower)
                
                # If we have a title but no event_id, search for the event
                if not event_id and title:
                    # Search in upcoming events (next 30 days)
                    events_list, _ = await fetch_upcoming_events_for_user(user, days=30)
                    
                    if not events_list:
                        response_content = f"❌ Could not find event '{title}' in your upcoming events."
                    else:
                        # Find matching event by title
                        matching_event = None
                        event_title_lower = title.lower().strip()
                        
                        for event in events_list:
                            event_summary = event.get("summary", "")
                            if event_summary and (event_summary.lower() == event_title_lower or event_title_lower in event_summary.lower()):
                                matching_event = event
                                break
                        
                        if not matching_event:
                            response_content = f"❌ Could not find event '{title}' in your upcoming events."
                        else:
                            actual_event_id = matching_event.get("id")
                            if not actual_event_id:
                                response_content = f"❌ Could not get event ID for '{title}'."
                            else:
                                event_id = actual_event_id
                
                if event_id:
                    # Pass preserve_original_time flag if "same time" was mentioned
                    result = await update_event_time(user, event_id, new_datetime, duration_minutes, preserve_original_time=preserve_time)
                    if result.get("status") == "success":
                        response_content = f"✅ Rescheduled event: {result.get('summary')} to {new_datetime}"
                        message_type = "event_card"
                        # Fetch updated event details for metadata
                        from app.services.calendar_service import fetch_event_details_for_user
                        updated_event = await fetch_event_details_for_user(user, event_id)
                        if "error" not in updated_event:
                            _, formatted_event = _format_event_details_response(updated_event)
                            metadata = {"event": formatted_event}
                    else:
                        response_content = result.get("error", "Failed to reschedule event")
                else:
                    response_content = "❌ Could not find the event to reschedule."
                
        elif intent == "create_calendar_event":
            # Handle event creation with confirmation flow
            title = params.get("title", "")
            datetime_str = params.get("datetime", "")
            description = params.get("description", "")
            duration_minutes = params.get("duration_minutes", 60)
            color = params.get("color", "default")
            
            if not title or not datetime_str:
                response_content = "❌ Please provide both title and datetime for the event."
            else:
                try:
                    logger.info(f"Creating calendar event: title={title}, datetime={datetime_str}, description={description}")
                    
                    # Parse datetime to check for conflicts
                    # First try to parse as ISO format if it looks like one
                    event_start = None
                    if "T" in datetime_str and ("+" in datetime_str or "Z" in datetime_str):
                        try:
                            from dateutil import parser as dateutil_parser
                            event_start = dateutil_parser.parse(datetime_str)
                            # Convert to IST if not already in a timezone
                            if event_start.tzinfo is None:
                                event_start = pytz.timezone("Asia/Kolkata").localize(event_start)
                            elif "Z" in datetime_str:
                                # Convert UTC to IST
                                event_start = event_start.astimezone(pytz.timezone("Asia/Kolkata"))
                        except Exception as e:
                            logger.warning(f"Failed to parse ISO datetime: {e}")
                    
                    # If not ISO format, try dateparser
                    if not event_start:
                        event_start = dateparser.parse(
                            datetime_str,
                            settings={
                                "TIMEZONE": "Asia/Kolkata",
                                "PREFER_DATES_FROM": "future",
                                "DATE_ORDER": "DMY",
                                "RELATIVE_BASE": datetime.now(pytz.timezone("Asia/Kolkata"))
                            }
                        )
                    
                    if not event_start:
                        response_content = f"❌ Could not understand the time: {datetime_str}"
                    else:
                        # Adjust year if needed
                        now_ist = datetime.now(pytz.timezone("Asia/Kolkata"))
                        if event_start.tzinfo is None:
                            event_start = pytz.timezone("Asia/Kolkata").localize(event_start)
                        if (now_ist - event_start).total_seconds() > 24 * 3600:
                            event_start = event_start.replace(year=now_ist.year)
                        
                        event_end = event_start + timedelta(minutes=duration_minutes)
                        start_utc = event_start.astimezone(timezone.utc)
                        end_utc = event_end.astimezone(timezone.utc)
                        
                        # Check for conflicts
                        conflicts = await check_conflicts_for_user(user, start_utc, end_utc)
                        
                        if conflicts:
                            # Show confirmation prompt with conflict warning
                            conflict_event = conflicts[0]
                            conflict_summary = conflict_event.get("summary", "another meeting")
                            
                            # Get alternative slots
                            free_slots_result = await find_best_free_slots(user, days=7, min_duration_minutes=duration_minutes)
                            
                            # Handle both old (list) and new (dict) return formats
                            if isinstance(free_slots_result, dict):
                                free_slots_formatted = free_slots_result.get("formatted", [])
                                free_slots_raw = free_slots_result.get("raw", [])
                            else:
                                # Legacy format
                                free_slots_formatted = free_slots_result
                                free_slots_raw = []
                            
                            response_content = (
                                f"⚠️ You're already busy at {event_start.strftime('%I:%M %p on %A, %d %b')} "
                                f"with '{conflict_summary}'\n\n"
                                f"Would you like to:\n"
                                f"1. Create the meeting anyway\n"
                                f"2. Choose a different time\n"
                            )
                            
                            if free_slots_formatted:
                                response_content += f"\nAvailable free slots:\n"
                                for i, slot in enumerate(free_slots_formatted[:3], 1):
                                    response_content += f"{i + 1}. {slot}\n"  # Options start from 2, so +1
                            
                            message_type = "confirmation"
                            metadata = {
                                "action": "create_calendar_event",
                                "title": title,
                                "datetime": datetime_str,
                                "description": description,
                                "duration_minutes": duration_minutes,
                                "color": color,
                                "conflict": conflict_summary,
                                "free_slots_formatted": free_slots_formatted[:3],
                                "free_slots_raw": free_slots_raw[:3],  # Store raw datetime data
                                "parsed_start": start_utc.isoformat(),
                                "parsed_end": end_utc.isoformat()
                            }
                            
                            # Store pending action for confirmation
                            crud.set_pending_action(
                                db, 
                                user_id, 
                                "calendar_conflict", 
                                None,  # event_id
                                metadata
                            )
                        else:
                            # No conflict, create directly
                            event = await create_event_for_user(
                                user=user,
                                title=title,
                                description=description,
                                datetime_str=datetime_str,
                                duration_minutes=duration_minutes,
                                color=color
                            )
                            
                            if "error" in event:
                                response_content = event["error"]
                            else:
                                response_content = f"✅ Event created: {title} at {event_start.strftime('%I:%M %p on %A, %d %b')}"
                                message_type = "event_card"
                                # Ensure all event data is JSON-serializable
                                event_data = {
                                    "id": event.get("event_id"),
                                    "summary": event.get("summary"),
                                    "start": event.get("start"),
                                    "end": event.get("end"),
                                    "description": event.get("description"),
                                    "location": event.get("location"),
                                    "organizer": event.get("organizer"),
                                    "attendees": event.get("attendees", []),
                                    "hangoutLink": event.get("hangoutLink"),
                                }
                                metadata = {"event": event_data}
                                
                except Exception as e:
                    logger.error(f"Exception in calendar event creation: {str(e)}")
                    response_content = f"❌ Failed to create event: {str(e)}"
        else:
            response_content = "❌ Unknown calendar operation."
        
        # Debug: Log if response is empty
        if not response_content:
            logger.warning(f"Empty response_content for intent: {intent}")
            response_content = "❌ Could not process your request"
        
        # If we have a response callback (WebSocket), send the response
        if response_callback:
            # Call the callback with all parameters
            if metadata:
                # If we have metadata, it's already in the response
                pass  # Just send the content normally since metadata is passed separately
            await response_callback(response_content, message_type, metadata)
            return {
                "content": response_content, 
                "status": "success", 
                "saved_to_db": True,
                "message_type": message_type,
                "metadata": metadata
            }
        
        # For WhatsApp compatibility, return the result
        return {"content": response_content, "status": "success", "message_type": message_type, "metadata": metadata}
        
    except Exception as e:
        logger.error(f"Error in calendar handler: {str(e)}")
        error_content = "❌ Error processing calendar request"
        if response_callback:
            await response_callback(error_content)
        return {"content": error_content, "status": "error"}


async def handle_tally_intent(intent, params, user, db, response_callback=None):
    """Wrapper for Tally handler that works with both WhatsApp and WebSocket."""
    try:
        from app.routes.whatsapp.handlers import tally_handler
        
        from_number = f"webchat:{user.id}"  # Mark as WebSocket to skip WhatsApp calls
        result = await tally_handler.handle_tally_intent(intent, params, user, from_number, db)
        
        # Extract content from result
        response_content = result.get("content", "Tally operation completed")
        message_type = result.get("message_type", "text")
        metadata = result.get("metadata")
        
        # Save to database if not already saved
        if result.get("status") == "success" and response_content:
            crud.create_chat_message(db, user.id, "assistant", response_content, intent, message_type=message_type, metadata=metadata)
        
        if response_callback:
            await response_callback(response_content, message_type, metadata)
            return {
                "content": response_content, 
                "status": result.get("status", "success"), 
                "saved_to_db": True,
                "message_type": message_type,
                "metadata": metadata
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in Tally handler: {str(e)}")
        error_content = "❌ Error processing Tally request"
        if response_callback:
            await response_callback(error_content)
        return {"content": error_content, "status": "error"}


async def handle_profile_intent(user, db, response_callback=None):
    """Wrapper for profile handler that works with both WhatsApp and WebSocket."""
    try:
        # Create profile content directly
        profile_content = (
            f"👤 *Profile*\n"
            f"Name: {user.name}\n"
            f"Email: {user.email}\n"
            f"WhatsApp: {user.whatsapp_no or 'Not linked'}"
        )
        
        if response_callback:
            await response_callback(profile_content)
            return {"content": profile_content, "status": "success", "saved_to_db": True}
        
        return {"content": profile_content, "status": "success"}
        
    except Exception as e:
        logger.error(f"Error in profile handler: {str(e)}")
        error_content = "❌ Error processing profile request"
        if response_callback:
            await response_callback(error_content)
        return {"content": error_content, "status": "error"}


async def handle_help_intent(db, response_callback=None):
    """Wrapper for help handler that works with both WhatsApp and WebSocket."""
    try:
        # Import help service directly to avoid WhatsApp dependency
        from app.services.help_service import get_help_content
        
        # Get the actual help content
        help_content = get_help_content()
        
        if response_callback:
            await response_callback(help_content)
            return {"content": help_content, "status": "success", "saved_to_db": True}
        
        return {"content": help_content, "status": "success"}
        
    except Exception as e:
        logger.error(f"Error in help handler: {str(e)}")
        error_content = "❌ Error processing help request"
        if response_callback:
            await response_callback(error_content)
        return {"content": error_content, "status": "error"}
