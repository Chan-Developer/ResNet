from datetime import datetime
from typing import Any

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


class ModelVersionInfo(BaseModel):
    id: int
    version_code: str
    display_name: str
    description: str
    model_path: str
    class_names_path: str
    metrics_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool
    is_runtime_loaded: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ModelVersionCreate(BaseModel):
    version_code: str
    display_name: str
    description: str = ""
    model_path: str
    class_names_path: str = ""
    metrics_json: dict[str, Any] = Field(default_factory=dict)


class ModelVersionUpdate(BaseModel):
    version_code: str | None = None
    display_name: str | None = None
    description: str | None = None
    model_path: str | None = None
    class_names_path: str | None = None
    metrics_json: dict[str, Any] | None = None


class ModelRuntimeInfo(BaseModel):
    active_version_id: int | None = None
    active_version_code: str | None = None
    model_path: str = ""
    class_names_source: str = ""
    class_count: int = 0
    device: str = "cpu"
    loaded: bool = False
