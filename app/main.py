from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

register_routers(app)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
