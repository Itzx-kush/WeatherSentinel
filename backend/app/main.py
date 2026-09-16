from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.services.runtime import RuntimeStore

VERSION = "0.4.0"

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.runtime = RuntimeStore()
    app.state.version = VERSION
    yield

app = FastAPI(title="WeatherSentinel", version=VERSION, description="AI/ML intelligent anomaly detection for automatic weather stations", lifespan=lifespan)
app.state.runtime = RuntimeStore()
app.state.version = VERSION
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
