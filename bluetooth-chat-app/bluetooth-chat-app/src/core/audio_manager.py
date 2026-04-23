"""
audio_manager.py
Handles real-time audio streaming for voice calls over an open socket.
"""

import threading
import socket
from typing import Optional

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


CHUNK = 1024
FORMAT_CODE = 8        # paInt16 = 8
CHANNELS = 1
RATE = 44100


class AudioManager:
    """Streams microphone audio bidirectionally over a raw socket."""

    def __init__(self):
        self._p: Optional["pyaudio.PyAudio"] = None
        self._in_stream = None
        self._out_stream = None
        self._send_thread: Optional[threading.Thread] = None
        self._recv_thread: Optional[threading.Thread] = None
        self._active = False

        if PYAUDIO_AVAILABLE:
            import pyaudio as _pa
            self._pa = _pa
            self._FORMAT = _pa.paInt16
        else:
            self._FORMAT = FORMAT_CODE

    def is_available(self) -> bool:
        return PYAUDIO_AVAILABLE

    def start_call(self, sock) -> bool:
        """Begin two-way audio over `sock` (a connected BluetoothSocket)."""
        if not PYAUDIO_AVAILABLE:
            return False

        self._p = self._pa.PyAudio()
        self._active = True

        self._in_stream = self._p.open(
            format=self._FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
        self._out_stream = self._p.open(
            format=self._FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True,
            frames_per_buffer=CHUNK,
        )

        self._send_thread = threading.Thread(
            target=self._send_loop, args=(sock,), daemon=True
        )
        self._recv_thread = threading.Thread(
            target=self._recv_loop, args=(sock,), daemon=True
        )
        self._send_thread.start()
        self._recv_thread.start()
        return True

    def stop_call(self):
        """Stop audio streaming and release resources."""
        self._active = False
        for stream in (self._in_stream, self._out_stream):
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
        if self._p:
            try:
                self._p.terminate()
            except Exception:
                pass
        self._in_stream = None
        self._out_stream = None
        self._p = None

    # ------------------------------------------------------------------ #
    #  Internal loops
    # ------------------------------------------------------------------ #

    def _send_loop(self, sock):
        """Read from microphone and send over socket."""
        while self._active:
            try:
                data = self._in_stream.read(CHUNK, exception_on_overflow=False)
                # Prefix so receiver can distinguish audio from chat messages
                sock.send(b"AUD:" + data)
            except Exception:
                break

    def _recv_loop(self, sock):
        """Receive from socket and play to speaker."""
        while self._active:
            try:
                raw = sock.recv(CHUNK * 2 + 4)  # 4 bytes for "AUD:" prefix
                if raw.startswith(b"AUD:"):
                    self._out_stream.write(raw[4:])
            except Exception:
                break
