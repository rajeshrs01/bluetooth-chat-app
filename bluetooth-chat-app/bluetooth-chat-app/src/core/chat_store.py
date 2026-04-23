"""
chat_store.py
Simple in-memory chat history with optional file persistence.
"""

import json
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List


@dataclass
class Message:
    sender: str        # "me" or remote device name/address
    text: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))


class ChatStore:
    """Stores messages in memory and can save/load from a JSON file."""

    def __init__(self, history_file: str = "chat_history.json"):
        self.history_file = history_file
        self._messages: List[Message] = []

    def add(self, sender: str, text: str) -> Message:
        msg = Message(sender=sender, text=text)
        self._messages.append(msg)
        return msg

    def all(self) -> List[Message]:
        return list(self._messages)

    def clear(self):
        self._messages.clear()

    def save(self):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump([asdict(m) for m in self._messages], f, indent=2)

    def load(self):
        if not os.path.exists(self.history_file):
            return
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._messages = [Message(**d) for d in data]
        except Exception:
            self._messages = []
