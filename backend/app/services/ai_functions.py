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
        "description": "Fetch ONLY today's Google Calendar events for the user. Use this ONLY when user specifically asks for 'today' or 'today's events'.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_upcoming_events",
        "description": "Fetch upcoming Google Calendar events for the user within the next N days. Use this for 'upcoming', 'next X days', 'this week', 'next week', or any future date range requests.",
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
            "duration_minutes": {"type": "integer", "description": "Duration in minutes (default 60)"},
            "color": {"type": "string", "description": "Event color: 'work' for blue, 'personal' for green, 'default' for no color"}
        },
        "required": ["title", "datetime"]
    }
},
{
    "name": "reschedule_calendar_event",
    "description": "PRIORITY: Reschedule, move, or change the time of an existing calendar event. Use this when user says: 'reschedule X to Y', 'move meeting to Y', 'change time of X to Y', 'move my next meeting to Y'. REQUIRES both the event (by title or ID) AND a new datetime. This is for MODIFYING an existing event's time.",
    "parameters": {
        "type": "object",
        "properties": {
            "event_id": {
                "type": "string",
                "description": "The ID of the calendar event to reschedule. If not provided, use title instead."
            },
            "title": {
                "type": "string",
                "description": "Title or name of the event to reschedule (use this if event_id is not available). Examples: 'Meeting with Sales', 'Team Standup', etc."
            },
            "new_datetime": {
                "type": "string",
                "description": "Natural language date/time for rescheduling (e.g. 'tomorrow 2:30pm', '5pm today', 'next Friday 3pm', '3pm tomorrow')."
            },
            "duration_minutes": {
                "type": "integer",
                "description": "New duration in minutes (default 60)."
            }
        },
        "required": ["new_datetime"]
    }
},
{
    "name": "check_event_conflict",
    "description": "Check if a proposed time conflicts with existing calendar events.",
    "parameters": {
        "type": "object",
        "properties": {
            "datetime": {
                "type": "string",
                "description": "Proposed date and time in natural language (e.g. 'tomorrow 4pm')."
            },
            "duration_minutes": {
                "type": "integer",
                "description": "Duration of the meeting in minutes (default 60)."
            }
        },
        "required": ["datetime"]
    }
},
{
    "name": "suggest_free_slots",
    "description": "Suggest the user's next available free slots within the next 3 days.",
    "parameters": {
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": "How many days ahead to check (default 3)."
            }
        },
        "required": []
    }
},
{
    "name": "get_next_meeting",
    "description": "ONLY for READING/QUERYING the next meeting - NOT for rescheduling. Use this ONLY when user asks to VIEW/SHOW the next meeting without any time change request. Examples: 'what's my next meeting', 'show next appointment', 'am I free right now'. DO NOT use this if user mentions rescheduling, moving, or changing time.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
},
{
    "name": "get_weekly_meetings",
    "description": "Fetch all meetings/events for the current week (next 7 days). Use for 'this week', 'my schedule this week', 'upcoming week' queries.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
},
    {
        "name": "find_free_time",
        "description": "Find available free time slots for a specific date or check if user is free at a specific time. Use for 'when am I available', 'when am I free', 'find time for', 'available tomorrow', 'free slots on Friday' queries. If user asks about availability on a specific DATE (e.g., 'tomorrow', 'Friday') without a specific time, leave datetime empty and it will show all free slots for that day.",
        "parameters": {
            "type": "object",
            "properties": {
                "datetime": {
                    "type": "string",
                    "description": "Specific DATE and TIME to check availability (e.g. 'friday 3pm', 'tomorrow 2pm'). If user asks about a DATE without time (e.g., 'tomorrow', 'Friday'), leave this EMPTY to find all free slots for that day."
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Duration to check (default 60 minutes)."
                },
                "target_date": {
                    "type": "string",
                    "description": "Specific date to find free slots for (e.g., 'tomorrow', 'Friday', '2025-10-30'). Use this when user asks 'when am I available tomorrow' or 'free slots on Friday' without specifying a time."
                }
            },
            "required": []
        }
    },
{
    "name": "cancel_calendar_event",
    "description": "Cancel or delete a calendar event. Use when user wants to remove a meeting or appointment.",
    "parameters": {
        "type": "object",
        "properties": {
            "event_id": {
                "type": "string",
                "description": "The ID of the event to cancel."
            },
            "title": {
                "type": "string",
                "description": "Title or name of the event to cancel (for confirmation)."
            }
        },
        "required": []
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

    # -------------------------------
    # 📊 Tally Integration
    # -------------------------------
    {
        "name": "get_tally_ledger_balance",
        "description": "Get the outstanding balance of a specific ledger from Tally Prime.",
        "parameters": {
            "type": "object",
            "properties": {
                "ledger_name": {
                    "type": "string",
                    "description": "Name of the ledger to check (e.g., 'ABC Company', 'Cash', 'Bank')."
                }
            },
            "required": ["ledger_name"]
        }
    },
    {
        "name": "get_tally_ledger_list",
        "description": "Get a list of all ledgers from Tally Prime.",
        "parameters": {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Optional search term to filter ledgers by name."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_tally_vouchers",
        "description": "Get vouchers from Tally Prime with optional date filters.",
        "parameters": {
            "type": "object",
            "properties": {
                "from_date": {
                    "type": "string",
                    "description": "Start date for voucher search (YYYY-MM-DD format)."
                },
                "to_date": {
                    "type": "string",
                    "description": "End date for voucher search (YYYY-MM-DD format)."
                },
                "party_name": {
                    "type": "string",
                    "description": "Filter vouchers by specific party name."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_tally_stock_items",
        "description": "Get stock items from Tally Prime.",
        "parameters": {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Optional search term to filter stock items by name."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_tally_parties",
        "description": "Get party ledgers (debtors/creditors) from Tally Prime.",
        "parameters": {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Optional search term to filter parties by name."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_tally_sales",
        "description": "Calculate total sales amount for a specific party/customer within a date range. Use this when user asks about sales figures, revenue from a customer, or sales for a specific period (e.g., 'sales of ABC for current month', 'revenue from XYZ this month').",
        "parameters": {
            "type": "object",
            "properties": {
                "party_name": {
                    "type": "string",
                    "description": "Name of the party/customer to calculate sales for (e.g., 'Vinay Trading Agencies, Mumbai', 'ABC Company')."
                },
                "from_date": {
                    "type": "string",
                    "description": "Start date for sales calculation (YYYY-MM-DD format). Defaults to start of current month if not specified."
                },
                "to_date": {
                    "type": "string",
                    "description": "End date for sales calculation (YYYY-MM-DD format). Defaults to end of current month if not specified."
                }
            },
            "required": ["party_name"]
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
    },
    # -------------------------------
    # 🤖 Help & Assistance
    # -------------------------------
    {
        "name": "get_help",
        "description": "Get a comprehensive list of all available features and capabilities.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    # -------------------------------
    # 🆕 New Feature Example
    # -------------------------------
    {
        "name": "get_weather",
        "description": "Get current weather information for a specific location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City or location name (e.g., 'Mumbai', 'New York')."
                }
            },
            "required": ["location"]
        }
    }
]
