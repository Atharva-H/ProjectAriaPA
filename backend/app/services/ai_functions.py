# app/services/ai_functions.py
"""
Centralized Function Registry for AI Integration.

Each function is defined once, with consistent name, description, and parameters.
Both GPT (OpenAI) and Gemini adapters import this list to ensure identical capabilities.
"""

FUNCTIONS = [
    # -------------------------------
    # 📅 Calendar Management
    # -------------------------------
    {
        "name": "get_today_events",
        "description": "Fetch today's Google Calendar events for the user.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_upcoming_events",
        "description": "Fetch upcoming Google Calendar events for the user within the next N days.",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days ahead to check (default: 7)."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_event_details",
        "description": "Fetch details of a specific Google Calendar event by its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Unique ID of the Google Calendar event."
                }
            },
            "required": ["event_id"]
        }
    },
    {
    "name": "create_calendar_event",
    "description": "Create a new calendar event and schedule a WhatsApp reminder 10 minutes before it starts.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Event title"},
            "description": {"type": "string", "description": "Short summary of the event"},
            "datetime": {"type": "string", "description": "Natural language date/time (e.g. 'tomorrow 2pm')"},
            "duration_minutes": {"type": "integer", "description": "Duration in minutes (default 60)"}
        },
        "required": ["title", "datetime"]
    }
},



    # -------------------------------
    # 💬 WhatsApp / Messaging
    # -------------------------------
    {
        "name": "send_whatsapp_message",
        "description": "Send a WhatsApp message using the linked Twilio number.",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient number in E.164 format (e.g. +919876543210)."},
                "body": {"type": "string", "description": "Text message content to send."}
            },
            "required": ["to", "body"]
        }
    },
    {
        "name": "link_whatsapp_number",
        "description": "Send a verification code to link a new WhatsApp number to the user’s account.",
        "parameters": {
            "type": "object",
            "properties": {
                "number": {"type": "string", "description": "Phone number to link (E.164 format)."}
            },
            "required": ["number"]
        }
    },

    # -------------------------------
    # 👤 User Profile
    # -------------------------------
    {
        "name": "get_user_profile",
        "description": "Fetch the current user’s profile information (name, email, WhatsApp verification).",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "update_user_profile",
        "description": "Update the user's profile name or profile picture.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "New display name for the user."},
                "picture": {"type": "string", "description": "URL of the new profile picture."}
            },
            "required": []
        }
    },

    # -------------------------------
    # 🧾 General / Utility
    # -------------------------------
    {
        "name": "get_system_status",
        "description": "Check backend health and system uptime.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_help",
        "description": "List available commands and features that the user can ask.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },

    # -------------------------------
    # 🧠 AI / Intent Layer (meta)
    # -------------------------------
    {
        "name": "interpret_user_message",
        "description": "Analyze a raw user message and extract structured intent or parameters for other backend functions.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The natural language message from the user."
                }
            },
            "required": ["message"]
        }
    }
]
