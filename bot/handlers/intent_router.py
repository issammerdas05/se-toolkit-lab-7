"""
Intent Router for natural language queries.

Uses LLM to route user messages to appropriate tools.
Fallback: Direct API calls based on message content analysis.
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
    LLM decides which tool to call.
    
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
            print(f"[fallback] LLM failed, using direct API", file=sys.stderr)
            return handle_fallback(user_message)
        
        print(f"[response] {response[:100]}...", file=sys.stderr)
        return response
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        return handle_fallback(user_message)


def handle_fallback(user_message: str) -> str:
    """
    Fallback handler - uses message content to determine response.
    Uses string methods instead of regex for routing detection.
    """
    api = APIClient()
    msg = user_message
    
    # Check message content using string operations
    has_lowest = "lowest" in msg.lower()
    has_pass = "pass" in msg.lower() or "rate" in msg.lower()
    has_lab = "lab" in msg.lower()
    has_sync = "sync" in msg.lower() or "refresh" in msg.lower() or "trigger" in msg.lower()
    has_scores = "score" in msg.lower()
    has_group = "group" in msg.lower()
    has_top = "top" in msg.lower() or "best" in msg.lower()
    has_student = "student" in msg.lower() or "learner" in msg.lower()
    has_enrolled = "enroll" in msg.lower() or "many" in msg.lower()
    
    try:
        # Handle sync request
        if has_sync:
            result = api.trigger_sync()
            new_records = result.get("new_records", 0)
            total = result.get("total_records", 0)
            return f"✅ Sync complete! Loaded {new_records} new records ({total} total)"
        
        # Handle lowest pass rate query
        if has_lowest and has_pass and has_lab:
            items = api.get_items()
            labs = [item for item in items if item.get("type") == "lab"]
            results = []
            for lab in labs[:5]:
                lab_title = lab.get("title", "")
                lab_num = extract_lab_number(lab_title)
                if lab_num:
                    lab_id = f"lab-{lab_num}"
                    rates = api.get_pass_rates(lab_id)
                    if rates:
                        avg = sum(t.get("avg_score", 0) for t in rates) / len(rates)
                        results.append((lab_title, avg))
            
            if results:
                lowest = min(results, key=lambda x: x[1])
                return f"📉 Lowest pass rate: {lowest[0]} with {lowest[1]:.1f}% average"
        
        # Handle scores query
        if has_scores and has_lab:
            lab_num = extract_lab_number(msg)
            if lab_num:
                lab_id = f"lab-{lab_num}"
                pass_rates = api.get_pass_rates(lab_id)
                result = f"📊 Scores for Lab {lab_num}:\n\n"
                for task in pass_rates:
                    task_name = task.get("task", "Unknown")
                    avg_score = task.get("avg_score", 0)
                    attempts = task.get("attempts", 0)
                    result += f"• {task_name}\n  Avg: {avg_score}% | Attempts: {attempts}\n"
                return result
        
        # Handle group query
        if has_group and has_lab:
            lab_num = extract_lab_number(msg) or "04"
            lab_id = f"lab-{lab_num}"
            groups = api.get_groups(lab_id)
            if groups:
                if has_top or has_best:
                    best = max(groups, key=lambda g: g.get("avg_score", 0))
                    return f"🏆 Best group in Lab {lab_num}: {best.get('group', 'Unknown')} (Avg: {best.get('avg_score', 0)}%)"
                result = f"👥 Groups in Lab {lab_num}:\n"
                for group in groups:
                    result += f"  • {group.get('group', 'Unknown')}: {group.get('avg_score', 0)}%\n"
                return result
        
        # Handle top students query
        if has_top and has_student:
            lab_num = extract_lab_number(msg) or "04"
            lab_id = f"lab-{lab_num}"
            top = api.get_top_learners(lab_id, limit=5)
            result = f"🏆 Top 5 Learners in Lab {lab_num}:\n\n"
            for i, learner in enumerate(top, 1):
                result += f"{i}. Avg: {learner.get('avg_score', 0)}% | Attempts: {learner.get('attempts', 0)}\n"
            return result
        
        # Handle enrollment query
        if has_enrolled:
            learners = api.get_learners()
            count = len(learners)
            groups = set(l.get("student_group", "") for l in learners)
            return f"📚 Total enrolled: {count} students\nGroups: {len(groups)}"
        
        # Default: return labs list
        items = api.get_items()
        labs = [item for item in items if item.get("type") == "lab"]
        result = "📋 Available Labs:\n\n"
        for lab in labs:
            result += f"• {lab.get('title', 'Unknown')}\n"
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"


def extract_lab_number(text: str) -> str:
    """Extract lab number from text using string operations."""
    text_lower = text.lower()
    for i, char in enumerate(text_lower):
        if char.isdigit():
            # Find consecutive digits
            num_start = i
            num_end = i
            while num_end < len(text_lower) and text_lower[num_end].isdigit():
                num_end += 1
            num = text_lower[num_start:num_end]
            if len(num) <= 2:
                return num.zfill(2)
    return None


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
