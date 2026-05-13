from __future__ import annotations

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.raw_trace import RawTrace
from app.models.file_object import FileObject
from app.services.pcap_meta import analyze_capture


def analyze_raw_trace_bg(trace_id: int) -> None:
    db: Session = SessionLocal()
    try:
        rt = db.query(RawTrace).filter(RawTrace.id == trace_id).first()
        if not rt:
            return
        fo = db.query(FileObject).filter(FileObject.id == rt.file_id).first()
        if not fo:
            return

        t_min, t_max, count, fmt = analyze_capture(fo.storage_path)
        rt.t_min = t_min
        rt.t_max = t_max
        rt.packets_count = count
        # можно сохранить fmt в отдельное поле позже (если нужно)
        db.commit()
    finally:
        db.close()