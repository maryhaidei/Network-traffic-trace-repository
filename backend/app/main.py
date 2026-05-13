import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import SessionLocal
from app.config import settings
from app.models.user import User
from app.security import hash_password

from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.raw_groups import router as raw_groups_router
from app.routers.raw_traces import router as raw_traces_router
from app.routers.labeled_traces import router as labeled_traces_router



app = FastAPI(title="Traffic Trace Repository (V1)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(raw_groups_router)
app.include_router(raw_traces_router)
app.include_router(labeled_traces_router)


@app.on_event("startup")
def seed_admin():
    if os.getenv("DISABLE_STARTUP_SEED") == "1":
        return

    try:
        db: Session = SessionLocal()
        db.execute(text("SELECT 1 FROM users LIMIT 1;"))

        admin = db.query(User).filter(User.login == settings.ADMIN_LOGIN).first()
        if not admin:
            if len(settings.ADMIN_LOGIN) != 8:
                raise RuntimeError("ADMIN_LOGIN must be exactly 8 characters")

            admin = User(
                login=settings.ADMIN_LOGIN,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                last_name=settings.ADMIN_LAST_NAME,
                first_name=settings.ADMIN_FIRST_NAME,
                organization=settings.ADMIN_ORG,
                email=settings.ADMIN_EMAIL,
                role="admin",
            )
            db.add(admin)
            db.commit()
    except Exception as e:
        print("Seed admin skipped:", e)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}