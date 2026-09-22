from pydantic import BaseModel
from typing import List, Any, Optional

class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    limit: int
    total_pages: int
