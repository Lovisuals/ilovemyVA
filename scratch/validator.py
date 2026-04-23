import os
import re

def audit_codebase():
    patterns = {
        "DetachedInstanceError": r"async with async_session\(\) as session:",
        "AttributeError builder": r"builder\.button\(.*\)\.button",
        "Missing .pack()": r"callback_data=[A-Z][a-zA-Z]+\(.*\)(?!\.pack\(\))",
        "Old scalar method": r"scalar_one_with_none",
        "Old APScheduler": r"from apscheduler\.schedulers\.asyncio import AsyncIOScheduler"
    }
    
    results = []
    for root, _, files in os.walk("bot"):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    for name, pattern in patterns.items():
                        if re.search(pattern, content):
                            results.append(f"FAIL: {path} contains {name}")
                            
    return results

if __name__ == "__main__":
    failures = audit_codebase()
    if failures:
        print("\n".join(failures))
    else:
        print("SUCCESS: No common failure patterns detected.")
