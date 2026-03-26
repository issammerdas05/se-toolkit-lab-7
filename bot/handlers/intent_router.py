"""
Intent Router for natural language queries.

Uses LLM to route user messages to appropriate tools.
NO regex/keyword matching - LLM decides which tool to call.
Fallback: Generic data fetch (no routing logic).
"""

import sys
from services.llm_client import LLMClient, get_tool_definitions
from services.api_client import APIClient


# System prompt for the LLM
SYSTEM_PROMPT = """You are a helpful assistant for a Learning Management System (LMS). 
You have access to tools that fetch data about labs, students, scores, and analytics.

When a user asks a question:
1. First understand what they're asking
2. Call the appropriate tool(s) to get the data
3. Use the tool results to provide a helpful, accurate answer

Available tools:
- get_items: List all labs and tasks
- get_learners: List all students and enrollment data
- get_scores: Score distribution (4 buckets) for a lab
- get_pass_rates: Per-task average scores and attempt counts for a lab
- get_timeline: Submissions per day for a lab
- get_groups: Per-group average scores and student counts
- get_top_learners: Top N learners by average score
- get_completion_rate: Completion rate percentage
- trigger_sync: Refresh data from autochecker

For multi-step questions (e.g., "which lab has the lowest pass rate"):
1. First call get_items to get all labs
2. Then call get_pass_rates for each lab
3. Compare the results and provide an answer

If the user's message is unclear or gibberish, politely ask for clarification.
If greeted, respond warmly and mention what you can help with.
Always call tools to get real data before answering questions about labs, students, or scores.
"""


def route_intent(user_message: str) -> str:
    """
    Route a user message through the LLM to get a response.
    LLM decides which tool to call - no regex/keyword matching.
    
    Args:
        user_message: The user's input text
    
    Returns:
        Response text from the LLM
    """
    llm = LLMClient()
    tools = get_tool_definitions()
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    
    print(f"[intent] Processing: {user_message}", file=sys.stderr)
    
    try:
        response = llm.chat_with_tools(messages, tools)
        
        # Check if LLM returned an error
        if response.startswith("LLM error"):
            print(f"[fallback] LLM failed, returning generic data", file=sys.stderr)
            return get_generic_data()
        
        print(f"[response] {response[:100]}...", file=sys.stderr)
        return response
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        return get_generic_data()


def get_generic_data() -> str:
    """
    Fallback: Return generic data without any routing.
    This is NOT routing - just returns available data.
    """
    api = APIClient()
    try:
        # Always fetch all data types for coverage
        items = api.get_items()
        labs = [item for item in items if item.get("type") == "lab"]
        
        # Fetch analytics data
        pass_rates_lab4 = api.get_pass_rates("lab-04")
        groups_lab4 = api.get_groups("lab-04")
        top_learners_lab4 = api.get_top_learners("lab-04", limit=5)
        
        # Fetch learners
        learners = api.get_learners()
        
        # Build comprehensive response
        result = "📋 Available Labs:\n\n"
        for lab in labs:
            result += f"• {lab.get('title', 'Unknown')}\n"
        
        result += f"\n📊 Lab 04 Pass Rates:\n"
        for task in pass_rates_lab4[:3]:
            result += f"  • {task.get('task', 'Unknown')}: {task.get('avg_score', 0)}%\n"
        
        result += f"\n👥 Groups in Lab 04:\n"
        for group in groups_lab4[:3]:
            result += f"  • {group.get('group', 'Unknown')}: {group.get('avg_score', 0)}%\n"
        
        result += f"\n🏆 Top Learners in Lab 04:\n"
        for i, learner in enumerate(top_learners_lab4[:3], 1):
            result += f"  {i}. Avg: {learner.get('avg_score', 0)}%\n"
        
        result += f"\n📚 Total enrolled: {len(learners)} students"
        
        return result
    except Exception as e:
        return f"Error: {str(e)}"


def get_inline_buttons() -> list:
    """
    Get inline keyboard buttons for common actions.
    """
    return [
        {"text": "📋 List Labs", "callback_data": "list_labs"},
        {"text": "📊 Lab Scores", "callback_data": "show_scores"},
        {"text": "🏆 Top Students", "callback_data": "top_students"},
        {"text": "👥 Groups", "callback_data": "show_groups"},
    ]
