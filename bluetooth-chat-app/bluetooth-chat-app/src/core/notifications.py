"""
notifications.py
Sound and system notifications for BlueChat.
Plays a beep on incoming messages and (on Linux) sends a desktop notification.
"""

import threading
import sys
from typing import Optional


class NotificationManager:
    """Plays sounds and sends desktop alerts for chat events."""

    def __init__(self, sound_enabled: bool = True, desktop_enabled: bool = True):
        self.sound_enabled = sound_enabled
        self.desktop_enabled = desktop_enabled
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def on_message(self, sender: str, preview: str = ""):
        """Call when a new message arrives."""
        threading.Thread(
            target=self._notify,
            args=(f"New message from {sender}", preview[:80]),
            daemon=True,
        ).start()

    def on_call_incoming(self, caller: str):
        """Call when a voice call starts."""
        threading.Thread(
            target=self._notify,
            args=(f"Incoming call from {caller}", "Use /hangup to end"),
            daemon=True,
        ).start()
        self._beep(frequency=880, duration=0.4, repeats=3)

    def on_file_received(self, filename: str):
        """Call when a file transfer completes."""
        threading.Thread(
            target=self._notify,
            args=("File received", filename),
            daemon=True,
        ).start()
        self._beep(frequency=600, duration=0.15, repeats=2)

    def on_connected(self, device: str):
        self._beep(frequency=660, duration=0.1, repeats=2)

    def on_disconnected(self):
        self._beep(frequency=300, duration=0.3, repeats=1)

    # ------------------------------------------------------------------ #
    #  Desktop notification (Linux via notify-send, macOS via osascript)
    # ------------------------------------------------------------------ #

    def _notify(self, title: str, body: str = ""):
        if not self.desktop_enabled:
            return
        try:
            if sys.platform.startswith("linux"):
                import subprocess
                subprocess.run(
                    ["notify-send", "--app-name=BlueChat", title, body],
                    check=False, timeout=3,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            elif sys.platform == "darwin":
                import subprocess
                script = f'display notification "{body}" with title "{title}"'
                subprocess.run(
                    ["osascript", "-e", script],
                    check=False, timeout=3,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass  # notifications are best-effort

    # ------------------------------------------------------------------ #
    #  Terminal beep (cross-platform)
    # ------------------------------------------------------------------ #

    def _beep(self, frequency: int = 440, duration: float = 0.2, repeats: int = 1):
        if not self.sound_enabled:
            return
        try:
            if sys.platform.startswith("linux"):
                self._beep_linux(frequency, duration, repeats)
            else:
                for _ in range(repeats):
                    print("\a", end="", flush=True)
        except Exception:
            pass

    def _beep_linux(self, frequency: int, duration: float, repeats: int):
        """Use PyAudio to produce a sine-wave beep on Linux."""
        try:
            import pyaudio
            import math
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paFloat32, channels=1, rate=44100, output=True)
            samples_per_beep = int(44100 * duration)
            silence = bytes(samples_per_beep * 4 // 2)  # 50% duty cycle gap

            for _ in range(repeats):
                wave = bytes(
                    int(
                        0.3 * math.sin(2 * math.pi * frequency * i / 44100)
                        * 127 + 128
                    ).to_bytes(4, "little")
                    for i in range(samples_per_beep)
                )
                stream.write(wave)
                stream.write(silence)

            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception:
            print("\a", end="", flush=True)
