from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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