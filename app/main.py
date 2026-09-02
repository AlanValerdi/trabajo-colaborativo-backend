from fastapi import FastAPI

from app.routers import user as user_router

app = FastAPI(title="servicio-trabajo-colaborativo")

app.include_router(user_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}
