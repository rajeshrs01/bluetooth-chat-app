"""
contacts.py
Persistent contacts / address book backed by SQLite.
Stores Bluetooth address, display name, notes, and last-seen timestamp.
"""

import sqlite3
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


DB_PATH = "contacts.db"


@dataclass
class Contact:
    address: str                   # Bluetooth MAC address (primary key)
    name: str                      # Display name
    notes: str = ""
    last_seen: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    message_count: int = 0

    def __str__(self):
        return f"{self.name} [{self.address}]"


class ContactBook:
    """SQLite-backed address book for BlueChat."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------ #
    #  Setup
    # ------------------------------------------------------------------ #

    def _init_db(self):
        with self._conn() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    address       TEXT PRIMARY KEY,
                    name          TEXT NOT NULL,
                    notes         TEXT DEFAULT '',
                    last_seen     TEXT,
                    message_count INTEGER DEFAULT 0
                )
            """)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    # ------------------------------------------------------------------ #
    #  CRUD
    # ------------------------------------------------------------------ #

    def add_or_update(self, contact: Contact) -> Contact:
        """Insert a new contact or update name/notes if address already exists."""
        with self._conn() as con:
            con.execute("""
                INSERT INTO contacts (address, name, notes, last_seen, message_count)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(address) DO UPDATE SET
                    name          = excluded.name,
                    notes         = excluded.notes,
                    last_seen     = excluded.last_seen,
                    message_count = excluded.message_count
            """, (
                contact.address,
                contact.name,
                contact.notes,
                contact.last_seen,
                contact.message_count,
            ))
        return contact

    def get(self, address: str) -> Optional[Contact]:
        with self._conn() as con:
            row = con.execute(
                "SELECT address, name, notes, last_seen, message_count "
                "FROM contacts WHERE address = ?", (address,)
            ).fetchone()
        return Contact(*row) if row else None

    def all(self) -> List[Contact]:
        with self._conn() as con:
            rows = con.execute(
                "SELECT address, name, notes, last_seen, message_count "
                "FROM contacts ORDER BY last_seen DESC"
            ).fetchall()
        return [Contact(*r) for r in rows]

    def delete(self, address: str) -> bool:
        with self._conn() as con:
            cur = con.execute("DELETE FROM contacts WHERE address = ?", (address,))
        return cur.rowcount > 0

    def search(self, query: str) -> List[Contact]:
        """Search by name or address (case-insensitive)."""
        q = f"%{query.lower()}%"
        with self._conn() as con:
            rows = con.execute(
                "SELECT address, name, notes, last_seen, message_count "
                "FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(address) LIKE ? "
                "ORDER BY name",
                (q, q),
            ).fetchall()
        return [Contact(*r) for r in rows]

    # ------------------------------------------------------------------ #
    #  Helpers called during chat sessions
    # ------------------------------------------------------------------ #

    def record_message(self, address: str, name: str):
        """Auto-create or update a contact when a message is received."""
        existing = self.get(address)
        if existing:
            existing.message_count += 1
            existing.last_seen = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.add_or_update(existing)
        else:
            self.add_or_update(Contact(
                address=address,
                name=name,
                message_count=1,
            ))

    def display_name(self, address: str, fallback: str = "") -> str:
        """Return saved name for an address, or fallback (usually the raw address)."""
        contact = self.get(address)
        return contact.name if contact else (fallback or address)
