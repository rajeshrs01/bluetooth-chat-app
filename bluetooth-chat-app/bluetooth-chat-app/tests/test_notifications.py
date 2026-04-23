"""
test_notifications.py
Unit tests for NotificationManager.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.core.notifications import NotificationManager


def test_notifications_disabled():
    mgr = NotificationManager(sound_enabled=False, desktop_enabled=False)
    mgr.on_message("Alice", "Hello!")
    mgr.on_call_incoming("Bob")
    mgr.on_file_received("photo.jpg")


def test_on_message_spawns_thread():
    mgr = NotificationManager(sound_enabled=False, desktop_enabled=False)
    with patch("threading.Thread") as mock_thread:
        mock_thread.return_value = MagicMock()
        mgr.on_message("Alice", "Hello")
        mock_thread.assert_called_once()


def test_on_connected_and_disconnected_no_crash():
    mgr = NotificationManager(sound_enabled=False, desktop_enabled=False)
    mgr.on_connected("Device A")
    mgr.on_disconnected()


def test_desktop_notification_linux():
    mgr = NotificationManager(sound_enabled=False, desktop_enabled=True)
    with patch("sys.platform", "linux"), \
         patch("subprocess.run") as mock_run:
        mgr._notify("Test title", "Test body")
        import time; time.sleep(0.05)


def test_desktop_notification_macos():
    mgr = NotificationManager(sound_enabled=False, desktop_enabled=True)
    with patch("sys.platform", "darwin"), \
         patch("subprocess.run") as mock_run:
        mgr._notify("Test title", "Test body")
