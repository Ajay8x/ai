"""
AJAX AI - Memory Privacy Filter
Prevents storing sensitive user credentials, bank cards, or passwords in memory.
"""

import re
from typing import Tuple

SENSITIVE_MEM_PATTERNS = [
    re.compile(r'\b(?:\d[ -]*?){13,16}\b'), # Credit card numbers
    re.compile(r'(?:password|pin|secret|otp|cvv)\s*[:=is]+\s*([^\s]+)', re.IGNORECASE),
    re.compile(r'(?:sk-[a-zA-Z0-9]{20,})', re.IGNORECASE),
]

class MemoryPrivacyFilter:
    @staticmethod
    def is_safe_to_remember(text: str) -> Tuple[bool, str]:
        for pattern in SENSITIVE_MEM_PATTERNS:
            if pattern.search(text):
                return False, "Contains sensitive credentials, passwords, or payment cards."
        return True, "Safe"

privacy_filter = MemoryPrivacyFilter()
