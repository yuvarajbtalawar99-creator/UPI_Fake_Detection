# -*- coding: utf-8 -*-
"""API router for UPI payment screenshot analysis."""

from fastapi import APIRouter, UploadFile, File
from ..services.screenshot_service import analyze_screenshot

router = APIRouter(prefix="/api/screenshot", tags=["Screenshot"])


@router.post("/analyze")
async def analyze_screenshot_endpoint(file: UploadFile = File(...)):
    """
    Upload a UPI payment screenshot for fraud analysis.

    Returns risk_score (0-100), status, extracted_fields, and reasons.
    """
    image_bytes = await file.read()
    result = analyze_screenshot(image_bytes)
    return result
