import csv
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import get_db
from app.deps_auth import get_current_user, require_admin
from app.models.file_object import FileObject
from app.models.labeled_trace import LabeledTrace
from app.models.labeled_trace_source import LabeledTraceSource
from app.models.raw_trace import RawTrace
from app.models.user import User
from app.schemas.labeled_trace import LabeledTraceOut, LabeledTraceSearchOut
from app.services.cleanup import delete_fileobject_and_file
from app.services.storage import new_filename, save_upload_to_path

router = APIRouter(prefix="/labeled-traces", tags=["labeled-traces"])

ALLOWED_KINDS = {"qos", "mac_intensity"}

QOS_REQUIRED_COLUMNS = ["seconds", "nanoseconds", "session_id", "speed", "RTT", "jitter", "loss"]
MAC_REQUIRED_COLUMNS = ["seconds", "nanoseconds"]


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_dt(seconds_value: str, nanoseconds_value: str | None) -> datetime:
    sec = int(seconds_value)
    ns = int(nanoseconds_value or "0")
    ts = sec + ns / 1_000_000_000
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _validate_and_extract_bounds(csv_path: Path, kind: str) -> tuple[datetime | None, datetime | None]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []

        required = QOS_REQUIRED_COLUMNS if kind == "qos" else MAC_REQUIRED_COLUMNS
        missing = [c for c in required if c not in header]
        if missing:
            raise HTTPException(status_code=422, detail=f"Missing csv columns: {', '.join(missing)}")

        t_from = None
        t_to = None

        for row in reader:
            sec = row.get("seconds")
            ns = row.get("nanoseconds")
            if not sec:
                continue

            dt = _to_dt(sec, ns)

            if t_from is None or dt < t_from:
                t_from = dt
            if t_to is None or dt > t_to:
                t_to = dt

        return t_from, t_to


def _parse_raw_trace_ids(value: str) -> list[int]:
    ids: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if part:
            ids.append(int(part))
    return ids


def _get_donor_ids(db: Session, labeled_trace_id: int) -> list[int]:
    rows = (
        db.query(LabeledTraceSource)
        .filter(LabeledTraceSource.labeled_trace_id == labeled_trace_id)
        .order_by(LabeledTraceSource.raw_trace_id.asc())
        .all()
    )
    return [row.raw_trace_id for row in rows]


def _build_out(db: Session, labeled: LabeledTrace) -> LabeledTraceOut:
    return LabeledTraceOut(
        id=labeled.id,
        kind=labeled.kind,
        group_id=labeled.group_id,
        file_id=labeled.file_id,
        description_file_id=labeled.description_file_id,
        software_desc=labeled.software_desc,
        t_from=labeled.t_from,
        t_to=labeled.t_to,
        created_by=labeled.created_by,
        created_at=labeled.created_at,
        donor_raw_trace_ids=_get_donor_ids(db, labeled.id),
    )


