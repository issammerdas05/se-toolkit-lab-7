"""
Command Handlers for LMS Telegram Bot

These handlers are pure functions - they take input and return text.
No Telegram dependency - same functions work from --test mode or Telegram.
"""

import httpx
import os
import sys

# Add bot directory to path for imports
bot_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, bot_dir)

from config import load_config

# Load configuration
_config = load_config()

# Backend API configuration
LMS_API_BASE_URL = _config.get("lms_api_base_url", "http://localhost:42002")
LMS_API_KEY = _config.get("lms_api_key", "")


def _get_headers() -> dict:
    """Get headers for API requests."""
    return {"Authorization": f"Bearer {LMS_API_KEY}"}


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
        Backend health status
    """
    try:
        # Check if backend is accessible
        response = httpx.get(f"{LMS_API_BASE_URL}/docs", headers=_get_headers(), timeout=5.0)
        if response.status_code == 200:
            # Get item count to show backend has data
            items_response = httpx.get(f"{LMS_API_BASE_URL}/items/", headers=_get_headers(), timeout=5.0)
            if items_response.status_code == 200:
                items = items_response.json()
                item_count = len(items)
                return f"🟢 Backend status: OK\n📊 Total items: {item_count}"
            return "🟢 Backend status: OK (but couldn't fetch items)"
        return f"🔴 Backend status: Error (HTTP {response.status_code})"
    except httpx.ConnectError:
        return "🔴 Backend status: Connection failed - is the backend running?"
    except Exception as e:
        return f"🔴 Backend status: Error - {str(e)}"


def handle_labs() -> str:
    """
    Handle /labs command.
    
    Returns:
        List of available labs from backend
    """
    try:
        response = httpx.get(f"{LMS_API_BASE_URL}/items/", headers=_get_headers(), timeout=10.0)
        if response.status_code != 200:
            return f"❌ Failed to fetch labs (HTTP {response.status_code})"
        
        items = response.json()
        # Filter only labs (type == "lab")
        labs = [item for item in items if item.get("type") == "lab"]
        
        if not labs:
            return "📋 No labs found"
        
        result = "📋 Available Labs:\n\n"
        for lab in labs:
            result += f"• {lab.get('title', 'Unknown')}\n"
        
        return result
    except httpx.ConnectError:
        return "❌ Cannot connect to backend - is it running?"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def handle_scores(lab_name: str) -> str:
    """
    Handle /scores command.
    
    Args:
        lab_name: Name of the lab to get scores for
    
    Returns:
        Scores information from backend
    """
    if not lab_name:
        return "Please specify a lab name. Example: /scores lab-04"
    
    try:
        # Call the analytics pass-rates endpoint
        response = httpx.get(
            f"{LMS_API_BASE_URL}/analytics/pass-rates",
            headers=_get_headers(),
            params={"lab": lab_name},
            timeout=10.0
        )
        
        if response.status_code != 200:
            return f"❌ Failed to fetch scores (HTTP {response.status_code})"
        
        pass_rates = response.json()
        
        if not pass_rates:
            return f"📊 No data found for {lab_name}"
        
        result = f"📊 Scores for {lab_name}:\n\n"
        for task in pass_rates:
            task_name = task.get("task", "Unknown")
            avg_score = task.get("avg_score", 0)
            attempts = task.get("attempts", 0)
            result += f"• {task_name}\n  Avg: {avg_score}% | Attempts: {attempts}\n"
        
        return result
    except httpx.ConnectError:
        return "❌ Cannot connect to backend - is it running?"
    except Exception as e:
        return f"❌ Error: {str(e)}"
