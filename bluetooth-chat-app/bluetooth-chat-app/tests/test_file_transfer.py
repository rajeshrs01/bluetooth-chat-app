"""
test_file_transfer.py
Unit tests for FileTransfer using mock sockets.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from src.core.file_transfer import FileTransfer


class MockSocket:
    """Minimal socket mock that records sent data."""
    def __init__(self):
        self.sent = []

    def send(self, data: bytes):
        self.sent.append(data)

    def total_sent(self) -> bytes:
        return b"".join(self.sent)


def test_send_and_receive_roundtrip(tmp_path):
    """Write a file, send it, parse on the receiving end, and verify contents."""
    # Create a test file
    test_file = tmp_path / "hello.txt"
    test_file.write_bytes(b"Hello, Bluetooth World!")

    # Sender side
    send_sock = MockSocket()
    ft_sender = FileTransfer(send_sock)
    result = ft_sender.send_file(str(test_file))
    assert result is True

    # Reconstruct what was sent
    raw_sent = send_sock.total_sent().decode("utf-8")

    # Receiver side
    recv_sock = MockSocket()
    received_files = []
    ft_receiver = FileTransfer(
        recv_sock,
        on_file_received=lambda name, path: received_files.append((name, path))
    )

    with patch("src.core.file_transfer.DOWNLOAD_DIR", str(tmp_path / "downloads")):
        os.makedirs(str(tmp_path / "downloads"), exist_ok=True)
        # Strip "FILE:" prefix handled internally
        handled = ft_receiver.handle_incoming(raw_sent)

    assert handled is True
    assert len(received_files) == 1
    name, path = received_files[0]
    assert name == "hello.txt"
    assert open(path, "rb").read() == b"Hello, Bluetooth World!"


def test_send_nonexistent_file():
    sock = MockSocket()
    ft = FileTransfer(sock)
    assert ft.send_file("/nonexistent/file.txt") is False


def test_unique_path(tmp_path):
    p = str(tmp_path / "file.txt")
    open(p, "w").close()
    unique = FileTransfer._unique_path(p)
    assert unique == str(tmp_path / "file_1.txt")


def test_progress_bar():
    bar = FileTransfer.progress_bar(50, 100, width=10)
    assert "50.0%" in bar
    assert "█" in bar
    assert "░" in bar


def test_handle_ack():
    sock = MockSocket()
    ft = FileTransfer(sock)
    assert ft.handle_ack("ACK:report.pdf") == "report.pdf"
    assert ft.handle_ack("ERR:disk full") == "ERROR — disk full"
    assert ft.handle_ack("MSG:hello") is None
