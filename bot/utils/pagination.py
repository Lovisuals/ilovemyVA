from typing import List, Tuple, Any
def get_pagination_metadata(total_count: int, page: int, per_page: int) -> Tuple[int, int, int]:
    total_pages = (total_count + per_page - 1) // per_page
    total_pages = max(1, total_pages)
    current_page = max(1, min(page, total_pages))
    offset = (current_page - 1) * per_page
    return current_page, total_pages, offset
