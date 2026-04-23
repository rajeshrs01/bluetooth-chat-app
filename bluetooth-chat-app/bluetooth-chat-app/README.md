# 📡 BlueChat — Bluetooth Chat & Voice App

A terminal-based **Bluetooth communication app** written in Python.  
Supports real-time **text messaging** and **voice calls** between two devices over RFCOMM Bluetooth.

---

## ✨ Features

- 🔍 **Device Discovery** — Scan for nearby Bluetooth devices
- 💬 **Text Messaging** — Real-time two-way chat
- 📞 **Voice Calls** — Stream audio bidirectionally using your mic and speakers
- 📜 **Chat History** — Save and load conversations
- 🖥️ **Terminal UI** — Clean curses-based interface, no browser needed

---

## 📋 Requirements

- Python 3.8+
- Linux (recommended) — PyBluez works best on Linux
- Bluetooth adapter
- Two devices that are **paired at OS level** before running

### Install system dependencies (Linux)

```bash
sudo apt-get update
sudo apt-get install bluetooth libbluetooth-dev portaudio19-dev
```

### Install Python dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Quick Start

### Device A — Host a session

```bash
python main.py
# Select: [1] Host a session
```

### Device B — Join the session

```bash
python main.py
# Select: [2] Join a session
# Scan will find Device A → select it
```

---

## 💬 Chat Commands

| Command    | Action                          |
|------------|---------------------------------|
| Type + Enter | Send a message               |
| `/call`    | Start a voice call              |
| `/hangup`  | End the voice call              |
| `/quit`    | Disconnect and exit             |

---

## 🗂️ Project Structure

```
bluetooth-chat-app/
├── main.py                      # Entry point
├── requirements.txt
├── setup.py
├── src/
│   ├── core/
│   │   ├── bluetooth_manager.py # BT discovery, connect, send/receive
│   │   ├── audio_manager.py     # Voice call streaming (PyAudio)
│   │   └── chat_store.py        # Message history (in-memory + JSON)
│   └── ui/
│       └── app.py               # Curses terminal UI
└── tests/
    └── test_chat_store.py       # Unit tests (pytest)
```

---

## 🧪 Running Tests

```bash
pytest tests/
```

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| `bluetooth module not found` | `pip install PyBluez` + install system deps |
| `No devices found` | Make sure both devices are discoverable and paired |
| `Connection failed` | Ensure Device A has run main.py first (server must be up) |
| `PyAudio not installed` | `pip install pyaudio` — voice calls won't work without it |
| Works on macOS? | Partially — PyBluez is unreliable on macOS; try `bleak` instead |

---

## 📦 How It Works

```
Device A (Host)                        Device B (Client)
─────────────────────────────────────────────────────────
BluetoothSocket (RFCOMM)   ◄──────►   BluetoothSocket
advertise_service()                    find_service()
                                       connect()

Text: send "MSG:<text>"    ◄──────►   recv → strip prefix → display
Audio: send "AUD:<pcm>"    ◄──────►   recv → strip prefix → play
```

---

## 🛣️ Roadmap

- [ ] File transfer
- [ ] Group chat (multiple clients)
- [ ] GUI version (Tkinter or PyQt)
- [ ] BLE (Bluetooth Low Energy) support via `bleak`
- [ ] End-to-end encryption

---

## 📄 License

MIT License — free to use and modify.
