"""FastAPI application entrypoint — wires routers and serves the static frontend."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import get_db
from .routers import (
    addresses,
    analytics,
    auth,
    carts,
    categories,
    orders,
    payments,
    products,
    reviews,
    suppliers,
    users,
)

app = FastAPI(
    title="E-Commerce MongoDB API",
    description="REST API for the MongoDB e-commerce evaluation project.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (
    auth,
    users,
    categories,
    suppliers,
    products,
    addresses,
    carts,
    orders,
    payments,
    reviews,
    analytics,
):
    app.include_router(module.router, prefix="/api")


@app.get("/api/health")
def health():
    """Ping MongoDB and report connectivity."""
    try:
        get_db().command("ping")
        return {"status": "ok", "database": "connected"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "database": "unreachable", "detail": str(exc)}


# Serve the static frontend (so `uvicorn` alone runs the whole stack).
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def index():
        return FileResponse(FRONTEND_DIR / "index.html")
