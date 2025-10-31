# app/routes/whatsapp/handlers/tally_handler.py

import logging
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db import crud
from app.services.twilio_service import send_whatsapp_message
from app.services.accounting.tally_sql_service import TallySQLService
from app.services.conversation_manager import add_assistant_message

logger = logging.getLogger("ProjectAria.TallyHandler")
tally_service = TallySQLService()


def format_indian_date(date_str: str) -> str:
    """Format date string (YYYY-MM-DD) to Indian format (e.g., '1 Oct 2024')."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%-d %b %Y")  # e.g., "1 Oct 2024"
    except (ValueError, AttributeError):
        # If strftime doesn't support %-d (Windows), use alternative
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            day = dt.day
            return dt.strftime(f"{day} %b %Y")  # e.g., "1 Oct 2024"
        except:
            return date_str


def format_period_string(from_date: str, to_date: str) -> str:
    """Format date range to readable format like '1 Oct 2024 to 31 Oct 2024' or 'October 2024'."""
    try:
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        
        # If same month, show as "October 2024"
        if from_dt.month == to_dt.month and from_dt.year == to_dt.year:
            # Check if it's the full month (1st to last day)
            if from_dt.day == 1:
                # Check if to_date is last day of month
                if to_dt.month == 12:
                    last_day = datetime(to_dt.year + 1, 1, 1) - timedelta(days=1)
                else:
                    last_day = datetime(to_dt.year, to_dt.month + 1, 1) - timedelta(days=1)
                
                if to_dt.day == last_day.day:
                    return from_dt.strftime("%B %Y")  # e.g., "October 2024"
        
        # Otherwise show full range
        return f"{format_indian_date(from_date)} to {format_indian_date(to_date)}"
    except:
        return f"{from_date} to {to_date}"


def format_indian_currency(amount: float) -> str:
    """Format currency in Indian numbering system (lakhs/crores).
    
    Indian numbering: 
    - Last 3 digits: thousands, hundreds, units (112)
    - Every 2 digits before that: lakhs, crores, etc. (35, 39)
    Example: 39,35,112.00 (39 lakhs, 35 thousand, 112)
    """
    try:
        # Convert to string with 2 decimal places
        amount_str = f"{amount:.2f}"
        parts = amount_str.split('.')
        integer_part = parts[0]
        decimal_part = parts[1] if len(parts) > 1 else '00'
        
        if len(integer_part) <= 3:
            # Less than thousand, no comma needed
            formatted_int = integer_part
        else:
            # Take last 3 digits
            last_three = integer_part[-3:]
            remaining = integer_part[:-3]
            
            # Group remaining digits in pairs from right to left
            formatted_parts = []
            remaining_reversed = remaining[::-1]  # Reverse to work from right
            for i in range(0, len(remaining_reversed), 2):
                pair = remaining_reversed[i:i+2]
                formatted_parts.append(pair[::-1])  # Reverse pair back to correct order
            
            formatted_parts.reverse()  # Reverse list to get correct order
            formatted_remaining = ','.join(formatted_parts)
            formatted_int = f"{formatted_remaining},{last_three}" if formatted_remaining else last_three
        
        return f"₹{formatted_int}.{decimal_part}"
    except Exception as e:
        # Fallback to standard formatting
        return f"₹{amount:,.2f}"


def convert_decimal_to_float(obj):
    """Recursively convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimal_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    else:
        return obj


async def handle_tally_intent(intent: str, params: dict, user, from_number: str, db: Session):
    """Handle Tally-related intents (works for both WhatsApp and WebSocket)."""
    
    # Check if this is a WebSocket request (from_number starts with "webchat:")
    is_websocket = from_number and from_number.startswith("webchat:")
    
    # Check if user has Tally connected
    if not user.tally_connected or not user.tally_database_name:
        error_msg = "❌ Tally not connected. Please connect your Tally server via the ProjectAria.PA dashboard first."
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
        return {"status": "tally_not_connected", "content": error_msg}
    
    try:
        if intent == "get_tally_ledger_balance":
            return await handle_ledger_balance(params, user, from_number, db)
        elif intent == "get_tally_ledger_list":
            return await handle_ledger_list(params, user, from_number, db)
        elif intent == "get_tally_vouchers":
            return await handle_vouchers(params, user, from_number, db)
        elif intent == "get_tally_stock_items":
            return await handle_stock_items(params, user, from_number, db)
        elif intent == "get_tally_parties":
            return await handle_parties(params, user, from_number, db)
        elif intent == "get_tally_sales":
            return await handle_sales(params, user, from_number, db)
        else:
            error_msg = "❌ Unknown Tally command. Available commands: ledger balance, ledger list, vouchers, stock items, parties."
            if not is_websocket:
                send_whatsapp_message(from_number, error_msg)
            return {"status": "unknown_command", "content": error_msg}
            
    except Exception as e:
        logger.error(f"❌ Error handling Tally intent {intent}: {str(e)}")
        error_msg = f"❌ Error fetching Tally data: {str(e)}"
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
        return {"status": "error", "content": error_msg}


