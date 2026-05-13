from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RawTraceOut(BaseModel):
    id: int
    group_id: int
    point: str
    file_id: int
    t_min: datetime | None = None
    t_max: datetime | None = None
    packets_count: int | None = None
    capture_series: str | None = None
    part_index: int | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class RawTraceSearchOut(BaseModel):
    id: int
    group_id: int
    point: str | None = None
    file_id: int | None = None
    t_min: datetime | None = None
    t_max: datetime | None = None
    packets_count: int | None = None
    capture_series: str | None = None
    part_index: int | None = None

    org: str | None = None
    data_character: str | None = None
    hardware_desc: str | None = None
    software_desc: str | None = None
    capture_points: int | None = None
    capture_start: datetime | None = None
    capture_end: datetime | None = None

    model_config = ConfigDict(from_attributes=True)