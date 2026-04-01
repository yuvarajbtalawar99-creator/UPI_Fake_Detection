# -*- coding: utf-8 -*-
"""API router for QR code analysis."""

from fastapi import APIRouter, UploadFile, File
from ..services.qrcode_service import analyze_qrcode

router = APIRouter(prefix="/api/qrcode", tags=["QR Code"])


@router.post("/analyze")
async def analyze_qrcode_endpoint(file: UploadFile = File(...)):
    """
    Upload a QR code image for UPI fraud analysis.

    Returns risk_score (0-100), status, decoded_data, and reasons.
    """
    image_bytes = await file.read()
    result = analyze_qrcode(image_bytes)
    return result
