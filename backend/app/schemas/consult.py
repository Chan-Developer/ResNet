from typing import Literal

from pydantic import BaseModel, Field


class ConsultMessageIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ConsultRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[ConsultMessageIn] = Field(default_factory=list, max_length=8)


class ConsultResponse(BaseModel):
    answer: str
