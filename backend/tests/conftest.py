import io
from pathlib import Path

import dpkt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.deps import get_db

# Важно: импортируем все модели, чтобы таблицы попали в metadata
import app.models.user
import app.models.file_object
import app.models.raw_group
import app.models.raw_trace
import app.models.labeled_trace
import app.models.labeled_trace_source

from app.models.base import Base
from app.models.file_object import FileObject
from app.models.raw_trace import RawTrace
from app.models.user import User
from app.security import hash_password
from app.services.pcap_meta import analyze_capture
from app.routers import raw_traces as raw_traces_router


TEST_DB_URL = "sqlite://"


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(engine):
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("DISABLE_STARTUP_SEED", "1")

    from app.main import app as fastapi_app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db

    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_session.get_bind(),
    )

    def test_analyze_raw_trace_bg(trace_id: int):
        db = TestSessionLocal()
        try:
            rt = db.query(RawTrace).filter(RawTrace.id == trace_id).first()
            if not rt:
                return

            fo = db.query(FileObject).filter(FileObject.id == rt.file_id).first()
            if not fo:
                return

            t_min, t_max, packets_count, _fmt = analyze_capture(fo.storage_path)
            rt.t_min = t_min
            rt.t_max = t_max
            rt.packets_count = packets_count
            db.commit()
        finally:
            db.close()

    monkeypatch.setattr(raw_traces_router, "analyze_raw_trace_bg", test_analyze_raw_trace_bg)

    with TestClient(fastapi_app) as c:
        yield c

    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def admin_user(db_session):
    user = User(
        login="admin000",
        password_hash=hash_password("admin000"),
        last_name="Admin",
        first_name="Root",
        organization="MSU",
        email="admin@example.com",
        role="admin",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def regular_user(db_session):
    user = User(
        login="user0001",
        password_hash=hash_password("user0001"),
        last_name="Ivanov",
        first_name="Ivan",
        organization="MSU",
        email="user@example.com",
        role="user",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client: TestClient, login: str, password: str):
    resp = client.post("/auth/login", json={"login": login, "password": password})
    if resp.status_code == 422:
        resp = client.post("/auth/login", data={"login": login, "password": password})
    return resp


@pytest.fixture()
def admin_headers(client, admin_user):
    resp = _login(client, "admin000", "admin000")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    token = data.get("access_token") or data.get("token")
    assert token
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def user_headers(client, regular_user):
    resp = _login(client, "user0001", "user0001")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    token = data.get("access_token") or data.get("token")
    assert token
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sample_group_payload():
    return {
        "org": "MSU",
        "data_character": "L2 traffic",
        "hardware_desc": "Server Xeon, 64GB RAM",
        "software_desc": "dpdkcap 1.0",
        "processing_degree": "headers only",
        "capture_points": 1,
        "capture_start": "2025-07-02T00:41:04",
        "capture_end": "2025-07-02T00:45:04",
    }


@pytest.fixture()
def created_group(client, admin_headers, sample_group_payload):
    resp = client.post("/raw-groups", json=sample_group_payload, headers=admin_headers)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


def make_pcap_bytes() -> bytes:
    bio = io.BytesIO()
    writer = dpkt.pcap.Writer(bio)
    writer.writepkt(b"\x00" * 60, ts=1751416864.0)
    writer.writepkt(b"\x01" * 60, ts=1751416865.0)
    writer.writepkt(b"\x02" * 60, ts=1751416870.0)
    return bio.getvalue()


@pytest.fixture()
def qos_csv_bytes():
    return (
        "seconds,nanoseconds,session_id,speed,RTT,jitter,loss\n"
        "1751416864,0,1,10.5,2.1,0.2,0.0\n"
        "1751416865,0,1,11.0,2.0,0.3,0.0\n"
    ).encode("utf-8")


@pytest.fixture()
def mac_csv_bytes():
    return (
        "seconds,nanoseconds,mac\n"
        "1751416864,0,aa:bb:cc:dd:ee:ff\n"
        "1751416865,0,11:22:33:44:55:66\n"
    ).encode("utf-8")