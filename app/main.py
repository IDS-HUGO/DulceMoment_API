from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import router as api_router
from app.core.config import settings
from app.db.database import Base, SessionLocal, engine
from app.db.seed import seed_data

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if engine.dialect.name == "sqlite":
            columns = db.execute(text("PRAGMA table_info(users)")).fetchall()
            column_names = [row[1] for row in columns]
            if "password_hash" not in column_names:
                db.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) DEFAULT ''"))
                db.commit()
            if "token_version" not in column_names:
                db.execute(text("ALTER TABLE users ADD COLUMN token_version INTEGER DEFAULT 0"))
                db.commit()
        seed_data(db)
    finally:
        db.close()


@app.get("/")
def root():
    return {"app": settings.app_name, "docs": "/docs"}
