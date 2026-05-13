from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RawGroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    org: str = Field(max_length=50)
    data_character: str = Field(max_length=200)
    capture_start: datetime
    capture_end: datetime
    hardware_desc: str = Field(max_length=300)
    software_desc: str = Field(max_length=300)
    processing_degree: str = Field(max_length=300)
    capture_points: int = Field(ge=1, le=2)


class RawGroupOut(BaseModel):
    id: int
    name: str
    org: str
    data_character: str
    capture_start: datetime
    capture_end: datetime
    hardware_desc: str
    software_desc: str
    processing_degree: str
    capture_points: int
    schema_file_id: int | None = None
    description_file_id: int | None = None
    created_by: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class RawGroupUpdate(BaseModel):
    name: str | None = None
    org: str | None = Field(default=None, max_length=50)
    data_character: str | None = Field(default=None, max_length=200)
    hardware_desc: str | None = Field(default=None, max_length=300)
    software_desc: str | None = Field(default=None, max_length=300)
    processing_degree: str | None = Field(default=None, max_length=300)
    capture_points: int | None = Field(default=None, ge=1, le=2)
    capture_start: datetime | None = None
    capture_end: datetime | None = None