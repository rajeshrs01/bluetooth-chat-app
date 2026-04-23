"""
file_transfer.py
Sends and receives files over an existing RFCOMM Bluetooth socket.

Protocol:
  Sender:   FILE:<filename>:<filesize>:<base64_data>
  Receiver: ACK:<filename>  (on success)  |  ERR:<reason>  (on failure)

Files are chunked and base64-encoded so they pass cleanly through
the same UTF-8 text channel used for chat messages.
"""

import os
import base64
import threading
from pathlib import Path
from typing import Callable, Optional


CHUNK_SIZE = 4096         # bytes per Bluetooth send
DOWNLOAD_DIR = "downloads"


class FileTransfer:
    """Handles sending and receiving files over a connected socket."""

    def __init__(self, sock, on_file_received: Optional[Callable] = None):
        """
        sock              : connected BluetoothSocket
        on_file_received  : callback(filename: str, path: str) when a file arrives
        """
        self.sock = sock
        self.on_file_received = on_file_received
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  Sending
    # ------------------------------------------------------------------ #

    def send_file(
        self,
        filepath: str,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """
        Send a file. `on_progress(bytes_sent, total_bytes)` is called each chunk.
        Returns True on success.
        """
        path = Path(filepath)
        if not path.exists():
            return False

        total = path.stat().st_size
        filename = path.name

        try:
            with open(path, "rb") as f:
                raw = f.read()

            b64 = base64.b64encode(raw).decode("ascii")
            header = f"FILE:{filename}:{total}:{b64}"

            # Send in chunks
            sent = 0
            data = header.encode("utf-8")
            while sent < len(data):
                chunk = data[sent : sent + CHUNK_SIZE]
                self.sock.send(chunk)
                sent += len(chunk)
                if on_progress:
                    on_progress(min(sent, total), total)

            return True
        except Exception as e:
            print(f"[FileTransfer] Send error: {e}")
            return False

    # ------------------------------------------------------------------ #
    #  Receiving  (called from bluetooth_manager's recv loop)
    # ------------------------------------------------------------------ #

    def handle_incoming(self, raw_text: str) -> bool:
        """
        Called by the BT manager when a message starts with 'FILE:'.
        Returns True if this was a file message (consumed), False otherwise.
        """
        if not raw_text.startswith("FILE:"):
            return False

        try:
            _, filename, size_str, b64_data = raw_text.split(":", 3)
            expected_size = int(size_str)
            file_bytes = base64.b64decode(b64_data)

            if len(file_bytes) != expected_size:
                self._send_ack(f"ERR:size mismatch for {filename}")
                return True

            save_path = os.path.join(DOWNLOAD_DIR, filename)
            # Avoid overwriting — append a counter if needed
            save_path = self._unique_path(save_path)
            with open(save_path, "wb") as f:
                f.write(file_bytes)

            self._send_ack(f"ACK:{filename}")
            if self.on_file_received:
                self.on_file_received(filename, save_path)

        except Exception as e:
            self._send_ack(f"ERR:{e}")

        return True

    def handle_ack(self, raw_text: str) -> Optional[str]:
        """Returns ACK filename or error string, or None if not an ACK."""
        if raw_text.startswith("ACK:"):
            return raw_text[4:]
        if raw_text.startswith("ERR:"):
            return f"ERROR — {raw_text[4:]}"
        return None

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _send_ack(self, message: str):
        try:
            self.sock.send(message.encode("utf-8"))
        except Exception:
            pass

    @staticmethod
    def _unique_path(path: str) -> str:
        """If path exists, append _1, _2 … until unique."""
        if not os.path.exists(path):
            return path
        base, ext = os.path.splitext(path)
        counter = 1
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1
        return f"{base}_{counter}{ext}"

    # ------------------------------------------------------------------ #
    #  Progress bar (terminal helper)
    # ------------------------------------------------------------------ #

    @staticmethod
    def progress_bar(sent: int, total: int, width: int = 30) -> str:
        """Returns a simple ASCII progress bar string."""
        pct = sent / total if total else 1
        filled = int(width * pct)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {pct*100:.1f}%  ({sent}/{total} bytes)"
