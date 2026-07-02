from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api import accounts, orders, copytrader, risk
from app.dependencies import initialize_dependencies, shutdown_dependencies

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Copytrading API", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(accounts.router)
app.include_router(orders.router)
app.include_router(copytrader.router)
app.include_router(risk.router)

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    logger.info("Starting up application...")
    await initialize_dependencies()
    logger.info("Dependencies initialized")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down application...")
    await shutdown_dependencies()
    logger.info("Shutdown complete")

@app.get("/")
async def root():
    return {"message": "Copytrading API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
