from typing import Any, Dict, List
from pydantic import BaseModel


class PaginatedRaw(BaseModel):
    rows: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
