# -*- coding: utf-8 -*-
"""
KAVACH – Real Time Scam Shield for Rural India
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .routers import screenshot, qrcode, url
from .utils.translations import get_all_translations

# Resolve paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = FastAPI(
    title="KAVACH – Real Time Scam Shield",
    description="Real-time fraud detection for UPI payments, QR codes, and suspicious URLs.",
    version="1.0.0",
)

# CORS — allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(screenshot.router)
app.include_router(qrcode.router)
app.include_router(url.router)


# Translation endpoint
@app.get("/api/translations/{lang}")
async def get_translations(lang: str):
    """Get all UI translations for a given language code (en, hi, kn, mr)."""
    return get_all_translations(lang)


# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": "KAVACH"}


# Mount frontend static files
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    # Serve PWA files from frontend root
    @app.get("/manifest.json")
    async def serve_manifest():
        return FileResponse(os.path.join(FRONTEND_DIR, "manifest.json"))

    @app.get("/sw.js")
    async def serve_sw():
        return FileResponse(
            os.path.join(FRONTEND_DIR, "sw.js"),
            media_type="application/javascript",
        )

    # Serve index.html for all non-API routes (SPA fallback)
    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # If the file exists in frontend dir, serve it
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # Otherwise, serve index.html (SPA routing)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
