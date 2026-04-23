import os
import re

PATTERNS = {
    "scalar_one_with_none": re.compile(r"scalar_one_with_none\(\)"),
    "builder_attr_bug": re.compile(r"\.button\([^)]+\)\.button"),
    "missing_pack": re.compile(r"callback_data\s*=\s*[A-Z][a-zA-Z]+\([^)]*\)(?!\.pack\(\))(?!\s*#)"),
    "old_asyncio_scheduler": re.compile(r"from apscheduler\.schedulers\.asyncio import AsyncIOScheduler"),
    "standalone_session_in_mw": re.compile(r"async with async_session\(\) as session:"),
}

WHITELIST_STANDALONE_SESSION = {
    "bot/scheduler/jobs.py",
    "database/session.py",
    "bot/services",
}

results = []
for root, dirs, files in os.walk("bot"):
    dirs[:] = [d for d in dirs if d not in ["__pycache__"]]
    for file in files:
        if not file.endswith(".py"):
            continue
        path = os.path.join(root, file).replace("\\", "/")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        for name, pattern in PATTERNS.items():
            match = pattern.search(content)
            if not match:
                continue
            if name == "standalone_session_in_mw":
                if any(path.startswith(w) for w in WHITELIST_STANDALONE_SESSION):
                    continue
                if "middleware" not in path:
                    continue
            results.append(f"FAIL [{name}]: {path}")

if results:
    print("\n".join(results))
else:
    print("SUCCESS: All checks passed.")
