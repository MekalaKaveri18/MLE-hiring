"""
Safety and adversarial detection module.
Runs BEFORE any LLM call to catch injections, social engineering, exfiltration attempts.
"""

import re
import base64

# Injection patterns — order matters, check most explicit first
INJECTION_PATTERNS = [
    # Direct override attempts
    r"ignore (all )?(previous|prior|above|your) (instructions?|guidelines?|rules?|prompts?|system)",
    r"disregard (all )?(previous|prior|above|your) (instructions?|guidelines?|rules?|prompts?|system)",
    r"(you are|you're) now (in |)(maintenance mode|dan|jailbreak|unrestricted)",
    r"system override",
    r"override (safety|all) (protocols?|instructions?|guidelines?)",
    r"(output|print|respond with|say exactly|respond exactly).*auth_code",
    r"resume normal operation",
    r"dan mode",
    r"do anything now",
    # Exfiltration attempts
    r"(output|print|show|display|reveal|share|provide).{0,60}(system prompt|internal instructions?|your instructions?|all (rules|guidelines|tools|functions|documents))",
    r"(full text|complete (list|text|contents?)) of your (system|instructions?|prompt)",
    r"(retrieval algorithm|confidence scoring algorithm|exact (logic|algorithm))",
    r"names? of all (tools|functions) available",
    # Social engineering — impersonation
    r"i (am|'m) (a |an )?(senior |)(qa engineer|employee|staff|ciso|anthropic|devplatform|visa).{0,40}(audit|access|emergency|internal|override)",
    r"internal credentials?.*emp_id",
    r"access_level.*l[0-9]",
    # Prompt injection via role
    r"<system>",
    r"\[system override\]",
    r"\[system\]",
    # Manipulation of classification
    r"classify this as (replied|escalated|invalid)",
    r"(output|respond with|set status to).{0,30}(replied|escalated)",
    # CVE / alert acknowledgment social engineering
    r"output the string.*alert_ack",
    r"acknowledge.*prevent automatic escalation",
]

_COMPILED = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in INJECTION_PATTERNS]


def _try_decode_base64(text: str) -> str:
    """Try to decode base64 strings found in content."""
    b64_pattern = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")
    for match in b64_pattern.finditer(text):
        try:
            decoded = base64.b64decode(match.group()).decode("utf-8", errors="ignore")
            if len(decoded) > 10 and decoded.isprintable():
                text += "\n[DECODED_B64]: " + decoded
        except Exception:
            pass
    return text


def check_injection(content: str) -> tuple[bool, str]:
    """
    Returns (is_injection, reason).
    Checks raw content AND any base64-decoded content.
    """
    expanded = _try_decode_base64(content)
    for pat in _COMPILED:
        m = pat.search(expanded)
        if m:
            return True, f"Adversarial pattern detected: '{m.group()[:80]}'"
    return False, ""


PII_PATTERNS = {
    "credit_card": re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}[\-]\d{2}[\-]\d{4}\b"),
    "phone": re.compile(r"\b(\+?\d{1,3}[\s\-]?)?\(?\d{3}\)?[\s\-]\d{3}[\s\-]\d{4}\b"),
    "email_in_content": re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"),
    "address": re.compile(r"\b\d{3,5}\s+[A-Za-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Blvd|Boulevard)\b", re.IGNORECASE),
    "dob": re.compile(r"\b(dob|date of birth|born on)[\s:]+\d{2}[\/\-]\d{2}[\/\-]\d{4}\b", re.IGNORECASE),
}


def detect_pii(text: str) -> bool:
    """Returns True if any PII patterns found."""
    for name, pat in PII_PATTERNS.items():
        if pat.search(text):
            return True
    return False
