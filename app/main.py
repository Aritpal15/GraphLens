import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.config.settings import settings
from app.pipeline import GraphLensPipeline

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize and load pipeline indices on startup
    logger.info("Initializing GraphLensPipeline...")
    pipeline = GraphLensPipeline()
    pipeline.build_or_load_indices()
    app.state.pipeline = pipeline
    logger.info("GraphLensPipeline initialized and attached to app.state.")
    yield
    logger.info("Shutting down GraphLens API...")


app = FastAPI(
    title="GraphLens API",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app/api/routes.py already defines prefix="/api/v1"
app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}