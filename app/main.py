from fastapi import FastAPI
from app.api.v1.api_router import api_router
from app.routers import admin, webhooks
from app.db.database import init_db

app = FastAPI(title="ModaMasal AI Backend")

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(api_router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(webhooks.router, prefix="/api/v1", tags=["webhooks"])

@app.get("/")
async def root():
    return {"message": "ModaMasal AI Backend is running"}
