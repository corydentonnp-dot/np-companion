"""
CareCompanion — JSON Helpers

Shared utility for safe JSON parsing.
Extracted from routes/intelligence.py (Band 3 B1.19).
"""

import json


def parse_json_safe(text):
    """Parse a JSON string; return empty list on failure."""
    if not text:
        return []
    try:
        result = json.loads(text)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
