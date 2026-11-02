"""
AJAX AI - Memory Privacy Filter
Prevents storing sensitive user credentials, bank cards, or passwords in memory.
"""

import re
from typing import Tuple

SENSITIVE_MEM_PATTERNS = [
    re.compile(r'\b(?:\d[ -]*?){13,16}\b'), # Credit card numbers
    re.compile(r'\b(?:password|passcode|pin|secret|otp|cvv|ssn)\b\s*(?::|=|is)\s*([^\s]+)', re.IGNORECASE),
    re.compile(r'\b(?:api[_ -]?key|access[_ -]?token|auth[_ -]?token|bearer)\b\s*(?::|=|is)\s*([^\s]+)', re.IGNORECASE),
    re.compile(r'\bsk-[a-zA-Z0-9]{20,}\b', re.IGNORECASE),
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', re.IGNORECASE),
    re.compile(r'(?<!\d)(?:\+?\d[\d ()-]{8,}\d)(?!\d)'),
]

class MemoryPrivacyFilter:
    @staticmethod
    def is_safe_to_remember(text: str) -> Tuple[bool, str]:
        for pattern in SENSITIVE_MEM_PATTERNS:
            if pattern.search(text):
                return False, "Contains sensitive credentials, passwords, or payment cards."
        return True, "Safe"

privacy_filter = MemoryPrivacyFilter()
