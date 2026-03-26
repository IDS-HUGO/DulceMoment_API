from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy import text

from app.api.routes import router as api_router
from app.core.config import settings
from app.db.database import Base, SessionLocal, engine
from app.db.seed import seed_data

app = FastAPI(title=settings.app_name)

media_root = Path(__file__).resolve().parents[1] / "media"
uploads_root = media_root / "uploads"
uploads_root.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=media_root), name="media")

allow_all_origins = settings.cors_allow_all

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else settings.cors_origins_list,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        message = detail.get("message") or "No se pudo completar la operación"
        payload = {"message": message, **detail}
    else:
        message = str(detail) if detail else "No se pudo completar la operación"
        payload = {"message": message}
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(str(part) for part in first.get("loc", [])[1:]) if first.get("loc") else "campo"
    reason = first.get("msg", "valor inválido")
    return JSONResponse(
        status_code=422,
        content={"message": f"Dato inválido en '{field}': {reason}"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, __: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Ocurrió un error inesperado del servidor. Intenta de nuevo."},
    )


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
