from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from backend.database import init_db
from backend.routers import upload, startup, mandate
from backend.routers.evaluate import router as evaluate_router
from backend.routers.ocr import router as ocr_router
from backend.routers.debug import router as debug_router
from backend.monitor.routes.monitor_routes import router as monitor_router
from backend.synergy.routes.synergy_routes import router as synergy_router
from backend.agents.ollama_client import check_ollama_available


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("uploads", exist_ok=True)
    await init_db()
    yield


app = FastAPI(title="ConvictAI API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(startup.router, prefix="/api")
app.include_router(mandate.router, prefix="/api")
app.include_router(evaluate_router, prefix="/api")
app.include_router(ocr_router, prefix="/api")
app.include_router(debug_router, prefix="/api")
app.include_router(monitor_router, prefix="/api")
app.include_router(synergy_router, prefix="/api")


@app.get("/api/health")
async def health():
    ollama_ok = await check_ollama_available()
    return {"status": "ok", "service": "ConvictAI", "ollama": ollama_ok}
