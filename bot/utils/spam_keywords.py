import re
SPAM_KEYWORDS = [
    r"crypto", r"bitcoin", r"investment", r"profit", r"earn", r"money",
    r"whatsapp", r"join now", r"click here", r"subscribe", r"limited offer",
    r"free gift", r"winner", r"congratulations", r"guaranteed", r"risk free"
]
def check_spam_regex(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    for pattern in SPAM_KEYWORDS:
        if re.search(pattern, text_lower):
            return True
    return False
