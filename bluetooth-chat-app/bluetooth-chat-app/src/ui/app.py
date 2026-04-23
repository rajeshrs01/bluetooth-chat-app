"""
app.py
Terminal UI for BlueChat using Python's built-in `curses` library.
Provides: device scan, host/join, chat window, and call controls.
"""

import curses
import threading
from typing import Optional

from src.core.bluetooth_manager import BluetoothManager, BluetoothDevice
from src.core.audio_manager import AudioManager
from src.core.chat_store import ChatStore


class BlueChatApp:
    def __init__(self):
        self.bt = BluetoothManager()
        self.audio = AudioManager()
        self.store = ChatStore()
        self.connected_device: Optional[str] = None
        self.in_call = False
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    #  Main entry
    # ------------------------------------------------------------------ #

    def run(self):
        curses.wrapper(self._main)

    # ------------------------------------------------------------------ #
    #  Curses main loop
    # ------------------------------------------------------------------ #

    def _main(self, stdscr):
        curses.curs_set(1)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN,    curses.COLOR_BLACK)  # header
        curses.init_pair(2, curses.COLOR_GREEN,   curses.COLOR_BLACK)  # me
        curses.init_pair(3, curses.COLOR_YELLOW,  curses.COLOR_BLACK)  # remote
        curses.init_pair(4, curses.COLOR_RED,     curses.COLOR_BLACK)  # system
        curses.init_pair(5, curses.COLOR_WHITE,   curses.COLOR_BLUE)   # status bar

        self.stdscr = stdscr
        self._show_menu()

    # ------------------------------------------------------------------ #
    #  Menu screen
    # ------------------------------------------------------------------ #

    def _show_menu(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        banner = [
            "  ____  _            ____ _           _  ",
            " | __ )| |_   _  ___/ ___| |__   __ _| |_ ",
            " |  _ \\| | | | |/ _ \\___ \\| '_ \\ / _` | __|",
            " | |_) | | |_| |  __/___) | | | | (_| | |_ ",
            " |____/|_|\\__,_|\\___|____/|_| |_|\\__,_|\\__|",
            "",
            "   Bluetooth Chat & Voice App  |  Python",
        ]
        for i, line in enumerate(banner):
            x = max(0, (w - len(line)) // 2)
            self.stdscr.addstr(i + 1, x, line, curses.color_pair(1))

        options = [
            ("1", "Host a session  (wait for someone to join)"),
            ("2", "Join a session  (scan & connect to a host)"),
            ("q", "Quit"),
        ]
        row = len(banner) + 3
        for key, label in options:
            self.stdscr.addstr(row, 4, f"[{key}]", curses.color_pair(2) | curses.A_BOLD)
            self.stdscr.addstr(row, 8, f" {label}")
            row += 2

        self.stdscr.refresh()

        while True:
            ch = self.stdscr.getch()
            if ch == ord("1"):
                self._host_session()
                break
            elif ch == ord("2"):
                self._join_session()
                break
            elif ch in (ord("q"), ord("Q")):
                break

    # ------------------------------------------------------------------ #
    #  Host
    # ------------------------------------------------------------------ #

    def _host_session(self):
        self.stdscr.clear()
        self._status("Starting server …")
        port = self.bt.start_server(self._on_client_connected)
        self._status(f"Advertising on RFCOMM channel {port}. Waiting for a friend to join …")
        self.stdscr.refresh()
        # Block until connected (poll)
        while not self.bt.connected:
            import time
            time.sleep(0.2)

    def _on_client_connected(self, address: str):
        self.connected_device = address
        self.bt.on_message = self._on_message_received
        self.bt.on_disconnect = self._on_disconnected
        self._open_chat()

    # ------------------------------------------------------------------ #
    #  Join
    # ------------------------------------------------------------------ #

    def _join_session(self):
        self.stdscr.clear()
        self._status("Scanning for devices (8 s) …")
        self.stdscr.refresh()
        try:
            devices = self.bt.scan_devices()
        except RuntimeError as e:
            self._status(f"ERROR: {e}  — press any key.")
            self.stdscr.getch()
            return

        if not devices:
            self._status("No devices found. Press any key to go back.")
            self.stdscr.getch()
            return

        self._pick_device(devices)

    def _pick_device(self, devices):
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, "Select a device:", curses.color_pair(1) | curses.A_BOLD)
        for i, d in enumerate(devices):
            self.stdscr.addstr(i + 2, 2, f"[{i}] {d}")
        self.stdscr.addstr(len(devices) + 3, 0, "Enter number: ")
        self.stdscr.refresh()

        curses.echo()
        try:
            choice = int(self.stdscr.getstr().decode())
            device = devices[choice]
        except (ValueError, IndexError):
            return
        finally:
            curses.noecho()

        self._status(f"Connecting to {device} …")
        self.stdscr.refresh()
        if self.bt.connect(device):
            self.connected_device = device.address
            self.bt.on_message = self._on_message_received
            self.bt.on_disconnect = self._on_disconnected
            self._open_chat()
        else:
            self._status("Connection failed. BlueChatService not found. Press any key.")
            self.stdscr.getch()

    # ------------------------------------------------------------------ #
    #  Chat window
    # ------------------------------------------------------------------ #

    def _open_chat(self):
        self.stdscr.clear()
        self.stdscr.refresh()
        self._chat_loop()

    def _chat_loop(self):
        h, w = self.stdscr.getmaxyx()
        msg_win = curses.newwin(h - 3, w, 0, 0)
        input_win = curses.newwin(3, w, h - 3, 0)
        msg_win.scrollok(True)
        input_win.keypad(True)

        self._draw_status_bar(input_win, w)
        msg_win.addstr(0, 0, f"Connected to {self.connected_device}\n",
                       curses.color_pair(1) | curses.A_BOLD)
        msg_win.addstr("Type a message and press Enter. Commands: /call  /hangup  /quit\n\n",
                       curses.color_pair(4))
        msg_win.refresh()

        self._msg_win = msg_win

        input_buf = []

        while True:
            self._draw_status_bar(input_win, w)
            input_win.move(1, 2 + len(input_buf))
            input_win.refresh()

            ch = input_win.getch()

            if ch in (curses.KEY_ENTER, 10, 13):
                line = "".join(input_buf).strip()
                input_buf.clear()
                input_win.clear()
                self._draw_status_bar(input_win, w)
                if not line:
                    continue
                if line == "/quit":
                    self.bt.disconnect()
                    if self.in_call:
                        self.audio.stop_call()
                    break
                elif line == "/call":
                    self._start_call(msg_win)
                elif line == "/hangup":
                    self._end_call(msg_win)
                else:
                    self.bt.send_message(line)
                    msg = self.store.add("me", line)
                    self._print_msg(msg_win, msg)

            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                if input_buf:
                    input_buf.pop()
                    input_win.clear()
                    self._draw_status_bar(input_win, w)
                    input_win.addstr(1, 2, "".join(input_buf))
            elif 32 <= ch <= 126:
                input_buf.append(chr(ch))
                input_win.addstr(1, 2, "".join(input_buf))

    def _print_msg(self, win, msg):
        if msg.sender == "me":
            win.addstr(f"[{msg.timestamp}] ", curses.color_pair(4))
            win.addstr("You: ", curses.color_pair(2) | curses.A_BOLD)
        else:
            win.addstr(f"[{msg.timestamp}] ", curses.color_pair(4))
            win.addstr(f"{msg.sender}: ", curses.color_pair(3) | curses.A_BOLD)
        win.addstr(msg.text + "\n")
        win.refresh()

    def _draw_status_bar(self, win, w):
        call_status = " 🔴 IN CALL" if self.in_call else " ⚫ No call"
        bar = f" Connected: {self.connected_device or '—'}{call_status}"
        bar = bar[:w - 1].ljust(w - 1)
        win.attron(curses.color_pair(5))
        win.addstr(0, 0, bar)
        win.attroff(curses.color_pair(5))
        win.addstr(1, 0, "> ")

    # ------------------------------------------------------------------ #
    #  Call helpers
    # ------------------------------------------------------------------ #

    def _start_call(self, win):
        if not self.audio.is_available():
            win.addstr("⚠  PyAudio not installed. Run: pip install pyaudio\n",
                       curses.color_pair(4))
            win.refresh()
            return
        if self.in_call:
            win.addstr("Already in a call.\n", curses.color_pair(4))
            win.refresh()
            return
        self.audio.start_call(self.bt.socket)
        self.in_call = True
        win.addstr("📞 Call started! Use /hangup to end.\n", curses.color_pair(2))
        win.refresh()

    def _end_call(self, win):
        if not self.in_call:
            win.addstr("Not in a call.\n", curses.color_pair(4))
            win.refresh()
            return
        self.audio.stop_call()
        self.in_call = False
        win.addstr("📵 Call ended.\n", curses.color_pair(4))
        win.refresh()

    # ------------------------------------------------------------------ #
    #  Callbacks
    # ------------------------------------------------------------------ #

    def _on_message_received(self, text: str):
        msg = self.store.add(self.connected_device or "Remote", text)
        if hasattr(self, "_msg_win"):
            self._print_msg(self._msg_win, msg)

    def _on_disconnected(self):
        if self.in_call:
            self.audio.stop_call()
            self.in_call = False
        if hasattr(self, "_msg_win"):
            self._msg_win.addstr("\n⚠  Disconnected from remote device.\n",
                                 curses.color_pair(4))
            self._msg_win.refresh()

    # ------------------------------------------------------------------ #
    #  Utility
    # ------------------------------------------------------------------ #

    def _status(self, text: str):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(h - 1, 0, text[:w - 1], curses.color_pair(5))