@router.post("", response_model=LabeledTraceOut)
def upload_labeled_trace(
    kind: str = Form(...),
    raw_trace_ids: str = Form(...),  # "12,13,14"
    software_desc: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if kind not in ALLOWED_KINDS:
        raise HTTPException(status_code=422, detail="kind must be qos or mac_intensity")

    donor_ids = _parse_raw_trace_ids(raw_trace_ids)
    if not donor_ids:
        raise HTTPException(status_code=422, detail="At least one donor raw trace is required")

    donors = db.query(RawTrace).filter(RawTrace.id.in_(donor_ids)).all()
    if len(donors) != len(donor_ids):
        raise HTTPException(status_code=404, detail="One or more donor raw traces not found")

    group_ids = {d.group_id for d in donors}
    if len(group_ids) != 1:
        raise HTTPException(status_code=422, detail="All donor traces must belong to one raw group")
    group_id = next(iter(group_ids))

    fname = new_filename(file.filename, default_ext=".csv")
    dst = Path(settings.STORAGE_ROOT) / "labeled" / kind / str(group_id) / fname
    size, sha = save_upload_to_path(file, dst)

    t_from, t_to = _validate_and_extract_bounds(dst, kind)

    fo = FileObject(
        storage_path=str(dst),
        content_type="csv",
        size_bytes=size,
        sha256=sha,
    )
    db.add(fo)
    db.commit()
    db.refresh(fo)

    labeled = LabeledTrace(
        kind=kind,
        group_id=group_id,
        file_id=fo.id,
        software_desc=software_desc,
        t_from=t_from,
        t_to=t_to,
        created_by=user.id,
    )
    db.add(labeled)
    db.commit()
    db.refresh(labeled)

    for donor_id in donor_ids:
        link = LabeledTraceSource(
            labeled_trace_id=labeled.id,
            raw_trace_id=donor_id,
        )
        db.add(link)
    db.commit()

    return _build_out(db, labeled)


@router.post("/{labeled_trace_id}/description")
def upload_labeled_description(
    labeled_trace_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    labeled = db.query(LabeledTrace).filter(LabeledTrace.id == labeled_trace_id).first()
    if not labeled:
        raise HTTPException(status_code=404, detail="Not found")

    old_description_file_id = labeled.description_file_id

    fname = new_filename(file.filename, default_ext=".md")
    dst = Path(settings.STORAGE_ROOT) / "labeled" / "descriptions" / str(labeled_trace_id) / fname
    size, sha = save_upload_to_path(file, dst)

    fo = FileObject(
        storage_path=str(dst),
        content_type="md",
        size_bytes=size,
        sha256=sha,
    )
    db.add(fo)
    db.commit()
    db.refresh(fo)

    labeled.description_file_id = fo.id
    db.commit()

    if old_description_file_id:
        delete_fileobject_and_file(db, old_description_file_id)
        db.commit()

    return {"status": "ok", "file_id": fo.id}


@router.get("/search", response_model=list[LabeledTraceSearchOut])
def search_labeled_traces(
    kind: str | None = None,
    donor_raw_trace_id: int | None = None,
    software_desc: str | None = None,
    group_id: int | None = None,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    limit = max(1, min(limit, 200))

    q = db.query(LabeledTrace)

    if donor_raw_trace_id is not None:
        q = q.join(
            LabeledTraceSource,
            LabeledTraceSource.labeled_trace_id == LabeledTrace.id,
        ).filter(LabeledTraceSource.raw_trace_id == donor_raw_trace_id)

    if kind:
        q = q.filter(LabeledTrace.kind == kind)
    if software_desc:
        q = q.filter(LabeledTrace.software_desc.ilike(f"%{software_desc}%"))
    if group_id is not None:
        q = q.filter(LabeledTrace.group_id == group_id)
    if from_ts and to_ts:
        q = q.filter(LabeledTrace.t_to >= from_ts, LabeledTrace.t_from <= to_ts)

    traces = q.order_by(LabeledTrace.id.desc()).limit(limit).all()

    result: list[LabeledTraceSearchOut] = []
    for lt in traces:
        result.append(
            LabeledTraceSearchOut(
                id=lt.id,
                kind=lt.kind,
                group_id=lt.group_id,
                file_id=lt.file_id,
                software_desc=lt.software_desc,
                t_from=lt.t_from,
                t_to=lt.t_to,
                created_at=lt.created_at,
                donor_raw_trace_ids=_get_donor_ids(db, lt.id),
            )
        )
    return result


@router.get("/{labeled_trace_id}", response_model=LabeledTraceOut)
def get_labeled_trace(
    labeled_trace_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    labeled = db.query(LabeledTrace).filter(LabeledTrace.id == labeled_trace_id).first()
    if not labeled:
        raise HTTPException(status_code=404, detail="Not found")
    return _build_out(db, labeled)


@router.get("/{labeled_trace_id}/download", response_class=FileResponse)
def download_labeled_trace(
    labeled_trace_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    labeled = db.query(LabeledTrace).filter(LabeledTrace.id == labeled_trace_id).first()
    if not labeled:
        raise HTTPException(status_code=404, detail="Not found")

    fo = db.query(FileObject).filter(FileObject.id == labeled.file_id).first()
    if not fo:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        fo.storage_path,
        filename=Path(fo.storage_path).name,
        media_type="text/csv",
    )


@router.get("/{labeled_trace_id}/export", response_class=FileResponse)
def export_labeled_trace_fragment(
    labeled_trace_id: int,
    t_from: datetime = Query(...),
    t_to: datetime = Query(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if t_from > t_to:
        raise HTTPException(status_code=422, detail="t_from must be <= t_to")

    labeled = db.query(LabeledTrace).filter(LabeledTrace.id == labeled_trace_id).first()
    if not labeled:
        raise HTTPException(status_code=404, detail="Not found")

    fo = db.query(FileObject).filter(FileObject.id == labeled.file_id).first()
    if not fo:
        raise HTTPException(status_code=404, detail="File not found")

    src = Path(fo.storage_path)
    dst = Path(settings.STORAGE_ROOT) / "exports" / "labeled" / f"labeled_{labeled_trace_id}_{int(datetime.now().timestamp())}.csv"
    dst.parent.mkdir(parents=True, exist_ok=True)

    q_from = _ensure_utc(t_from)
    q_to = _ensure_utc(t_to)
    written = 0

    with src.open("r", encoding="utf-8-sig", newline="") as fin, dst.open("w", encoding="utf-8", newline="") as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames or [])
        writer.writeheader()

        for row in reader:
            sec = row.get("seconds")
            ns = row.get("nanoseconds")
            if not sec:
                continue

            dt = _to_dt(sec, ns)
            if q_from <= dt <= q_to:
                writer.writerow(row)
                written += 1

    if written == 0:
        dst.unlink(missing_ok=True)
        raise HTTPException(status_code=404, detail="No rows found in the selected interval")

    return FileResponse(str(dst), filename=dst.name, media_type="text/csv")


@router.delete("/{labeled_trace_id}", status_code=204)
def delete_labeled_trace(
    labeled_trace_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    labeled = db.query(LabeledTrace).filter(LabeledTrace.id == labeled_trace_id).first()
    if not labeled:
        raise HTTPException(status_code=404, detail="Not found")

    links = db.query(LabeledTraceSource).filter(LabeledTraceSource.labeled_trace_id == labeled_trace_id).all()
    for link in links:
        db.delete(link)

    file_id = labeled.file_id
    description_file_id = labeled.description_file_id

    db.delete(labeled)
    delete_fileobject_and_file(db, file_id)
    delete_fileobject_and_file(db, description_file_id)
    db.commit()
    return