"bot/utils/preview.py"

def truncate_preview(text: str, length: int) -> str:
    if not text:
        return ""
    if len(text) <= length:
        return text
    return text[:length-3] + "..."

def get_media_icon(media_type: str) -> str:
    icons = {
        "photo": "🖼",
        "video": "🎥",
        "document": "📄",
        "audio": "🎵",
        "voice": "🎤",
        "animation": "🎞"
    }
    return icons.get(media_type, "📎")