async def handle_ledger_balance(params: dict, user, from_number: str, db: Session):
    """Handle ledger balance queries."""
    # Check if this is a WebSocket request
    is_websocket = from_number and from_number.startswith("webchat:")
    
    ledger_name = params.get("ledger_name", "").strip()
    
    if not ledger_name:
        error_msg = "❌ Please specify a ledger name. Example: 'outstanding of ABC Company'"
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
        return {"status": "missing_ledger_name", "content": error_msg}
    
    # Get all ledgers - pass None or empty dict as filters, not company_name
    result = await tally_service.get_ledgers(user.tally_database_name, None)
    
    if not result.get("success"):
        error_msg = f"❌ Failed to fetch ledgers: {result.get('message', 'Unknown error')}"
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
        return {"status": "fetch_error", "content": error_msg}
    
    ledgers = result.get("ledgers", [])
    
    # Search for the ledger (case-insensitive)
    matching_ledgers = [
        ledger for ledger in ledgers 
        if ledger_name.lower() in ledger.get("name", "").lower()
    ]
    
    if not matching_ledgers:
        # Try partial matches
        partial_matches = [
            ledger for ledger in ledgers 
            if any(word in ledger.get("name", "").lower() for word in ledger_name.lower().split())
        ]
        
        if partial_matches:
            error_msg = f"❓ Did you mean one of these?\n" + "\n".join([f"• {ledger['name']}" for ledger in partial_matches[:5]])
        else:
            error_msg = f"❌ No ledger found matching '{ledger_name}'. Use 'ledger list' to see available ledgers."
        
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
            add_assistant_message(user.id, error_msg)
        return {"status": "ledger_not_found", "content": error_msg}
    
    # If multiple matches, show all
    if len(matching_ledgers) > 1:
        response = f"📊 Found {len(matching_ledgers)} ledgers matching '{ledger_name}':\n\n"
        for ledger in matching_ledgers[:10]:  # Limit to 10 results
            balance = ledger.get("closing_balance", "0")
            response += f"• {ledger['name']}: ₹{balance}\n"
        
        if len(matching_ledgers) > 10:
            response += f"\n... and {len(matching_ledgers) - 10} more"
        
        # For WebSocket, return structured data for frontend component
        # Convert Decimal values to float for JSON serialization
        serializable_ledgers = [convert_decimal_to_float(ledger) for ledger in matching_ledgers[:20]]
        metadata = {
            "ledgers": serializable_ledgers,
            "search_term": ledger_name,
            "total_found": len(matching_ledgers)
        }
    else:
        # Single ledger match - also return structured data
        ledger = matching_ledgers[0]
        balance = ledger.get("closing_balance", "0")
        opening_balance = ledger.get("opening_balance", "0")
        
        response = f"📊 *{ledger['name']}*\n"
        response += f"💰 Outstanding Balance: ₹{balance}\n"
        response += f"📈 Opening Balance: ₹{opening_balance}\n"
        response += f"🏷️ Type: {ledger.get('parent', 'N/A')}"
        
        # Convert Decimal values to float for JSON serialization
        serializable_ledger = convert_decimal_to_float(ledger)
        metadata = {
            "ledger": serializable_ledger
        }
    
    # Only send WhatsApp message if not WebSocket
    if not is_websocket:
        send_whatsapp_message(from_number, response)
        add_assistant_message(user.id, response)
    
    # Return result with metadata for WebSocket
    if len(matching_ledgers) > 1 and metadata:
        return {
            "status": "success", 
            "content": response,
            "message_type": "ledger_list",
            "metadata": metadata
        }
    elif len(matching_ledgers) == 1 and metadata:
        return {
            "status": "success",
            "content": response,
            "message_type": "ledger_card",
            "metadata": metadata
        }
    
    return {"status": "success", "content": response}


