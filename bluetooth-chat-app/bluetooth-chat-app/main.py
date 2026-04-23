#!/usr/bin/env python3
"""
BlueChat - Bluetooth Communication App
Entry point for the application.
"""

import sys
from src.ui.app import BlueChatApp


def main():
    app = BlueChatApp()
    app.run()


if __name__ == "__main__":
    main()
