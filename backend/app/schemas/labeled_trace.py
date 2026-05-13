from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LabelRunIn(BaseModel):
    raw_trace_id: int
    kind: str = Field(pattern="^(qos|mac_intensity)$")
    t_from: datetime | None = None
    t_to: datetime | None = None


class JobOut(BaseModel):
    id: int
    status: str
    kind: str
    raw_trace_id: int
    group_id: int
    requested_by: int
    t_from: datetime | None = None
    t_to: datetime | None = None
    tool_info: str | None = None
    error_text: str | None = None

    model_config = ConfigDict(from_attributes=True)


class LabeledTraceOut(BaseModel):
    id: int
    kind: str
    group_id: int
    file_id: int
    description_file_id: int | None = None
    software_desc: str | None = None
    t_from: datetime | None = None
    t_to: datetime | None = None
    created_by: int | None = None
    created_at: datetime | None = None
    donor_raw_trace_ids: list[int] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class LabeledTraceSearchOut(BaseModel):
    id: int
    kind: str
    group_id: int
    file_id: int
    software_desc: str | None = None
    t_from: datetime | None = None
    t_to: datetime | None = None
    created_at: datetime | None = None
    donor_raw_trace_ids: list[int] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)