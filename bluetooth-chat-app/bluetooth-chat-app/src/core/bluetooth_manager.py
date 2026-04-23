"""
bluetooth_manager.py
Handles Bluetooth device discovery, pairing, and connection management.
"""

import bluetooth
import threading
from dataclasses import dataclass
from typing import Optional, Callable, List


SERVICE_UUID = "94f39d29-7d6d-437d-973b-fba39e49d4ef"
SERVICE_NAME = "BlueChatService"


@dataclass
class BluetoothDevice:
    address: str
    name: str

    def __str__(self):
        return f"{self.name} [{self.address}]"


class BluetoothManager:
    """Manages Bluetooth connections, discovery, and socket handling."""

    def __init__(self):
        self.socket: Optional[bluetooth.BluetoothSocket] = None
        self.server_socket: Optional[bluetooth.BluetoothSocket] = None
        self.connected = False
        self._recv_thread: Optional[threading.Thread] = None
        self.on_message: Optional[Callable[[str], None]] = None
        self.on_disconnect: Optional[Callable[[], None]] = None

    # ------------------------------------------------------------------ #
    #  Discovery
    # ------------------------------------------------------------------ #

    def scan_devices(self, duration: int = 8) -> List[BluetoothDevice]:
        """Scan for nearby Bluetooth devices. Blocks for `duration` seconds."""
        try:
            raw = bluetooth.discover_devices(
                duration=duration,
                lookup_names=True,
                flush_cache=True
            )
            return [BluetoothDevice(addr, name or "Unknown") for addr, name in raw]
        except Exception as e:
            raise RuntimeError(f"Scan failed: {e}") from e

    # ------------------------------------------------------------------ #
    #  Server (host / listen)
    # ------------------------------------------------------------------ #

    def start_server(self, on_client_connected: Callable) -> int:
        """
        Start an RFCOMM server and wait for one client.
        Calls `on_client_connected(address)` when a client joins.
        Returns the RFCOMM channel number.
        """
        self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_socket.bind(("", bluetooth.PORT_ANY))
        self.server_socket.listen(1)
        port = self.server_socket.getsockname()[1]

        bluetooth.advertise_service(
            self.server_socket,
            SERVICE_NAME,
            service_id=SERVICE_UUID,
            service_classes=[SERVICE_UUID, bluetooth.SERIAL_PORT_CLASS],
            profiles=[bluetooth.SERIAL_PORT_PROFILE],
        )

        def _accept():
            try:
                client_sock, client_info = self.server_socket.accept()
                self.socket = client_sock
                self.connected = True
                on_client_connected(client_info[0])
                self._start_receiver()
            except Exception:
                pass  # server was closed

        threading.Thread(target=_accept, daemon=True).start()
        return port

    def stop_server(self):
        """Stop advertising and close the server socket."""
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None

    # ------------------------------------------------------------------ #
    #  Client (connect to host)
    # ------------------------------------------------------------------ #

    def connect(self, device: BluetoothDevice) -> bool:
        """Connect to a device running BlueChatService. Returns True on success."""
        try:
            services = bluetooth.find_service(
                uuid=SERVICE_UUID, address=device.address
            )
            if not services:
                return False

            port = services[0]["port"]
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((device.address, port))
            self.socket = sock
            self.connected = True
            self._start_receiver()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    #  Messaging
    # ------------------------------------------------------------------ #

    def send_message(self, text: str) -> bool:
        """Send a UTF-8 encoded text message. Returns True on success."""
        if not self.connected or not self.socket:
            return False
        try:
            prefix = "MSG:"
            self.socket.send((prefix + text).encode("utf-8"))
            return True
        except Exception:
            self._handle_disconnect()
            return False

    def _start_receiver(self):
        """Start background thread to receive incoming data."""
        self._recv_thread = threading.Thread(
            target=self._recv_loop, daemon=True
        )
        self._recv_thread.start()

    def _recv_loop(self):
        while self.connected and self.socket:
            try:
                raw = self.socket.recv(4096)
                if not raw:
                    break
                text = raw.decode("utf-8", errors="replace")

                if text.startswith("MSG:") and self.on_message:
                    self.on_message(text[4:])
            except Exception:
                break
        self._handle_disconnect()

    def _handle_disconnect(self):
        self.connected = False
        if self.on_disconnect:
            self.on_disconnect()

    # ------------------------------------------------------------------ #
    #  Cleanup
    # ------------------------------------------------------------------ #

    def disconnect(self):
        """Close the active connection cleanly."""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
        self.stop_server()


    def is_connected(self) -> bool:
        """Safe connection state check (thread-safe)."""
        return bool(self.connected and self.socket)
