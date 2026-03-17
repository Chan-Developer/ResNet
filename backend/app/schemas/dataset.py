from typing import List

from pydantic import BaseModel


class CategoryOut(BaseModel):
    name: str
    display_name: str
    count: int


class CategoryImageOut(BaseModel):
    filename: str
    url: str
