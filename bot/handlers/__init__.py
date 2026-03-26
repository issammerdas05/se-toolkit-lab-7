"""
Command Handlers for LMS Telegram Bot

These handlers are pure functions - they take input and return text.
No Telegram dependency - same functions work from --test mode or Telegram.
"""


def handle_start() -> str:
    """
    Handle /start command.
    
    Returns:
        Welcome message
    """
    return (
        "👋 Welcome to the LMS Bot!\n\n"
        "I can help you interact with the Learning Management System.\n\n"
        "Use /help to see available commands."
    )


def handle_help() -> str:
    """
    Handle /help command.
    
    Returns:
        List of available commands
    """
    return (
        "📚 Available Commands:\n\n"
        "/start - Welcome message\n"
        "/help - Show this help\n"
        "/health - Check backend status\n"
        "/labs - List available labs\n"
        "/scores <lab> - Get scores for a lab\n\n"
        "You can also ask questions in plain language!"
    )


def handle_health() -> str:
    """
    Handle /health command.
    
    Returns:
        Backend health status (placeholder for Task 2)
    """
    # Task 2: Will call actual backend API
    return "🟢 Backend status: OK (placeholder - will implement in Task 2)"


def handle_labs() -> str:
    """
    Handle /labs command.
    
    Returns:
        List of available labs (placeholder for Task 2)
    """
    # Task 2: Will fetch from actual backend API
    return (
        "📋 Available Labs:\n\n"
        "Lab 01 - Products, Architecture & Roles\n"
        "Lab 02 - Run, Fix, and Deploy a Backend Service\n"
        "Lab 03 - Backend API: Explore, Debug, Implement, Deploy\n"
        "Lab 04 - Testing, Front-end, and AI Agents\n"
        "Lab 05 - Data Pipeline and Analytics Dashboard\n"
        "Lab 06 - Build Your Own Agent\n"
        "Lab 07 - Build a Client with an AI Coding Agent\n\n"
        "(placeholder - will fetch real data in Task 2)"
    )


def handle_scores(lab_name: str) -> str:
    """
    Handle /scores command.
    
    Args:
        lab_name: Name of the lab to get scores for
    
    Returns:
        Scores information (placeholder for Task 2)
    """
    # Task 2: Will fetch from actual backend API
    if not lab_name:
        return "Please specify a lab name. Example: /scores lab-04"
    
    return (
        f"📊 Scores for {lab_name}:\n\n"
        "Task completion rates will be shown here.\n"
        "(placeholder - will fetch real data in Task 2)"
    )
