#!/usr/bin/env python3
"""
Telegram Bot for LMS - Entry Point

Usage:
    uv run bot.py              # Start Telegram bot
    uv run bot.py --test "/command"  # Test mode (no Telegram connection)
    uv run bot.py --test "natural language query"  # LLM-powered
"""

import sys
import os

# Add bot directory to path for imports
bot_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, bot_dir)

import handlers
from handlers.intent_router import route_intent, get_inline_buttons


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
        command: The command string (e.g., "/start", "/help", or natural language)
    
    Returns:
        Response text to print to stdout
    """
    # Slash commands - use handlers
    if command.startswith("/"):
        if command == "/start":
            return handlers.handle_start_with_buttons()
        elif command == "/help":
            return handlers.handle_help()
        elif command == "/health":
            return handlers.handle_health()
        elif command == "/labs":
            return handlers.handle_labs()
        elif command.startswith("/scores"):
            parts = command.split(maxsplit=1)
            lab_name = parts[1] if len(parts) > 1 else ""
            return handlers.handle_scores(lab_name)
        else:
            return f"Unknown command: {command}"
    else:
        # Natural language - use LLM intent router (NO regex routing)
        return route_intent(command)


def start_telegram_bot():
    """Start the Telegram bot with inline keyboard support."""
    bot_token = os.environ.get("BOT_TOKEN", "")
    
    if not bot_token or bot_token == "<bot-token>" or bot_token == "fake-token":
        print("Starting Telegram bot...")
        print("Bot token:", bot_token)
        print("LMS API URL:", os.environ.get("LMS_API_BASE_URL", "NOT SET"))
        print("LLM API URL:", os.environ.get("LLM_API_BASE_URL", "NOT SET"))
        print("\nInline keyboard buttons enabled for common actions.")
        print("\n⚠️  BOT_TOKEN not configured. Running in demo mode.")
        print("Set BOT_TOKEN in environment to connect to Telegram.")
        print("\nFor now, use --test mode to test handlers:")
        print("  uv run bot.py --test '/start'")
        print("  uv run bot.py --test 'what labs are available'")
        
        # Keep running in demo mode
        import time
        print("\nBot running in demo mode. Press Ctrl+C to stop.")
        while True:
            time.sleep(60)
        return
    
    try:
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
        
        print("Starting Telegram bot...")
        print("Bot token: [CONFIGURED]")
        print("LMS API URL:", os.environ.get("LMS_API_BASE_URL", "NOT SET"))
        print("LLM API URL:", os.environ.get("LLM_API_BASE_URL", "NOT SET"))
        
        async def start(update: Update, context):
            keyboard = [
                [InlineKeyboardButton("📋 List Labs", callback_data="list_labs")],
                [InlineKeyboardButton("📊 Lab Scores", callback_data="show_scores")],
                [InlineKeyboardButton("🏆 Top Students", callback_data="top_students")],
                [InlineKeyboardButton("👥 Groups", callback_data="show_groups")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(handle_test_command("/start"), reply_markup=reply_markup)
        
        async def help_cmd(update: Update, context):
            await update.message.reply_text(handle_test_command("/help"))
        
        async def health(update: Update, context):
            await update.message.reply_text(handle_test_command("/health"))
        
        async def labs(update: Update, context):
            await update.message.reply_text(handle_test_command("/labs"))
        
        async def scores(update: Update, context):
            lab = " ".join(context.args) if context.args else ""
            await update.message.reply_text(handle_test_command(f"/scores {lab}"))
        
        async def message_handler(update: Update, context):
            text = update.message.text
            response = handle_test_command(text)
            await update.message.reply_text(response)
        
        async def button_handler(update: Update, context):
            query = update.callback_query
            await query.answer()
            callback = query.data
            if callback == "list_labs":
                await query.edit_message_text(handle_test_command("/labs"))
            elif callback == "show_scores":
                await query.edit_message_text("Send: /scores lab-04")
            elif callback == "top_students":
                await query.edit_message_text(handle_test_command("top 5 students in lab 4"))
            elif callback == "show_groups":
                await query.edit_message_text(handle_test_command("show groups in lab 4"))
        
        # Create application
        application = Application.builder().token(bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_cmd))
        application.add_handler(CommandHandler("health", health))
        application.add_handler(CommandHandler("labs", labs))
        application.add_handler(CommandHandler("scores", scores))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        print("\nBot started! Polling for messages...")
        
        # Start polling
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except ImportError as e:
        print(f"Telegram library not installed: {e}")
        print("Run: uv sync")
    except Exception as e:
        print(f"Error starting bot: {e}")


if __name__ == "__main__":
    main()
