"""
Fleet Task C: Retrieve user context.
To be executed as a parallel /fleet task.
"""

import json
import sys
from src.utils.user_context import UserContextRetriever


def run_task() -> str:
    """
    Execute Fleet Task C: Retrieve user context.
    Returns JSON string with user context data.
    """
    try:
        retriever = UserContextRetriever()
        context = retriever.retrieve_context()
        return json.dumps({
            "success": True,
            "task": "retrieve-user-context",
            "data": context,
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "task": "retrieve-user-context",
            "error": str(e),
        })


if __name__ == "__main__":
    result = run_task()
    print(result)
