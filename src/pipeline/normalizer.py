import re
from typing import Optional

def normalize_for_comparison(val: str) -> str:
    """
    Implements the official AMD evaluator normalization:
    - Converted to uppercase
    - All whitespace removed
    - Characters - . · _ removed
    """
    if not val:
        return ""
    val = val.upper()
    val = re.sub(r'[\s\-\.·_]+', '', val)
    return val

def clean_exact_value(text: str) -> str:
    """
    Prunes filler conversational phrases so the answer is strictly the value.
    E.g., "The release date was October 15, 2024" -> "October 15, 2024"
    """
    if not text:
        return ""
    text = text.strip().strip('"\'')
    # Strip common LLM prefixes
    prefixes = [
        r"^the answer is:?\s*",
        r"^the answer:?\s*",
        r"^answer:?\s*",
        r"^result:?\s*",
        r"^value:?\s*",
        r"^it is:?\s*",
        r"^it was:?\s*",
    ]
    for p in prefixes:
        text = re.sub(p, "", text, flags=re.IGNORECASE).strip()
    return text.strip()