async def handle_sales(params: dict, user, from_number: str, db: Session):
    """Handle sales calculation queries."""
    from datetime import datetime, timedelta
    
    # Check if this is a WebSocket request
    is_websocket = from_number and from_number.startswith("webchat:")
    
    party_name = params.get("party_name", "").strip()
    
    if not party_name:
        error_msg = "❌ Please specify a party name. Example: 'sales of Vinay Trading Agencies for current month'"
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
        return {"status": "missing_party_name", "content": error_msg}
    
    # Get date range - default to current month if not specified
    from_date = params.get("from_date")
    to_date = params.get("to_date")
    
    # If dates not specified, default to current month
    if not from_date or not to_date:
        now = datetime.now()
        from_date = now.replace(day=1).strftime("%Y-%m-%d")
        # Get last day of current month
        if now.month == 12:
            last_day = datetime(now.year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(now.year, now.month + 1, 1) - timedelta(days=1)
        to_date = last_day.strftime("%Y-%m-%d")
    
    # First, try to find matching ledgers for the party name
    ledgers_result = await tally_service.get_ledgers(user.tally_database_name, None)
    
    if not ledgers_result.get("success"):
        error_msg = f"❌ Failed to fetch ledgers: {ledgers_result.get('message', 'Unknown error')}"
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
        return {"status": "fetch_error", "content": error_msg}
    
    ledgers = ledgers_result.get("ledgers", [])
    
    # Search for matching party ledgers (case-insensitive, partial match)
    matching_ledgers = [
        ledger for ledger in ledgers 
        if party_name.lower() in ledger.get("name", "").lower()
    ]
    
    if not matching_ledgers:
        # Try to find exact match or suggest alternatives
        partial_matches = [
            ledger for ledger in ledgers 
            if any(word in ledger.get("name", "").lower() for word in party_name.lower().split())
        ]
        
        if partial_matches:
            suggestions = "\n".join([f"• {ledger['name']}" for ledger in partial_matches[:5]])
            error_msg = f"❓ Party '{party_name}' not found. Did you mean one of these?\n{suggestions}"
        else:
            error_msg = f"❌ No party found matching '{party_name}'. Use 'parties list' to see available parties."
        
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
        return {"status": "party_not_found", "content": error_msg}
    
    # If multiple matches, ask user to be more specific
    if len(matching_ledgers) > 1:
        response = f"📊 Found {len(matching_ledgers)} parties matching '{party_name}':\n\n"
        for ledger in matching_ledgers[:10]:
            response += f"• {ledger['name']}\n"
        
        if len(matching_ledgers) > 10:
            response += f"\n... and {len(matching_ledgers) - 10} more"
        response += f"\n\nPlease specify the exact party name."
        
        if not is_websocket:
            send_whatsapp_message(from_number, response)
        return {"status": "multiple_parties", "content": response}
    
    # Single match - calculate sales
    exact_party_name = matching_ledgers[0]["name"]
    
    result = await tally_service.get_sales(
        user.tally_database_name,
        party_name=exact_party_name,
        from_date=from_date,
        to_date=to_date
    )
    
    if not result.get("success"):
        error_msg = f"❌ Failed to calculate sales: {result.get('message', 'Unknown error')}"
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
        return {"status": "calculation_error", "content": error_msg}
    
    total_sales = result.get("total_sales", 0) or 0
    voucher_count = result.get("voucher_count", 0) or 0
    
    # Format the response with Indian number and date formats
    period_str = format_period_string(from_date, to_date) if from_date and to_date else "the specified period"
    
    # Format currency in Indian format (lakhs/crores)
    sales_formatted = format_indian_currency(total_sales)
    
    response = f"💰 *Sales Report*\n\n"
    response += f"📊 Party: {exact_party_name}\n"
    response += f"📅 Period: {period_str}\n"
    response += f"💵 Total Sales: {sales_formatted}\n"
    response += f"📄 Vouchers: {voucher_count:,}"
    
    # For WebSocket, also return structured data
    metadata = {
        "party_name": exact_party_name,
        "total_sales": float(total_sales),
        "voucher_count": int(voucher_count),
        "from_date": from_date,
        "to_date": to_date,
        "period": period_str
    }
    
    if not is_websocket:
        send_whatsapp_message(from_number, response)
        add_assistant_message(user.id, response)
    
    return {
        "status": "success",
        "content": response,
        "message_type": "sales_report",
        "metadata": metadata
    }


async def handle_ledger_list(params: dict, user, from_number: str, db: Session):
    """Handle ledger list queries."""
    # Check if this is a WebSocket request
    is_websocket = from_number and from_number.startswith("webchat:")
    
    search_term = params.get("search", "").strip()
    
    # Build filters dict if search_term provided
    filters = None
    if search_term:
        filters = {"search": search_term}
    
    result = await tally_service.get_ledgers(user.tally_database_name, filters)
    
    if not result.get("success"):
        error_msg = f"❌ Failed to fetch ledgers: {result.get('message', 'Unknown error')}"
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
        return {"status": "fetch_error", "content": error_msg}
    
    ledgers = result.get("ledgers", [])
    
    if search_term:
        filtered_ledgers = [
            ledger for ledger in ledgers 
            if search_term.lower() in ledger.get("name", "").lower()
        ]
    else:
        filtered_ledgers = ledgers
    
    if not filtered_ledgers:
        error_msg = f"❌ No ledgers found matching '{search_term}'" if search_term else "❌ No ledgers found"
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
            add_assistant_message(user.id, error_msg)
        return {"status": "no_ledgers", "content": error_msg}
    
    # Limit results to avoid message length issues
    display_ledgers = filtered_ledgers[:20]
    
    response = f"📋 *Ledger List* ({len(display_ledgers)} of {len(filtered_ledgers)})\n\n"
    
    for ledger in display_ledgers:
        balance = ledger.get("closing_balance", "0")
        response += f"• {ledger['name']}: ₹{balance}\n"
    
    if len(filtered_ledgers) > 20:
        response += f"\n... and {len(filtered_ledgers) - 20} more ledgers"
    
    # Only send WhatsApp message if not WebSocket
    if not is_websocket:
        send_whatsapp_message(from_number, response)
        add_assistant_message(user.id, response)
    
    return {"status": "success", "content": response}


async def handle_vouchers(params: dict, user, from_number: str, db: Session):
    """Handle voucher queries."""
    from_date = params.get("from_date")
    to_date = params.get("to_date")
    party_name = params.get("party_name", "").strip()
    
    # Build filters dict for get_vouchers
    filters = {}
    if from_date:
        filters["from_date"] = from_date
    if to_date:
        filters["to_date"] = to_date
    if party_name:
        filters["party_name"] = party_name
    
    result = await tally_service.get_vouchers(
        user.tally_database_name, 
        filters  # Pass filters as dict instead of separate parameters
    )
    
    # Check if this is a WebSocket request (from_number starts with "webchat:")
    is_websocket = from_number and from_number.startswith("webchat:")
    
    if not result.get("success"):
        if not is_websocket:
            send_whatsapp_message(
                from_number,
                f"❌ Failed to fetch vouchers: {result.get('message', 'Unknown error')}"
            )
        # Return error response for WebSocket
        error_msg = f"❌ Failed to fetch vouchers: {result.get('message', 'Unknown error')}"
        if not is_websocket:
            add_assistant_message(user.id, error_msg)
        return {"status": "fetch_error", "content": error_msg}
    
    vouchers = result.get("vouchers", [])
    
    if party_name and not filters.get("party_name"):
        # Filter by party name if provided but not already in filters
        vouchers = [
            voucher for voucher in vouchers 
            if party_name.lower() in voucher.get("party_name", "").lower()
        ]
    
    if not vouchers:
        error_msg = f"❌ No vouchers found" + (f" for {party_name}" if party_name else "")
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
            add_assistant_message(user.id, error_msg)
        return {"status": "no_vouchers", "content": error_msg}
    
    # Limit results
    display_vouchers = vouchers[:10]
    
    response = f"📄 *Recent Vouchers* ({len(display_vouchers)} of {len(vouchers)})\n\n"
    
    for voucher in display_vouchers:
        date = voucher.get("date", "N/A")
        vouch_num = voucher.get("voucher_number", "N/A")
        party = voucher.get("party_name", voucher.get("ledger", "N/A"))  # Use party_name from voucher or ledger from accounting
        amount = voucher.get("amount", "0")
        response += f"• {date} - {vouch_num}\n  {party}: ₹{amount}\n\n"
    
    if len(vouchers) > 10:
        response += f"... and {len(vouchers) - 10} more vouchers"
    
    # Only send WhatsApp message if not WebSocket
    if not is_websocket:
        send_whatsapp_message(from_number, response)
        add_assistant_message(user.id, response)
    
    # Return response for both WhatsApp and WebSocket
    return {"status": "success", "content": response, "vouchers": vouchers}


async def handle_stock_items(params: dict, user, from_number: str, db: Session):
    """Handle stock items queries."""
    # Check if this is a WebSocket request
    is_websocket = from_number and from_number.startswith("webchat:")
    
    search_term = params.get("search", "").strip()
    
    # Build filters dict
    filters = {}
    if search_term:
        filters["search"] = search_term
    
    result = await tally_service.get_stock_items(user.tally_database_name, filters if filters else None)
    
    if not result.get("success"):
        error_msg = f"❌ Failed to fetch stock items: {result.get('message', 'Unknown error')}"
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
        return {"status": "fetch_error", "content": error_msg}
    
    items = result.get("items", [])
    
    if search_term and not filters.get("search"):
        # Additional filtering if needed
        items = [
            item for item in items 
            if search_term.lower() in item.get("name", "").lower()
        ]
    
    if not items:
        error_msg = f"❌ No stock items found" + (f" matching '{search_term}'" if search_term else "")
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
            add_assistant_message(user.id, error_msg)
        return {"status": "no_items", "content": error_msg}
    
    # Limit results
    display_items = items[:15]
    
    response = f"📦 *Stock Items* ({len(display_items)} of {len(items)})\n\n"
    
    for item in display_items:
        name = item.get("name", "N/A")
        qty = item.get("closing_quantity", "0")
        rate = item.get("closing_rate", "0")
        response += f"• {name}\n  Qty: {qty}, Rate: ₹{rate}\n\n"
    
    if len(items) > 15:
        response += f"... and {len(items) - 15} more items"
    
    # Only send WhatsApp message if not WebSocket
    if not is_websocket:
        send_whatsapp_message(from_number, response)
        add_assistant_message(user.id, response)
    
    return {"status": "success", "content": response}


async def handle_parties(params: dict, user, from_number: str, db: Session):
    """Handle party queries."""
    # Check if this is a WebSocket request
    is_websocket = from_number and from_number.startswith("webchat:")
    
    search_term = params.get("search", "").strip()
    
    # Build filters dict
    filters = {}
    if search_term:
        filters["search"] = search_term
    
    result = await tally_service.get_parties(user.tally_database_name, filters if filters else None)
    
    if not result.get("success"):
        error_msg = f"❌ Failed to fetch parties: {result.get('message', 'Unknown error')}"
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
        return {"status": "fetch_error", "content": error_msg}
    
    parties = result.get("parties", [])
    
    if search_term and not filters.get("search"):
        # Additional filtering if needed
        parties = [
            party for party in parties 
            if search_term.lower() in party.get("name", "").lower()
        ]
    
    if not parties:
        error_msg = f"❌ No parties found" + (f" matching '{search_term}'" if search_term else "")
        if not is_websocket:
            send_whatsapp_message(from_number, error_msg)
            add_assistant_message(user.id, error_msg)
        return {"status": "no_parties", "content": error_msg}
    
    # Limit results
    display_parties = parties[:15]
    
    response = f"👥 *Parties* ({len(display_parties)} of {len(parties)})\n\n"
    
    for party in display_parties:
        name = party.get("name", "N/A")
        balance = party.get("closing_balance", "0")
        parent = party.get("parent", "N/A")
        response += f"• {name}\n  Balance: ₹{balance} ({parent})\n\n"
    
    if len(parties) > 15:
        response += f"... and {len(parties) - 15} more parties"
    
    # Only send WhatsApp message if not WebSocket
    if not is_websocket:
        send_whatsapp_message(from_number, response)
        add_assistant_message(user.id, response)
    
    return {"status": "success", "content": response}
