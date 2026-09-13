from fastapi import FastAPI

from app.urls import register_routers

app = FastAPI(title="servicio-trabajo-colaborativo")

register_routers(app)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
