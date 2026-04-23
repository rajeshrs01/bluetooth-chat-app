"""
test_contacts.py
Unit tests for ContactBook (uses a temp SQLite DB).
"""

import pytest
from src.core.contacts import Contact, ContactBook


@pytest.fixture
def book(tmp_path):
    """Fresh ContactBook backed by a temp SQLite file."""
    return ContactBook(db_path=str(tmp_path / "test_contacts.db"))


def test_add_and_get(book):
    c = Contact(address="AA:BB:CC:DD:EE:FF", name="Alice")
    book.add_or_update(c)
    fetched = book.get("AA:BB:CC:DD:EE:FF")
    assert fetched is not None
    assert fetched.name == "Alice"


def test_update_existing(book):
    book.add_or_update(Contact(address="AA:BB:CC:DD:EE:FF", name="Alice"))
    book.add_or_update(Contact(address="AA:BB:CC:DD:EE:FF", name="Alice Smith"))
    assert book.get("AA:BB:CC:DD:EE:FF").name == "Alice Smith"


def test_delete(book):
    book.add_or_update(Contact(address="11:22:33:44:55:66", name="Bob"))
    assert book.delete("11:22:33:44:55:66") is True
    assert book.get("11:22:33:44:55:66") is None


def test_all_sorted_by_last_seen(book):
    book.add_or_update(Contact(address="AA:BB:CC:DD:EE:01", name="Zara",  last_seen="2024-01-01 09:00"))
    book.add_or_update(Contact(address="AA:BB:CC:DD:EE:02", name="Alice", last_seen="2024-06-15 14:00"))
    contacts = book.all()
    # Most recent first
    assert contacts[0].name == "Alice"


def test_search(book):
    book.add_or_update(Contact(address="AA:BB:CC:DD:EE:FF", name="Alice"))
    book.add_or_update(Contact(address="11:22:33:44:55:66", name="Bob"))
    results = book.search("ali")
    assert len(results) == 1
    assert results[0].name == "Alice"


def test_record_message_creates_contact(book):
    book.record_message("DE:AD:BE:EF:00:01", "Charlie")
    c = book.get("DE:AD:BE:EF:00:01")
    assert c is not None
    assert c.message_count == 1


def test_record_message_increments_count(book):
    book.add_or_update(Contact(address="DE:AD:BE:EF:00:01", name="Charlie"))
    book.record_message("DE:AD:BE:EF:00:01", "Charlie")
    book.record_message("DE:AD:BE:EF:00:01", "Charlie")
    assert book.get("DE:AD:BE:EF:00:01").message_count == 2


def test_display_name_fallback(book):
    assert book.display_name("00:00:00:00:00:00") == "00:00:00:00:00:00"
    book.add_or_update(Contact(address="00:00:00:00:00:00", name="Dave"))
    assert book.display_name("00:00:00:00:00:00") == "Dave"
