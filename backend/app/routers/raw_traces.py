import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import get_db
from app.deps_auth import get_current_user, require_admin
from app.models.file_object import FileObject
from app.models.raw_group import RawGroup
from app.models.raw_trace import RawTrace
from app.models.user import User
from app.schemas.raw_trace import RawTraceOut, RawTraceSearchOut
from app.services.cleanup import delete_fileobject_and_file
from app.services.pcap_meta import export_pcap_segment
from app.services.raw_trace_tasks import analyze_raw_trace_bg
from app.services.storage import new_filename, save_upload_to_path

router = APIRouter(prefix="/raw-traces", tags=["raw-traces"])

_SPLIT_RE = re.compile(r"^(?P<series>.+\.pcap)(?P<part>\d{3})$", re.IGNORECASE)


def parse_split_name(filename: str) -> tuple[str | None, int | None]:
    name = Path(filename).name
    m = _SPLIT_RE.match(name)
    if not m:
        return None, None
    return m.group("series"), int(m.group("part"))


def _validate_point_for_group(group: RawGroup, point: str) -> str:
    point = point.strip()
    if group.capture_points == 1 and point != "Single":
        raise HTTPException(status_code=422, detail="For 1-point capture, point must be Single")
    if group.capture_points == 2 and point not in ("A", "B"):
        raise HTTPException(status_code=422, detail="For 2-point capture, point must be A or B")
    return point


def _trace_search_out(rt: RawTrace, group: RawGroup) -> RawTraceSearchOut:
    return RawTraceSearchOut(
        id=rt.id,
        group_id=rt.group_id,
        point=rt.point,
        file_id=rt.file_id,
        t_min=rt.t_min,
        t_max=rt.t_max,
        packets_count=rt.packets_count,
        capture_series=rt.capture_series,
        part_index=rt.part_index,
        org=group.org,
        data_character=group.data_character,
        hardware_desc=group.hardware_desc,
        software_desc=group.software_desc,
        capture_points=group.capture_points,
        capture_start=group.capture_start,
        capture_end=group.capture_end,
    )


