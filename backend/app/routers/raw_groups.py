import hashlib
import json
import zipfile
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
from app.schemas.raw_group import RawGroupCreate, RawGroupOut, RawGroupUpdate
from app.services.cleanup import delete_fileobject_and_file
from app.services.pcap_meta import analyze_capture, export_pcap_segment
from app.services.storage import new_filename, save_upload_to_path

router = APIRouter(prefix="/raw-groups", tags=["raw-groups"])


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _save_group_meta_file(
    *,
    group: RawGroup,
    file: UploadFile,
    db: Session,
    is_description: bool,
) -> dict:
    subdir = Path(settings.STORAGE_ROOT) / "raw" / str(group.id) / "meta"
    default_ext = ".md" if is_description else ".bin"
    fname = new_filename(file.filename, default_ext=default_ext)
    dst = subdir / fname
    size, sha = save_upload_to_path(file, dst)

    content_type = "md" if is_description else (file.content_type or "application/octet-stream")
    fo = FileObject(
        storage_path=str(dst),
        content_type=content_type,
        size_bytes=size,
        sha256=sha,
    )
    db.add(fo)
    db.commit()
    db.refresh(fo)

    old_file_id = group.description_file_id if is_description else group.schema_file_id

    if is_description:
        group.description_file_id = fo.id
    else:
        group.schema_file_id = fo.id

    db.commit()

    if old_file_id:
        delete_fileobject_and_file(db, old_file_id)
        db.commit()

    return {"status": "ok", "file_id": fo.id}


