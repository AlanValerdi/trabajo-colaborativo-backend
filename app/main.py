from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.urls import register_routers

app = FastAPI(title="servicio-trabajo-colaborativo")

# Configuración CORS
origins = [
    "http://localhost:4200",  # Angular por defecto
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

register_routers(app)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
