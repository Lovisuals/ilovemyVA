import hashlib
import json
from typing import List, Dict, Any
def calculate_content_hash(text: str, file_ids: List[Dict[str, Any]]) -> str:
    sorted_files = sorted(file_ids, key=lambda x: (x.get("type", ""), x.get("file_id", "")))
    data = {
        "text": text or "",
        "files": sorted_files
    }
    dump = json.dumps(data, sort_keys=True)
    return hashlib.sha256(dump.encode()).hexdigest()
