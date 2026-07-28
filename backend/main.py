import os
import sys
from pathlib import Path

# Inject parent directory into sys.path to allow importing from 'backend.core...'
# regardless of whether the app is run from the workspace root or from the backend directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import logging

# Configure structured console logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("backend")
logger.info("Initializing Agentic Bug Hunter API server...")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.router import router
from backend.core.config import settings

app = FastAPI(title="Agentic Bug Hunter API", version="2.0.0")



# Setup CORS middleware with configuration settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    # Allow running directly using python main.py
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)