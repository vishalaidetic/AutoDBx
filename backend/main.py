import os
from typing import Any, Dict, Optional

from api.routes import router as autodbx_router
from api.websockets.migration import ws_router as migration_ws_router
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from utils.cors import setup_cors

load_dotenv()
app = FastAPI(title="AutoDBx", version="1.0.0")

# Setup CORS middleware
setup_cors(app)

app.include_router(migration_ws_router)
app.include_router(autodbx_router, prefix="/api")


@app.get("/")
async def read_root():
    return {"status": "ok", "message": "Welcome to AutoDBx Backend!"}
