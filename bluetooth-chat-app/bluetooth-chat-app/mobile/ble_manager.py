"""
ble_manager.py
Bluetooth Low Energy manager for Android using bleak.
Replaces bluetooth_manager.py (PyBluez/RFCOMM) which doesn't work on Android.

Architecture:
  - Server role: advertises a BLE GATT service with a chat characteristic
  - Client role: scans for devices advertising our SERVICE_UUID, connects, subscribes
  - Messages are written to the TX characteristic; received via notifications on RX
"""

import asyncio
import threading
from typing import Callable, List, Optional
from dataclasses import dataclass

try:
    from bleak import BleakScanner, BleakClient, BleakGATTCharacteristic
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False

# Custom 128-bit UUIDs for BlueChat GATT service
SERVICE_UUID   = "12345678-1234-5678-1234-56789abcdef0"
TX_CHAR_UUID   = "12345678-1234-5678-1234-56789abcdef1"  # client writes here
RX_CHAR_UUID   = "12345678-1234-5678-1234-56789abcdef2"  # server notifies here


@dataclass
class BLEDevice:
    address: str
    name: str
    rssi: int = 0

    def __str__(self):
        bars = "▂▄▆█"[min(3, max(0, (self.rssi + 100) // 20))]
        return f"{self.name or 'Unknown'}  {bars}  [{self.address}]"


class BLEManager:
    """Manages BLE scanning, connecting, and bidirectional messaging."""

    def __init__(self):
        self.client: Optional["BleakClient"] = None
        self.connected = False
        self.connected_device: Optional[BLEDevice] = None

        # Callbacks set by the UI
        self.on_message:    Optional[Callable[[str], None]] = None
        self.on_disconnect: Optional[Callable[[], None]]    = None
        self.on_connected:  Optional[Callable[[str], None]] = None

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------ #
    #  Event loop (runs in background thread)
    # ------------------------------------------------------------------ #

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _run(self, coro):
        """Schedule a coroutine on the background loop and return a Future."""
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    # ------------------------------------------------------------------ #
    #  Scanning
    # ------------------------------------------------------------------ #

    def scan(self, duration: float = 8.0, callback: Optional[Callable] = None):
        """
        Scan for BLE devices for `duration` seconds.
        Calls callback(List[BLEDevice]) when done.
        """
        async def _scan():
            devices = await BleakScanner.discover(timeout=duration)
            result = [
                BLEDevice(address=d.address, name=d.name or "Unknown", rssi=d.rssi or 0)
                for d in devices
            ]
            if callback:
                callback(result)
            return result

        self._run(_scan())

    # ------------------------------------------------------------------ #
    #  Connect (client role)
    # ------------------------------------------------------------------ #

    def connect(self, device: BLEDevice, on_done: Optional[Callable[[bool], None]] = None):
        """Connect to a BlueChat BLE server device."""
        async def _connect():
            try:
                client = BleakClient(
                    device.address,
                    disconnected_callback=self._on_ble_disconnect,
                )
                await client.connect()
                await client.start_notify(RX_CHAR_UUID, self._on_notification)
                self.client = client
                self.connected = True
                self.connected_device = device
                if self.on_connected:
                    self.on_connected(device.name or device.address)
                if on_done:
                    on_done(True)
            except Exception as e:
                print(f"[BLE] Connect failed: {e}")
                if on_done:
                    on_done(False)

        self._run(_connect())

    # ------------------------------------------------------------------ #
    #  Send message
    # ------------------------------------------------------------------ #

    def send_message(self, text: str) -> bool:
        """Send a UTF-8 message to the connected device."""
        if not self.connected or not self.client:
            return False

        async def _send():
            try:
                data = f"MSG:{text}".encode("utf-8")
                # BLE MTU is ~20 bytes by default; chunk if needed
                for i in range(0, len(data), 20):
                    await self.client.write_gatt_char(TX_CHAR_UUID, data[i:i+20])
            except Exception as e:
                print(f"[BLE] Send failed: {e}")
                self._on_ble_disconnect(None)

        self._run(_send())
        return True

    # ------------------------------------------------------------------ #
    #  Disconnect
    # ------------------------------------------------------------------ #

    def disconnect(self):
        async def _disc():
            if self.client and self.client.is_connected:
                await self.client.disconnect()
            self.connected = False
            self.client = None

        self._run(_disc())

    # ------------------------------------------------------------------ #
    #  Internal callbacks
    # ------------------------------------------------------------------ #

    def _on_notification(self, char: "BleakGATTCharacteristic", data: bytearray):
        """Called when the server sends a notification (incoming message)."""
        text = data.decode("utf-8", errors="replace")
        if text.startswith("MSG:") and self.on_message:
            self.on_message(text[4:])

    def _on_ble_disconnect(self, client):
        self.connected = False
        self.client = None
        if self.on_disconnect:
            self.on_disconnect()

    # ------------------------------------------------------------------ #
    #  Availability
    # ------------------------------------------------------------------ #

    @staticmethod
    def is_available() -> bool:
        return BLEAK_AVAILABLE
