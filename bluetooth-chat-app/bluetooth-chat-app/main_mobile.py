"""
main_mobile.py
BlueChat Android app built with Kivy.
Entry point for the APK.

Screens:
  HomeScreen  — welcome + navigation
  ScanScreen  — BLE device discovery
  ChatScreen  — two-way messaging
"""

import os
import sys
from datetime import datetime

# Kivy must be configured before import
os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.core.window import Window

from mobile.ble_manager import BLEManager, BLEDevice
from src.core.chat_store import ChatStore
from src.core.contacts import ContactBook

# Load KV layout
KV_FILE = os.path.join(os.path.dirname(__file__), "mobile", "bluechat.kv")
Builder.load_file(KV_FILE)


# ──────────────────────────────────────────────────────────────────────────────
#  Home Screen
# ──────────────────────────────────────────────────────────────────────────────

class HomeScreen(Screen):
    def go_scan(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "scan"

    def go_contacts(self):
        app = App.get_running_app()
        contacts = app.contact_book.all()
        if not contacts:
            self._toast("No contacts yet — connect to someone first!")
            return
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "scan"

    def _toast(self, text):
        popup = Popup(
            title="",
            content=Label(text=text, font_size="14sp"),
            size_hint=(0.8, 0.18),
            auto_dismiss=True,
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2.5)


# ──────────────────────────────────────────────────────────────────────────────
#  Scan Screen
# ──────────────────────────────────────────────────────────────────────────────

class ScanScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._devices: list[BLEDevice] = []

    def start_scan(self):
        app = App.get_running_app()
        self.ids.scan_btn.text = "Scanning…"
        self.ids.scan_btn.disabled = True
        self.ids.scan_status.text = "Looking for nearby Bluetooth devices…"
        self.ids.device_list.clear_widgets()
        self._devices.clear()

        app.ble.scan(duration=8.0, callback=self._on_scan_done)

    def _on_scan_done(self, devices: list):
        """Called from BLE thread — schedule UI update on main thread."""
        Clock.schedule_once(lambda dt: self._show_devices(devices))

    def _show_devices(self, devices):
        self.ids.scan_btn.text = "Scan for devices"
        self.ids.scan_btn.disabled = False

        if not devices:
            self.ids.scan_status.text = "No devices found. Make sure Bluetooth is on."
            return

        self.ids.scan_status.text = f"Found {len(devices)} device(s) — tap one to connect"
        self._devices = devices

        for i, device in enumerate(devices):
            row = self._make_device_row(device, i)
            self.ids.device_list.add_widget(row)

    def _make_device_row(self, device: BLEDevice, index: int) -> BoxLayout:
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            padding=[0, dp(4)],
            spacing=dp(12),
        )

        # Text info
        info = BoxLayout(orientation="vertical", spacing=dp(2))
        name_label = Label(
            text=device.name or "Unknown device",
            font_size="15sp",
            bold=True,
            color=(0.173, 0.173, 0.165, 1),
            halign="left",
            valign="middle",
        )
        name_label.bind(size=name_label.setter("text_size"))

        addr_label = Label(
            text=device.address,
            font_size="12sp",
            color=(0.537, 0.529, 0.502, 1),
            halign="left",
            valign="middle",
        )
        addr_label.bind(size=addr_label.setter("text_size"))
        info.add_widget(name_label)
        info.add_widget(addr_label)

        # Connect button
        btn = Button(
            text="Connect",
            size_hint=(None, None),
            size=(dp(90), dp(36)),
            background_color=(0, 0, 0, 0),
        )
        btn.bind(on_release=lambda _, d=device: self.connect_to(d))

        row.add_widget(info)
        row.add_widget(btn)
        return row

    def connect_to(self, device: BLEDevice):
        app = App.get_running_app()
        self.ids.scan_status.text = f"Connecting to {device.name or device.address}…"

        def on_done(success: bool):
            Clock.schedule_once(lambda dt: self._on_connect_result(success, device))

        app.ble.connect(device, on_done=on_done)

    def _on_connect_result(self, success: bool, device: BLEDevice):
        if success:
            app = App.get_running_app()
            chat: ChatScreen = self.manager.get_screen("chat")
            chat.open_with(device)
            self.manager.transition = SlideTransition(direction="left")
            self.manager.current = "chat"
        else:
            self.ids.scan_status.text = "Connection failed — try again"


# ──────────────────────────────────────────────────────────────────────────────
#  Chat Screen
# ──────────────────────────────────────────────────────────────────────────────

class ChatScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._device: BLEDevice | None = None
        self._store = ChatStore()

    def open_with(self, device: BLEDevice):
        self._device = device
        self._store.clear()
        self.ids.chat_title.text = device.name or device.address
        self.ids.status_dot.text = "● Connected"
        self.ids.status_dot.color = (0.557, 0.941, 0.710, 1)
        self.ids.chat_messages.clear_widgets()

        app = App.get_running_app()
        app.ble.on_message = self._on_incoming
        app.ble.on_disconnect = self._on_disconnected

        # Auto-save contact
        app.contact_book.record_message(device.address, device.name or device.address)

    def send_message(self):
        text = self.ids.msg_input.text.strip()
        if not text:
            return
        self.ids.msg_input.text = ""

        app = App.get_running_app()
        if app.ble.send_message(text):
            msg = self._store.add("me", text)
            Clock.schedule_once(lambda dt: self._add_bubble(msg.text, is_mine=True, time=msg.timestamp))

    def _on_incoming(self, text: str):
        msg = self._store.add(self._device.name or "Remote", text)
        Clock.schedule_once(lambda dt: self._add_bubble(msg.text, is_mine=False, time=msg.timestamp))

    def _on_disconnected(self):
        Clock.schedule_once(lambda dt: self._mark_disconnected())

    def _mark_disconnected(self):
        self.ids.status_dot.text = "○ Disconnected"
        self.ids.status_dot.color = (0.9, 0.4, 0.4, 1)
        self._add_bubble("Connection lost", is_mine=False, time="", is_system=True)

    def _add_bubble(self, text: str, is_mine: bool, time: str, is_system: bool = False):
        """Render a chat bubble and scroll to bottom."""
        wrapper = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(1),        # will be updated after render
            padding=[0, dp(2)],
        )

        if is_system:
            lbl = Label(
                text=text,
                font_size="12sp",
                color=(0.6, 0.6, 0.6, 1),
                size_hint=(1, None),
                halign="center",
            )
            lbl.bind(texture_size=lambda *a: setattr(lbl, "height", lbl.texture_size[1] + dp(8)))
            lbl.bind(texture_size=lambda *a: setattr(wrapper, "height", lbl.height + dp(4)))
            lbl.bind(size=lbl.setter("text_size"))
            wrapper.add_widget(lbl)
            self.ids.chat_messages.add_widget(wrapper)
            self._scroll_bottom()
            return

        bubble_color = (0.094, 0.373, 0.647, 1) if is_mine else (1, 1, 1, 1)
        text_color   = (1, 1, 1, 1) if is_mine else (0.173, 0.173, 0.165, 1)

        spacer_before = BoxLayout(size_hint_x=0.15 if is_mine else None, size_hint_y=None, height=1)
        spacer_after  = BoxLayout(size_hint_x=0.15 if not is_mine else None, size_hint_y=None, height=1)

        bubble_outer = BoxLayout(
            orientation="vertical",
            size_hint_x=0.85,
            size_hint_y=None,
            height=dp(1),
            padding=[dp(12), dp(8)],
            spacing=dp(2),
        )
        with bubble_outer.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*bubble_color)
            self._bubble_rect = RoundedRectangle(
                pos=bubble_outer.pos,
                size=bubble_outer.size,
                radius=[dp(14)],
            )
        bubble_outer.bind(pos=lambda *a: setattr(self._bubble_rect, "pos", bubble_outer.pos))
        bubble_outer.bind(size=lambda *a: setattr(self._bubble_rect, "size", bubble_outer.size))

        msg_lbl = Label(
            text=text,
            font_size="15sp",
            color=text_color,
            size_hint=(1, None),
            halign="left",
            valign="top",
        )
        msg_lbl.bind(size=msg_lbl.setter("text_size"))
        msg_lbl.bind(texture_size=lambda *a: setattr(msg_lbl, "height", msg_lbl.texture_size[1] + dp(4)))

        time_lbl = Label(
            text=time,
            font_size="10sp",
            color=(0.8, 0.8, 0.8, 1) if is_mine else (0.6, 0.6, 0.6, 1),
            size_hint=(1, None),
            height=dp(14),
            halign="right" if is_mine else "left",
        )
        time_lbl.bind(size=time_lbl.setter("text_size"))

        bubble_outer.add_widget(msg_lbl)
        bubble_outer.add_widget(time_lbl)

        def update_heights(*a):
            total = msg_lbl.height + time_lbl.height + dp(20)
            bubble_outer.height = total
            wrapper.height = total + dp(8)

        msg_lbl.bind(height=update_heights)

        if is_mine:
            wrapper.add_widget(spacer_before)
            wrapper.add_widget(bubble_outer)
        else:
            wrapper.add_widget(bubble_outer)
            wrapper.add_widget(spacer_after)

        self.ids.chat_messages.add_widget(wrapper)
        self._scroll_bottom()

    def _scroll_bottom(self):
        Clock.schedule_once(lambda dt: setattr(self.ids.chat_scroll, "scroll_y", 0), 0.1)

    def disconnect(self):
        app = App.get_running_app()
        app.ble.disconnect()
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "home"


# ──────────────────────────────────────────────────────────────────────────────
#  App
# ──────────────────────────────────────────────────────────────────────────────

class BlueChatApp(App):
    def build(self):
        self.title = "BlueChat"
        Window.clearcolor = (1, 1, 1, 1)

        self.ble = BLEManager()
        self.contact_book = ContactBook()

        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(ScanScreen(name="scan"))
        sm.add_widget(ChatScreen(name="chat"))
        return sm


if __name__ == "__main__":
    BlueChatApp().run()
