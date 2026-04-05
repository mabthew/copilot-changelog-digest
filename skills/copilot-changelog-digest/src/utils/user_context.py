"""
User context retriever: fetch user session data from /chronicle API.
Retrieves development patterns, recent focus areas, workflow hints.
"""

import json
import subprocess
import os
from typing import Dict, Optional


class UserContextRetriever:
    """Retrieve user session data and context."""

    def __init__(self):
        """Initialize retriever."""
        pass

    def retrieve_context(self) -> Dict:
        """
        Fetch user context via /chronicle command or API.
        Returns dict with: {patterns, focus_areas, recent_tips, workflow_hints}
        """
        # Try /chronicle command first
        context = self._try_chronicle_command()

        # Fallback: empty context if /chronicle unavailable
        if not context:
            context = self._fallback_context()

        return context

    def _try_chronicle_command(self) -> Optional[Dict]:
        """Try to fetch context via 'copilot /chronicle' command."""
        try:
            result = subprocess.run(
                ["copilot", "/chronicle"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and result.stdout.strip():
                # Try to parse as JSON
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    # If not JSON, create structured object from text
                    return {
                        "patterns": [],
                        "focus_areas": [],
                        "recent_tips": [result.stdout.strip()],
                        "workflow_hints": [],
                    }
        except Exception:
            pass

        return None

    def _fallback_context(self) -> Dict:
        """Fallback context when /chronicle unavailable."""
        return {
            "patterns": [],
            "focus_areas": [],
            "recent_tips": [],
            "workflow_hints": [
                "Copilot /chronicle not available; using repo-only context"
            ],
            "note": "User context unavailable; analysis based on repo tech stack only",
        }

    def to_json(self, context: Dict) -> str:
        """Convert context to JSON string."""
        return json.dumps(context, indent=2)


if __name__ == "__main__":
    retriever = UserContextRetriever()
    context = retriever.retrieve_context()
    print(retriever.to_json(context))
