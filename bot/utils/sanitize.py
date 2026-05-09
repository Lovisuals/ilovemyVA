import html
def escape_html(text: str) -> str:
    if not text:
        return ""
    return html.escape(text)
def sanitize_callback_data(data: str) -> str:
    if not data:
        return ""
    return data[:64]
