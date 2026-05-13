from pathlib import Path
from sqlalchemy.orm import Session

from app.models.file_object import FileObject

def delete_fileobject_and_file(db: Session, file_id: int | None) -> None:
    if not file_id:
        return
    fo = db.query(FileObject).filter(FileObject.id == file_id).first()
    if not fo:
        return
    path = Path(fo.storage_path)
    db.delete(fo)
    # commit снаружи
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass