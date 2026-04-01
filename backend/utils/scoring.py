# -*- coding: utf-8 -*-
"""
Unified scoring and response standardization utility for KAVACH.
"""

def clamp_score(score: float) -> int:
    """Clamp score to [0, 100] range."""
    return max(0, min(100, int(score)))

def score_to_status(score: int) -> str:
    """Convert a 0-100 risk score to a human-readable status."""
    if score <= 35:
        return "safe"
    elif score <= 65:
        return "suspicious"
    else:
        return "blocked"

def build_response(risk_score: int, reasons: list, extracted_fields: dict = None, confidence: str = "medium", evidence_summary: str = "") -> dict:
    """
    Build a standardized API response dictionary.
    
    Args:
        risk_score: 0-100 risk score
        reasons: List of strings explaining the risk score
        extracted_fields: Dict of key data extracted (UPI ID, amount, etc.)
        confidence: "low", "medium", or "high"
        evidence_summary: Short string summarizing the evidence (e.g. "2 indicators found")
        
    Returns:
        Standardized response dict compatible with existing frontend result display.
    """
    status = score_to_status(risk_score)
    
    # If no useful evidence was found and risk is low, mark as insufficient evidence if appropriate.
    # Note: If analysis explicitly fails, this status can be overridden.
    
    return {
        "risk_score": risk_score,
        "status": status,
        "confidence": confidence,
        "reasons": reasons if reasons else ["No suspicious indicators found."],
        "extracted_fields": extracted_fields or {},
        "evidence_summary": evidence_summary or f"{len(reasons)} point(s) of analysis noted."
    }

def insufficient_evidence_response(message: str = "Insufficient evidence to perform analysis.") -> dict:
    """Return a response when OCR or decoding fails completely."""
    return {
        "risk_score": 0,
        "status": "insufficient_evidence",
        "confidence": "low",
        "reasons": [message],
        "extracted_fields": {},
        "evidence_summary": "Analysis could not be completed."
    }
