from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeChunkManageInfo(BaseModel):
    id: int
    label_key: str | None = None
    crop_name: str | None = None
    disease_family: str | None = None
    health_status: str
    source_type: str
    source_name: str
    title: str
    content: str
    url: str = ""
    tags_json: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class KnowledgeChunkCreate(BaseModel):
    label_key: str | None = None
    crop_name: str | None = None
    disease_family: str | None = None
    health_status: str = "diseased"
    source_type: str = "internal"
    source_name: str = "PlantCare 知识库"
    title: str
    content: str
    url: str = ""
    tags_json: list[str] = Field(default_factory=list)


class KnowledgeChunkUpdate(BaseModel):
    label_key: str | None = None
    crop_name: str | None = None
    disease_family: str | None = None
    health_status: str | None = None
    source_type: str | None = None
    source_name: str | None = None
    title: str | None = None
    content: str | None = None
    url: str | None = None
    tags_json: list[str] | None = None
