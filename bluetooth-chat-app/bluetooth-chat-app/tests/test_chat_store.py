"""
test_chat_store.py
Unit tests for the ChatStore class.
"""

import pytest
from src.core.chat_store import ChatStore, Message


def test_add_message():
    store = ChatStore()
    msg = store.add("me", "Hello!")
    assert isinstance(msg, Message)
    assert msg.sender == "me"
    assert msg.text == "Hello!"


def test_all_messages():
    store = ChatStore()
    store.add("me", "Hi")
    store.add("friend", "Hey!")
    msgs = store.all()
    assert len(msgs) == 2
    assert msgs[0].sender == "me"
    assert msgs[1].sender == "friend"


def test_clear():
    store = ChatStore()
    store.add("me", "test")
    store.clear()
    assert store.all() == []


def test_save_and_load(tmp_path):
    path = str(tmp_path / "history.json")
    store = ChatStore(history_file=path)
    store.add("me", "Saved message")
    store.save()

    store2 = ChatStore(history_file=path)
    store2.load()
    msgs = store2.all()
    assert len(msgs) == 1
    assert msgs[0].text == "Saved message"