@router.post("", response_model=RawGroupOut)
def create_group(
    data: RawGroupCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    exists = db.query(RawGroup).filter(RawGroup.name == data.name).first()
    if exists:
        raise HTTPException(status_code=409, detail="Group name already exists")

    if data.capture_start > data.capture_end:
        raise HTTPException(status_code=422, detail="capture_start must be <= capture_end")

    if data.capture_points not in (1, 2):
        raise HTTPException(status_code=422, detail="capture_points must be 1 or 2")

    g = RawGroup(
        name=data.name,
        org=data.org,
        data_character=data.data_character,
        capture_start=data.capture_start,
        capture_end=data.capture_end,
        hardware_desc=data.hardware_desc,
        software_desc=data.software_desc,
        processing_degree=data.processing_degree,
        capture_points=data.capture_points,
        created_by=user.id,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@router.get("", response_model=list[RawGroupOut])
def list_groups(
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    limit = max(1, min(limit, 200))
    return db.query(RawGroup).order_by(RawGroup.id.desc()).limit(limit).all()


@router.get("/search", response_model=list[RawGroupOut])
def search_groups(
    name: str | None = None,
    org: str | None = None,
    data_character: str | None = None,
    hardware_desc: str | None = None,
    software_desc: str | None = None,
    capture_points: int | None = None,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    limit = max(1, min(limit, 200))

    q = db.query(RawGroup)

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
    if from_ts and to_ts:
        q = q.filter(RawGroup.capture_end >= from_ts, RawGroup.capture_start <= to_ts)
    if name:
        q = q.filter(RawGroup.name.ilike(f"%{name}%"))

    return q.order_by(RawGroup.id.desc()).limit(limit).all()


@router.get("/{group_id}", response_model=RawGroupOut)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    g = db.query(RawGroup).filter(RawGroup.id == group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Not found")
    return g


@router.patch("/{group_id}", response_model=RawGroupOut)
def update_group(
    group_id: int,
    body: RawGroupUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    g = db.query(RawGroup).filter(RawGroup.id == group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Not found")

    payload = body.model_dump(exclude_unset=True)

    if "capture_start" in payload and "capture_end" not in payload:
        if payload["capture_start"] and g.capture_end and payload["capture_start"] > g.capture_end:
            raise HTTPException(status_code=422, detail="capture_start must be <= capture_end")

    if "capture_end" in payload and "capture_start" not in payload:
        if g.capture_start and payload["capture_end"] and g.capture_start > payload["capture_end"]:
            raise HTTPException(status_code=422, detail="capture_start must be <= capture_end")

    if "capture_start" in payload and "capture_end" in payload:
        if payload["capture_start"] and payload["capture_end"] and payload["capture_start"] > payload["capture_end"]:
            raise HTTPException(status_code=422, detail="capture_start must be <= capture_end")

    if "capture_points" in payload and payload["capture_points"] not in (1, 2):
        raise HTTPException(status_code=422, detail="capture_points must be 1 or 2")

    for k, v in payload.items():
        setattr(g, k, v)

    db.commit()
    db.refresh(g)
    return g


@router.post("/{group_id}/description")
def upload_description(
    group_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    g = db.query(RawGroup).filter(RawGroup.id == group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Not found")
    return _save_group_meta_file(group=g, file=file, db=db, is_description=True)


@router.post("/{group_id}/upload-description")
def upload_description_alias(
    group_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    g = db.query(RawGroup).filter(RawGroup.id == group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Not found")
    return _save_group_meta_file(group=g, file=file, db=db, is_description=True)


@router.post("/{group_id}/schema")
def upload_schema(
    group_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    g = db.query(RawGroup).filter(RawGroup.id == group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Not found")
    return _save_group_meta_file(group=g, file=file, db=db, is_description=False)


@router.post("/{group_id}/upload-schema")
def upload_schema_alias(
    group_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    g = db.query(RawGroup).filter(RawGroup.id == group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Not found")
    return _save_group_meta_file(group=g, file=file, db=db, is_description=False)


@router.get("/{group_id}/description")
def download_description(
    group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    g = db.query(RawGroup).filter(RawGroup.id == group_id).first()
    if not g or not g.description_file_id:
        raise HTTPException(status_code=404, detail="Not found")

    fo = db.query(FileObject).filter(FileObject.id == g.description_file_id).first()
    if not fo:
        raise HTTPException(status_code=404, detail="Not found")

    return FileResponse(
        fo.storage_path,
        media_type="text/markdown",
        filename=Path(fo.storage_path).name,
    )


@router.get("/{group_id}/schema")
def download_schema(
    group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    g = db.query(RawGroup).filter(RawGroup.id == group_id).first()
    if not g or not g.schema_file_id:
        raise HTTPException(status_code=404, detail="Not found")

    fo = db.query(FileObject).filter(FileObject.id == g.schema_file_id).first()
    if not fo:
        raise HTTPException(status_code=404, detail="Not found")

    return FileResponse(
        fo.storage_path,
        filename=Path(fo.storage_path).name,
    )


@router.get("/{group_id}/export", response_class=FileResponse)
def export_group_zip(
    group_id: int,
    include_pcaps: bool = True,
    t_from: datetime | None = Query(default=None),
    t_to: datetime | None = Query(default=None),
    bg: BackgroundTasks = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if (t_from and not t_to) or (t_to and not t_from):
        raise HTTPException(status_code=422, detail="Provide both t_from and t_to, or neither")
    if t_from and t_to and t_from > t_to:
        raise HTTPException(status_code=422, detail="t_from must be <= t_to")

    g = db.query(RawGroup).filter(RawGroup.id == group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")

    traces = (
        db.query(RawTrace)
        .filter(RawTrace.group_id == group_id)
        .order_by(RawTrace.id.asc())
        .all()
    )

    export_dir = Path(settings.STORAGE_ROOT) / "exports" / "groups" / str(group_id)
    export_dir.mkdir(parents=True, exist_ok=True)
    zip_path = export_dir / f"group_{group_id}_{uuid4().hex}.zip"

    meta = {
        "group": {
            "id": g.id,
            "name": g.name,
            "org": g.org,
            "data_character": g.data_character,
            "hardware_desc": g.hardware_desc,
            "software_desc": g.software_desc,
            "processing_degree": g.processing_degree,
            "capture_points": g.capture_points,
            "capture_start": g.capture_start.isoformat() if g.capture_start else None,
            "capture_end": g.capture_end.isoformat() if g.capture_end else None,
        },
        "export": {
            "include_pcaps": include_pcaps,
            "t_from": t_from.isoformat() if t_from else None,
            "t_to": t_to.isoformat() if t_to else None,
        },
        "traces": [],
    }

    for rt in traces:
        meta["traces"].append(
            {
                "id": rt.id,
                "point": rt.point,
                "file_id": rt.file_id,
                "t_min": rt.t_min.isoformat() if rt.t_min else None,
                "t_max": rt.t_max.isoformat() if rt.t_max else None,
                "packets_count": rt.packets_count,
                "capture_series": rt.capture_series,
                "part_index": rt.part_index,
            }
        )

    tmp_segments: list[Path] = []

    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
            zf.writestr("metadata.json", json.dumps(meta, ensure_ascii=False, indent=2))

            if g.description_file_id:
                fo = db.query(FileObject).filter(FileObject.id == g.description_file_id).first()
                if fo and Path(fo.storage_path).exists():
                    zf.write(fo.storage_path, arcname="docs/description.md")

            if g.schema_file_id:
                fo = db.query(FileObject).filter(FileObject.id == g.schema_file_id).first()
                if fo and Path(fo.storage_path).exists():
                    ext = Path(fo.storage_path).suffix or ".bin"
                    zf.write(fo.storage_path, arcname=f"docs/schema{ext}")

            if include_pcaps:
                for rt in traces:
                    fo = db.query(FileObject).filter(FileObject.id == rt.file_id).first()
                    if not fo or not Path(fo.storage_path).exists():
                        continue

                    if t_from and t_to:
                        seg_path = export_dir / f"trace_{rt.id}_{uuid4().hex}.pcap"
                        try:
                            written = export_pcap_segment(fo.storage_path, seg_path, t_from, t_to)
                            if written > 0:
                                zf.write(seg_path, arcname=f"pcaps/trace_{rt.id}.pcap")
                                tmp_segments.append(seg_path)
                        except Exception:
                            if seg_path.exists():
                                seg_path.unlink(missing_ok=True)
                    else:
                        zf.write(fo.storage_path, arcname=f"pcaps/trace_{rt.id}.pcap")
    finally:
        for p in tmp_segments:
            p.unlink(missing_ok=True)

    if bg is not None:
        bg.add_task(lambda p=str(zip_path): Path(p).unlink(missing_ok=True))

    return FileResponse(
        str(zip_path),
        filename=zip_path.name,
        media_type="application/zip",
    )


@router.post("/import", response_model=RawGroupOut)
def import_group_zip(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported")

    tmp_dir = Path(settings.STORAGE_ROOT) / "imports" / "groups"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_zip_path = tmp_dir / f"import_{uuid4().hex}.zip"

    file.file.seek(0)
    tmp_zip_path.write_bytes(file.file.read())

    try:
        with zipfile.ZipFile(tmp_zip_path, "r") as zf:
            if "metadata.json" not in zf.namelist():
                raise HTTPException(status_code=400, detail="metadata.json not found in archive")

            meta = json.loads(zf.read("metadata.json").decode("utf-8"))
            g_meta = meta.get("group") or {}
            traces_meta = meta.get("traces") or []

            g = RawGroup(
                org=g_meta.get("org"),
                data_character=g_meta.get("data_character"),
                hardware_desc=g_meta.get("hardware_desc"),
                software_desc=g_meta.get("software_desc"),
                processing_degree=g_meta.get("processing_degree") or "",
                capture_points=g_meta.get("capture_points") or 1,
                capture_start=_parse_dt(g_meta.get("capture_start")),
                capture_end=_parse_dt(g_meta.get("capture_end")),
                created_by=user.id,
            )
            db.add(g)
            db.commit()
            db.refresh(g)

            if "docs/description.md" in zf.namelist():
                desc_bytes = zf.read("docs/description.md")
                desc_dir = Path(settings.STORAGE_ROOT) / "raw" / str(g.id) / "meta"
                desc_dir.mkdir(parents=True, exist_ok=True)
                desc_path = desc_dir / "description.md"
                desc_path.write_bytes(desc_bytes)

                fo = FileObject(
                    storage_path=str(desc_path),
                    content_type="md",
                    size_bytes=len(desc_bytes),
                    sha256=_sha256_bytes(desc_bytes),
                )
                db.add(fo)
                db.commit()
                db.refresh(fo)
                g.description_file_id = fo.id
                db.commit()

            schema_name = None
            for name in zf.namelist():
                if name.startswith("docs/") and name != "docs/description.md":
                    schema_name = name
                    break

            if schema_name:
                schema_bytes = zf.read(schema_name)
                ext = Path(schema_name).suffix or ".bin"
                schema_dir = Path(settings.STORAGE_ROOT) / "raw" / str(g.id) / "meta"
                schema_dir.mkdir(parents=True, exist_ok=True)
                schema_path = schema_dir / f"schema{ext}"
                schema_path.write_bytes(schema_bytes)

                fo = FileObject(
                    storage_path=str(schema_path),
                    content_type="image",
                    size_bytes=len(schema_bytes),
                    sha256=_sha256_bytes(schema_bytes),
                )
                db.add(fo)
                db.commit()
                db.refresh(fo)
                g.schema_file_id = fo.id
                db.commit()

            pcap_names = sorted(n for n in zf.namelist() if n.startswith("pcaps/"))
            for trace_meta, pcap_name in zip(traces_meta, pcap_names):
                pcap_bytes = zf.read(pcap_name)

                capture_series = trace_meta.get("capture_series")
                part_index = trace_meta.get("part_index")
                series_dir = capture_series.replace("/", "_") if capture_series else "single"

                pcap_dir = Path(settings.STORAGE_ROOT) / "raw" / str(g.id) / series_dir
                pcap_dir.mkdir(parents=True, exist_ok=True)
                pcap_path = pcap_dir / Path(pcap_name).name
                pcap_path.write_bytes(pcap_bytes)

                fo = FileObject(
                    storage_path=str(pcap_path),
                    content_type="pcap",
                    size_bytes=len(pcap_bytes),
                    sha256=_sha256_bytes(pcap_bytes),
                )
                db.add(fo)
                db.commit()
                db.refresh(fo)

                t_min = _parse_dt(trace_meta.get("t_min"))
                t_max = _parse_dt(trace_meta.get("t_max"))
                packets_count = trace_meta.get("packets_count")

                if t_min is None or t_max is None or packets_count is None:
                    try:
                        a_min, a_max, count, _fmt = analyze_capture(pcap_path)
                        t_min = t_min or a_min
                        t_max = t_max or a_max
                        packets_count = packets_count or count
                    except Exception:
                        pass

                rt = RawTrace(
                    group_id=g.id,
                    file_id=fo.id,
                    point=trace_meta.get("point") or "Single",
                    t_min=t_min,
                    t_max=t_max,
                    packets_count=packets_count,
                    capture_series=capture_series,
                    part_index=part_index,
                )
                db.add(rt)
                db.commit()

        db.refresh(g)
        return g
    finally:
        tmp_zip_path.unlink(missing_ok=True)


@router.delete("/{group_id}", status_code=204)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    g = db.query(RawGroup).filter(RawGroup.id == group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Not found")

    traces = db.query(RawTrace).filter(RawTrace.group_id == group_id).all()
    for rt in traces:
        file_id = rt.file_id
        db.delete(rt)
        delete_fileobject_and_file(db, file_id)

    delete_fileobject_and_file(db, g.description_file_id)
    delete_fileobject_and_file(db, g.schema_file_id)

    db.delete(g)
    db.commit()
    return