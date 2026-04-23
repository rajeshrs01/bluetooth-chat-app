[app]

# ── App identity ─────────────────────────────────────────────────
title           = BlueChat
package.name    = bluechat
package.domain  = com.yourname
version         = 1.2.0

# ── Source ───────────────────────────────────────────────────────
source.dir      = .
source.include_exts = py,kv,png,jpg,ttf,json,db
source.exclude_dirs = tests, .git, .vscode, venv, __pycache__, docs

# Entry point
entrypoint = main_mobile.py

# ── Python dependencies ──────────────────────────────────────────
requirements =
    python3==3.11.6,
    kivy==2.2.1,
    bleak==0.21.1,
    cryptography==42.0.0,
    sqlite3

# ── Android specifics ────────────────────────────────────────────
android.minapi          = 26
android.api             = 33
android.ndk             = 25b
android.archs           = arm64-v8a, armeabi-v7a

# Bluetooth permissions (required for BLE on Android 12+)
android.permissions =
    BLUETOOTH,
    BLUETOOTH_ADMIN,
    BLUETOOTH_SCAN,
    BLUETOOTH_CONNECT,
    BLUETOOTH_ADVERTISE,
    ACCESS_FINE_LOCATION,
    ACCESS_COARSE_LOCATION,
    INTERNET

# BLE feature declaration
android.features        = android.hardware.bluetooth_le

# ── Presplash & icon ─────────────────────────────────────────────
# Uncomment and add your image files:
# presplash.filename    = %(source.dir)s/mobile/assets/splash.png
# icon.filename         = %(source.dir)s/mobile/assets/icon.png

# ── Orientation ──────────────────────────────────────────────────
orientation             = portrait

# ── Build output ─────────────────────────────────────────────────
android.debug           = 1

# ── Logging ──────────────────────────────────────────────────────
log_level               = 2
warn_on_root            = 1

[buildozer]
# Directory for Buildozer's cache (NDK, SDK downloads)
build_dir               = .buildozer
bin_dir                 = ./bin
