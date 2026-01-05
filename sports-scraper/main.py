from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import health, api, training_data, populate
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title=settings.app_name,
    description="A FastAPI wrapper for SportAI services with MongoDB document database",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - Only training_data and populate routers for LLM training data
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(api.router, prefix="/api/v1", tags=["api"])
app.include_router(training_data.router, prefix="/training-data", tags=["training-data"])
app.include_router(populate.router, prefix="/populate", tags=["population"])

@app.get("/")
async def root():
    return {"message": "Welcome to SportAI API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
