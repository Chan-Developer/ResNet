from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: Optional[T] = None


class PageData(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
