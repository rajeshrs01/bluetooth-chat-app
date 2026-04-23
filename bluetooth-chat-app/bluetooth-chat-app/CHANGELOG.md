# Changelog

All notable changes to BlueChat are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.2.0] — 2026-04-18

### Added
- Sound + desktop notifications for messages, calls, and file transfers
- Git Flow branching strategy + CONTRIBUTING.md
- PR template, issue templates, CODEOWNERS
- Multi-version CI matrix (Python 3.9 – 3.12)

### Fixed
- Recv thread crash on abrupt remote disconnect (v1.1.1 hotfix included)

## [1.3.0] — 2026-04-23

### Added
- Android APK via Kivy + BLE (bleak) — full mobile app
- GitHub Actions: auto-build APK on every push to develop/main
- GitHub Actions: auto-release signed APK on version tags
- scripts/setup_keystore.sh — keystore generation helper

## [Unreleased] — develop

### Planned
- Group chat (multi-client)
- iOS support via CoreBluetooth

---

## [1.1.0] — 2026-04-18

### Added
- End-to-end encryption (RSA-2048 key exchange + Fernet AES-128)
- File transfer over Bluetooth RFCOMM with progress tracking
- Contacts / address book backed by SQLite
- Automatic contact saving when messages arrive

### Changed
- CI now runs on Python 3.9, 3.10, 3.11, and 3.12
- requirements.txt updated with `cryptography` and `pytest-mock`

---

## [1.0.0] — 2026-04-18

### Added
- Bluetooth device discovery and RFCOMM connection
- Real-time two-way text messaging
- Voice call streaming with PyAudio
- Terminal UI using Python curses
- In-memory + JSON-backed chat history
- GitHub Actions CI workflow
