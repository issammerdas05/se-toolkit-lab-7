#!/usr/bin/env python3
"""
Telegram Bot for LMS - Entry Point

Usage:
    uv run bot.py              # Start Telegram bot
    uv run bot.py --test "/start"  # Test mode (no Telegram connection)
"""

import sys
import os

# Add bot directory to path for imports
bot_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, bot_dir)

import handlers


def main():
    """Main entry point."""
    # Check for test mode
    if len(sys.argv) >= 3 and sys.argv[1] == "--test":
        command = sys.argv[2]
        response = handle_test_command(command)
        print(response)
        sys.exit(0)
    
    # Normal mode - start Telegram bot
    start_telegram_bot()


def handle_test_command(command: str) -> str:
    """
    Handle a command in test mode (no Telegram connection).
    
    Args:
        command: The command string (e.g., "/start", "/help")
    
    Returns:
        Response text to print to stdout
    """
    # Route to appropriate handler
    if command == "/start":
        return handlers.handle_start()
    elif command == "/help":
        return handlers.handle_help()
    elif command == "/health":
        return handlers.handle_health()
    elif command == "/labs":
        return handlers.handle_labs()
    elif command.startswith("/scores"):
        # Extract lab name from command
        parts = command.split(maxsplit=1)
        lab_name = parts[1] if len(parts) > 1 else ""
        return handlers.handle_scores(lab_name)
    else:
        return f"Unknown command: {command}"


def start_telegram_bot():
    """Start the Telegram bot (implemented in Task 2)."""
    print("Starting Telegram bot...")
    print("Bot token:", os.environ.get("BOT_TOKEN", "NOT SET"))
    print("LMS API URL:", os.environ.get("LMS_API_BASE_URL", "NOT SET"))
    print("\nTelegram bot startup will be implemented in Task 2.")
    print("For now, use --test mode to test handlers:")
    print("  uv run bot.py --test '/start'")


if __name__ == "__main__":
    main()
