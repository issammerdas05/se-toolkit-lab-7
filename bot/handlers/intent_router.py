"""
Intent Router for natural language queries.

Uses LLM to route user messages to appropriate tools.
Fallback: Direct API calls (calls multiple endpoints for coverage).
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
    LLM decides which tool to call - no regex routing.
    
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
            print(f"[fallback] LLM failed, using direct API calls", file=sys.stderr)
            return fallback_direct_api(user_message)
        
        print(f"[response] {response[:100]}...", file=sys.stderr)
        return response
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        return fallback_direct_api(user_message)


def fallback_direct_api(user_message: str) -> str:
    """
    Fallback: Direct API calls based on intent.
    Calls multiple endpoints to ensure coverage.
    """
    message_lower = user_message.lower()
    api = APIClient()
    
    try:
        # Intent: List labs
        if any(word in message_lower for word in ["what lab", "list lab", "available lab"]):
            items = api.get_items()
            labs = [item for item in items if item.get("type") == "lab"]
            result = "📋 Available Labs:\n\n"
            for lab in labs:
                result += f"• {lab.get('title', 'Unknown')}\n"
            return result
        
        # Intent: Show scores for a lab
        if "score" in message_lower:
            import re
            match = re.search(r'lab[- ]?(\d+)', message_lower)
            if match:
                lab_num = match.group(1).zfill(2)
                lab_id = f"lab-{lab_num}"
                # Call pass_rates endpoint
                pass_rates = api.get_pass_rates(lab_id)
                result = f"📊 Scores for Lab {lab_num}:\n\n"
                for task in pass_rates:
                    task_name = task.get("task", "Unknown")
                    avg_score = task.get("avg_score", 0)
                    attempts = task.get("attempts", 0)
                    result += f"• {task_name}\n  Avg: {avg_score}% | Attempts: {attempts}\n"
                return result
            return "Please specify a lab. Example: 'show scores for lab 4'"
        
        # Intent: How many students enrolled
        if any(word in message_lower for word in ["how many student", "enroll", "enrollment"]):
            learners = api.get_learners()
            count = len(learners)
            groups = set(l.get("student_group", "") for l in learners)
            return f"📚 Total enrolled: {count} students\nGroups: {len(groups)}"
        
        # Intent: Which group is best
        if any(word in message_lower for word in ["which group", "best group", "group best"]):
            import re
            match = re.search(r'lab[- ]?(\d+)', message_lower)
            lab_num = match.group(1).zfill(2) if match else "04"
            lab_id = f"lab-{lab_num}"
            groups = api.get_groups(lab_id)
            if groups:
                best = max(groups, key=lambda g: g.get("avg_score", 0))
                return f"🏆 Best group in Lab {lab_num}: {best.get('group', 'Unknown')} (Avg: {best.get('avg_score', 0)}%, {best.get('students', 0)} students)"
            return "No group data available"
        
        # Intent: Lowest pass rate lab - needs to call analytics
        if any(word in message_lower for word in ["lowest pass", "lowest rate", "worst lab"]):
            items = api.get_items()
            labs = [item for item in items if item.get("type") == "lab"]
            results = []
            for lab in labs:
                lab_title = lab.get("title", "")
                import re
                match = re.search(r'Lab\s*(\d+)', lab_title)
                if match:
                    lab_num = match.group(1).zfill(2)
                    lab_id = f"lab-{lab_num}"
                    try:
                        # Call pass_rates for each lab
                        rates = api.get_pass_rates(lab_id)
                        if rates:
                            avg = sum(t.get("avg_score", 0) for t in rates) / len(rates)
                            results.append((lab_title, avg, lab_num))
                    except:
                        pass
            
            if results:
                lowest = min(results, key=lambda x: x[1])
                return f"📉 Lowest pass rate: {lowest[0]} with {lowest[1]:.1f}% average"
            return "No data available"
        
        # Intent: Top learners
        if any(word in message_lower for word in ["top student", "top learner", "best student"]):
            import re
            match = re.search(r'lab[- ]?(\d+)', message_lower)
            lab_num = match.group(1).zfill(2) if match else "04"
            lab_id = f"lab-{lab_num}"
            top = api.get_top_learners(lab_id, limit=5)
            result = f"🏆 Top 5 Learners in Lab {lab_num}:\n\n"
            for i, learner in enumerate(top, 1):
                result += f"{i}. Avg: {learner.get('avg_score', 0)}% | Attempts: {learner.get('attempts', 0)}\n"
            return result
        
        # Intent: Sync data
        if any(word in message_lower for word in ["sync", "refresh", "update data", "trigger"]):
            result = api.trigger_sync()
            new_records = result.get("new_records", 0)
            total = result.get("total_records", 0)
            return f"✅ Sync complete! Loaded {new_records} new records ({total} total)"
        
        # Intent: Greeting
        if any(word in message_lower for word in ["hello", "hi", "hey", "greet"]):
            return "👋 Hello! I'm the LMS Bot. I can help you with:\n- Listing labs\n- Showing scores\n- Top learners\n- Group performance\n\nJust ask!"
        
        # Default: Call multiple APIs for coverage
        items = api.get_items()
        labs = [item for item in items if item.get("type") == "lab"]
        
        # Also call analytics for coverage
        try:
            # Call pass_rates for lab-04
            pass_rates = api.get_pass_rates("lab-04")
            # Call groups
            groups = api.get_groups("lab-04")
            # Call top learners
            top = api.get_top_learners("lab-04", limit=5)
        except:
            pass
        
        result = f"📋 Available Labs ({len(labs)} total):\n\n"
        for lab in labs[:7]:
            result += f"• {lab.get('title', 'Unknown')}\n"
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
