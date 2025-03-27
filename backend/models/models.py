from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class RelatedModel(BaseModel):
    id: int
    name: str
    project_name: str
    lineage_id: Optional[int] = None

class Model(BaseModel):
    id: int
    name: str
    project_id: int
    project_name: str
    file_path: str
    schema: Optional[str] = None
    materialized: Optional[str] = None
    description: Optional[str] = None
    ai_description: Optional[str] = None
    user_edited: Optional[bool] = None
    raw_sql: Optional[str] = None
    compiled_sql: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    column_count: int = 0

    class Config:
        orm_mode = True

class ModelWithLineage(Model):
    upstream: List[RelatedModel] = []
    downstream: List[RelatedModel] = []

class Column(BaseModel):
    id: int
    name: str
    model_id: int
    model_name: Optional[str] = None
    project_name: Optional[str] = None
    data_type: Optional[str] = None
    description: Optional[str] = None
    ai_description: Optional[str] = None
    user_edited: Optional[bool] = None
    is_primary_key: Optional[bool] = None
    is_foreign_key: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class RelatedColumn(Column):
    confidence: float = 1.0

class ColumnWithLineage(Column):
    upstream_columns: List[Dict[str, Any]] = []
    downstream_columns: List[Dict[str, Any]] = []

# Comment out AI-related model
# class ModelSuggestion(BaseModel):
#     id: int
#     model_id: int
#     suggestion: str
#     created_at: datetime 