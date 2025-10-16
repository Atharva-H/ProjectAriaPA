# app/services/conversation_manager.py
from collections import defaultdict, deque
from typing import List, Dict

# Lightweight in-memory conversation store (per-process)
_user_conversations: Dict[int, deque] = defaultdict(lambda: deque(maxlen=10))

def add_user_message(user_id: int, content: str) -> None:
    _user_conversations[user_id].append({"role": "user", "content": content})

def add_assistant_message(user_id: int, content: str) -> None:
    _user_conversations[user_id].append({"role": "assistant", "content": content})

def get_recent_chat(user_id: int, limit: int = 5) -> List[Dict[str, str]]:
    conv = _user_conversations.get(user_id)
    if not conv:
        return []
    return list(conv)[-limit:]

def clear_chat(user_id: int) -> None:
    _user_conversations.pop(user_id, None)
