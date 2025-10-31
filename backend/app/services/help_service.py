# app/services/help_service.py

import logging
from typing import Dict, List
from app.services.ai_functions import FUNCTIONS
from app.core.logging_config import user_context

logger = logging.getLogger("ProjectAria.HelpService")

def get_help_content() -> str:
    """Generate dynamic help content based on available AI functions."""
    
    # Categorize functions by their prefixes
    categories = {
        "📅 Calendar & Events": [],
        "📊 Tally Integration": [],
        "📧 Gmail Integration": [],
        "🌤️ Weather & Environment": [],
        "📱 WhatsApp Features": [],
        "🤖 General Help": []
    }
    
    # Process each function and categorize
    for func in FUNCTIONS:
        name = func["name"]
        description = func["description"]
        
        # Categorize based on function name
        if name.startswith("get_") and ("event" in name or "calendar" in name or "meeting" in name):
            categories["📅 Calendar & Events"].append((name, description))
        elif name.startswith("get_tally_") or name.startswith("create_tally_"):
            categories["📊 Tally Integration"].append((name, description))
        elif name.startswith("get_gmail_") or name.startswith("send_gmail_"):
            categories["📧 Gmail Integration"].append((name, description))
        elif name.startswith("get_weather"):
            categories["🌤️ Weather & Environment"].append((name, description))
        elif name.startswith("get_help"):
            categories["🤖 General Help"].append((name, description))
        else:
            # Default to WhatsApp features for other functions
            categories["📱 WhatsApp Features"].append((name, description))
    
    # Generate help message
    help_message = "🤖 *ProjectAria Assistant - What I Can Do*\n\n"
    
    for category, functions in categories.items():
        if functions:  # Only show categories that have functions
            help_message += f"{category}:\n"
            
            for func_name, func_desc in functions:
                # Convert function names to user-friendly examples
                example = get_user_friendly_example(func_name, func_desc)
                if example:
                    help_message += f"• {example}\n"
            
            help_message += "\n"
    
    # Add general instructions
    help_message += "💡 *How to use:*\n"
    help_message += "• Just type naturally like 'Show my meetings today'\n"
    help_message += "• Ask questions like 'What's my schedule?'\n"
    help_message += "• Request data like 'Outstanding of ABC Company'\n"
    help_message += "• I understand natural language - no special commands needed!\n\n"
    
    help_message += "🔄 *This help is automatically updated* when new features are added!"
    
    logger.info("📋 Generated dynamic help content")
    return help_message

def get_user_friendly_example(func_name: str, func_desc: str) -> str:
    """Convert function names to user-friendly examples."""
    
    examples = {
        # Calendar functions
        "get_today_events": "Show today's meetings",
        "get_upcoming_events": "Show upcoming meetings",
        "get_event_details": "Get details of a specific meeting",
        "create_calendar_event": "Create a new meeting",
        "update_calendar_event": "Update an existing meeting",
        "delete_calendar_event": "Cancel a meeting",
        
        # Tally functions
        "get_tally_ledger_balance": "Outstanding of [Company Name]",
        "get_tally_ledger_list": "Show ledger list",
        "get_tally_vouchers": "Show vouchers/transactions",
        "get_tally_stock_items": "Show stock items",
        "get_tally_parties": "Show parties list",
        
        # Gmail functions
        "get_gmail_messages": "Show recent emails",
        "send_gmail_message": "Send an email",
        
        # Profile functions
        "get_user_profile": "Show my profile",
        "update_user_profile": "Update my profile",
        
        # Help function
        "get_help": "What can you do?",
        
        # Weather function
        "get_weather": "What's the weather in [City]?"
    }
    
    return examples.get(func_name, func_desc)

def get_feature_categories() -> Dict[str, List[str]]:
    """Get categorized list of available features."""
    
    categories = {
        "Calendar": [
            "View today's meetings",
            "Show upcoming events", 
            "Create new meetings",
            "Update/cancel meetings"
        ],
        "Tally Integration": [
            "Check outstanding balances",
            "View ledger lists",
            "Show vouchers/transactions",
            "Check stock items",
            "View parties list"
        ],
        "Gmail Integration": [
            "Read recent emails",
            "Send emails"
        ],
        "Profile Management": [
            "View profile",
            "Update profile"
        ]
    }
    
    return categories