@router.post("/group/{group_id}", response_model=RawTraceOut)
def upload_pcap(
    group_id: int,
    point: str = Query(default="Single"),
    file: UploadFile = File(...),
    bg: BackgroundTasks = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    group = db.query(RawGroup).filter(RawGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    point = _validate_point_for_group(group, point)

    capture_series, part_index = parse_split_name(file.filename)
    series_dir = capture_series.replace("/", "_") if capture_series else "single"

    fname = new_filename(file.filename, default_ext=".pcap")
    dst = Path(settings.STORAGE_ROOT) / "raw" / str(group_id) / series_dir / fname
    size, sha = save_upload_to_path(file, dst)

    fo = FileObject(
        storage_path=str(dst),
        content_type="pcap",
        size_bytes=size,
        sha256=sha,
    )
    db.add(fo)
    db.commit()
    db.refresh(fo)

    rt = RawTrace(
        group_id=group_id,
        point=point,
        file_id=fo.id,
        t_min=None,
        t_max=None,
        packets_count=None,
        capture_series=capture_series,
        part_index=part_index,
    )
    db.add(rt)
    db.commit()
    db.refresh(rt)

    if bg is not None:
        bg.add_task(analyze_raw_trace_bg, rt.id)

    return rt

def _get_group_by_name(db: Session, group_name: str) -> RawGroup:
    group = db.query(RawGroup).filter(RawGroup.name == group_name).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@router.post("/group/by-name/{group_name}", response_model=RawTraceOut)
def upload_pcap_by_group_name(
    group_name: str,
    point: str = Query(default="Single"),
    file: UploadFile = File(...),
    bg: BackgroundTasks = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    group = _get_group_by_name(db, group_name)

    point = _validate_point_for_group(group, point)

    capture_series, part_index = parse_split_name(file.filename)
    series_dir = capture_series.replace("/", "_") if capture_series else "single"

    fname = new_filename(file.filename, default_ext=".pcap")
    dst = Path(settings.STORAGE_ROOT) / "raw" / str(group.id) / series_dir / fname
    size, sha = save_upload_to_path(file, dst)

    fo = FileObject(
        storage_path=str(dst),
        content_type="pcap",
        size_bytes=size,
        sha256=sha,
    )
    db.add(fo)
    db.commit()
    db.refresh(fo)

    rt = RawTrace(
        group_id=group.id,
        point=point,
        file_id=fo.id,
        t_min=None,
        t_max=None,
        packets_count=None,
        capture_series=capture_series,
        part_index=part_index,
    )
    db.add(rt)
    db.commit()
    db.refresh(rt)

    if bg is not None:
        bg.add_task(analyze_raw_trace_bg, rt.id)

    return rt

@router.post("/group/by-name/{group_name}/batch", response_model=list[RawTraceOut])
def upload_pcap_batch_by_group_name(
    group_name: str,
    files: list[UploadFile] = File(...),
    point: str = Query(default="Single"),
    bg: BackgroundTasks = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    group = _get_group_by_name(db, group_name)

    point = _validate_point_for_group(group, point)

    result: list[RawTrace] = []

    for file in files:
        capture_series, part_index = parse_split_name(file.filename)
        series_dir = capture_series.replace("/", "_") if capture_series else "single"

        fname = new_filename(file.filename, default_ext=".pcap")
        dst = Path(settings.STORAGE_ROOT) / "raw" / str(group.id) / series_dir / fname
        size, sha = save_upload_to_path(file, dst)

        fo = FileObject(
            storage_path=str(dst),
            content_type="pcap",
            size_bytes=size,
            sha256=sha,
        )
        db.add(fo)
        db.commit()
        db.refresh(fo)

        rt = RawTrace(
            group_id=group.id,
            point=point,
            file_id=fo.id,
            t_min=None,
            t_max=None,
            packets_count=None,
            capture_series=capture_series,
            part_index=part_index,
        )
        db.add(rt)
        db.commit()
        db.refresh(rt)

        if bg is not None:
            bg.add_task(analyze_raw_trace_bg, rt.id)

        result.append(rt)

    return result


@router.post("/group/{group_id}/batch", response_model=list[RawTraceOut])
def upload_pcap_batch(
    group_id: int,
    files: list[UploadFile] = File(...),
    point: str = Query(default="Single"),
    bg: BackgroundTasks = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    group = db.query(RawGroup).filter(RawGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    point = _validate_point_for_group(group, point)

    result: list[RawTrace] = []

    for file in files:
        capture_series, part_index = parse_split_name(file.filename)
        series_dir = capture_series.replace("/", "_") if capture_series else "single"

        fname = new_filename(file.filename, default_ext=".pcap")
        dst = Path(settings.STORAGE_ROOT) / "raw" / str(group_id) / series_dir / fname
        size, sha = save_upload_to_path(file, dst)

        fo = FileObject(
            storage_path=str(dst),
            content_type="pcap",
            size_bytes=size,
            sha256=sha,
        )
        db.add(fo)
        db.commit()
        db.refresh(fo)

        rt = RawTrace(
            group_id=group_id,
            point=point,
            file_id=fo.id,
            t_min=None,
            t_max=None,
            packets_count=None,
            capture_series=capture_series,
            part_index=part_index,
        )
        db.add(rt)
        db.commit()
        db.refresh(rt)

        if bg is not None:
            bg.add_task(analyze_raw_trace_bg, rt.id)

        result.append(rt)

    return result


@router.get("/search", response_model=list[RawTraceSearchOut])
def search_traces(
    group_name: str | None = None,
    group_id: int | None = None,
    org: str | None = None,
    data_character: str | None = None,
    hardware_desc: str | None = None,
    software_desc: str | None = None,
    capture_points: int | None = None,
    point: str | None = None,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    limit = max(1, min(limit, 200))

    q = db.query(RawTrace, RawGroup).join(RawGroup, RawTrace.group_id == RawGroup.id)

    if group_id is not None:
        q = q.filter(RawTrace.group_id == group_id)
    if org:
        q = q.filter(RawGroup.org.ilike(f"%{org}%"))
    if data_character:
        q = q.filter(RawGroup.data_character.ilike(f"%{data_character}%"))
    if hardware_desc:
        q = q.filter(RawGroup.hardware_desc.ilike(f"%{hardware_desc}%"))
    if software_desc:
        q = q.filter(RawGroup.software_desc.ilike(f"%{software_desc}%"))
    if capture_points in (1, 2):
        q = q.filter(RawGroup.capture_points == capture_points)
    if point:
        q = q.filter(RawTrace.point == point)
    if from_ts and to_ts:
        q = q.filter(RawTrace.t_max >= from_ts, RawTrace.t_min <= to_ts)
    if group_name:
        q = q.filter(RawGroup.name.ilike(f"%{group_name}%"))

    rows = q.order_by(RawTrace.id.desc()).limit(limit).all()
    return [_trace_search_out(rt, group) for rt, group in rows]


@router.get("/{trace_id}", response_model=RawTraceOut)
def get_trace(
    trace_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rt = db.query(RawTrace).filter(RawTrace.id == trace_id).first()
    if not rt:
        raise HTTPException(status_code=404, detail="Not found")
    return rt


@router.get("/{trace_id}/download")
def download_trace(
    trace_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rt = db.query(RawTrace).filter(RawTrace.id == trace_id).first()
    if not rt:
        raise HTTPException(status_code=404, detail="Not found")

    fo = db.query(FileObject).filter(FileObject.id == rt.file_id).first()
    if not fo:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        fo.storage_path,
        filename=Path(fo.storage_path).name,
        media_type="application/vnd.tcpdump.pcap",
    )


@router.get("/{trace_id}/export")
def export_trace_segment(
    trace_id: int,
    t_from: datetime = Query(...),
    t_to: datetime = Query(...),
    bg: BackgroundTasks = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if t_from > t_to:
        raise HTTPException(status_code=422, detail="t_from must be <= t_to")

    rt = db.query(RawTrace).filter(RawTrace.id == trace_id).first()
    if not rt:
        raise HTTPException(status_code=404, detail="Not found")

    fo = db.query(FileObject).filter(FileObject.id == rt.file_id).first()
    if not fo:
        raise HTTPException(status_code=404, detail="File not found")

    export_dir = Path(settings.STORAGE_ROOT) / "exports" / "raw"
    export_dir.mkdir(parents=True, exist_ok=True)
    out_path = export_dir / f"trace_{trace_id}_{uuid4().hex}.pcap"

    try:
        written = export_pcap_segment(fo.storage_path, out_path, t_from, t_to)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if written == 0:
        out_path.unlink(missing_ok=True)
        raise HTTPException(status_code=404, detail="No packets found in the selected interval")

    if bg is not None:
        bg.add_task(lambda p=str(out_path): Path(p).unlink(missing_ok=True))

    return FileResponse(
        str(out_path),
        filename=out_path.name,
        media_type="application/vnd.tcpdump.pcap",
    )


@router.delete("/{trace_id}", status_code=204)
def delete_trace(
    trace_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    rt = db.query(RawTrace).filter(RawTrace.id == trace_id).first()
    if not rt:
        raise HTTPException(status_code=404, detail="Not found")

    file_id = rt.file_id
    db.delete(rt)
    delete_fileobject_and_file(db, file_id)
    db.commit()
    return