# -*- coding: utf-8 -*-
"""
Enhanced QR Code analysis service for KAVACH.
Decodes QR codes with multiple passes and validates UPI payment data.
"""

import re
from urllib.parse import urlparse, parse_qs
import numpy as np
import cv2
from ..utils.scoring import build_response, insufficient_evidence_response, clamp_score, score_to_status
from ..utils.ml_classifier import refine_with_ml

# Try importing QR decoding libraries
# Catches OSError/FileNotFoundError on Windows when libzbar-64.dll is missing
try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    _HAS_PYZBAR = True
except (ImportError, OSError, FileNotFoundError):
    _HAS_PYZBAR = False


# ---------------------------------------------------------------------------
# Trusted UPI Processors (legitimate bank handles)
# These are NEVER flagged — even alone they indicate a safe transaction.
# ---------------------------------------------------------------------------
TRUSTED_UPI_PROCESSORS = [
    "@okicici", "@oksbi", "@okaxis", "@okhdfcbank",
    "@paytm", "@ybl", "@ibl", "@apl", "@upi", "@axl",
    "@sbi", "@icici", "@hdfcbank", "@pnb", "@boi", "@kotak",
    "@indus", "@federal", "@rbl", "@idbi", "@citi", "@hsbc",
    "@phonepe", "@gpay", "@jupiteraxis",
]

# ---------------------------------------------------------------------------
# Explicitly suspicious handles — confirmed scam patterns
# ---------------------------------------------------------------------------
SUSPICIOUS_HANDLES = [
    "@okbizaxis", "@okbiz", "@bizaxis", "@fastpay", "@quickupi",
    "@securepay", "@instantpay", "@safepay",
]

# Generic/Placeholder merchant names often used in fake QRs
GENERIC_MERCHANT_NAMES = [
    "unknown store", "merchant", "shop", "generic merchant",
    "test store", "payment recipient", "user", "customer",
    "retailer", "vendor", "store", "business",
]

# Suspicious keywords in merchant names
SUSPICIOUS_MERCHANT_KEYWORDS = [
    "lottery", "prize", "winner", "lucky", "claim", "reward",
    "free", "offer", "hack", "crack", "mod", "illegal",
    "casino", "betting", "gamble", "kyc", "refund", "bonus",
]


def _decode_qr_multi_pass(img) -> str:
    """Try to decode QR code using multiple image processing passes."""
    detector = cv2.QRCodeDetector()

    # Pass 1: Original
    if _HAS_PYZBAR:
        decoded = pyzbar_decode(img)
        if decoded:
            return decoded[0].data.decode("utf-8", errors="ignore")

    data, _, _ = detector.detectAndDecode(img)
    if data:
        return data

    # Pass 2: Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if _HAS_PYZBAR:
        decoded = pyzbar_decode(gray)
        if decoded:
            return decoded[0].data.decode("utf-8", errors="ignore")

    data, _, _ = detector.detectAndDecode(gray)
    if data:
        return data

    # Pass 3: Threshold
    _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    if _HAS_PYZBAR:
        decoded = pyzbar_decode(thresh)
        if decoded:
            return decoded[0].data.decode("utf-8", errors="ignore")

    data, _, _ = detector.detectAndDecode(thresh)
    return data or ""


def _parse_upi_uri(text: str) -> dict:
    """Parse a UPI payment URI and extract parameters."""
    text = text.strip()
    if not (text.lower().startswith("upi://pay") or text.lower().startswith("upi://")):
        return {"is_upi": False}

    try:
        parsed = urlparse(text)
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        return {
            "is_upi": True,
            "pa": params.get("pa", ""),   # VPA (UPI ID)
            "pn": params.get("pn", ""),   # Payee Name
            "am": params.get("am", ""),   # Amount
            "cu": params.get("cu", "INR"),# Currency
            "tn": params.get("tn", ""),   # Transaction Note
            "mc": params.get("mc", ""),   # Merchant Code
            "tr": params.get("tr", ""),   # Transaction Ref
        }
    except Exception:
        return {"is_upi": False}


def _extract_processor(upi_id: str) -> str:
    """Extract the @handle processor from a UPI ID."""
    if "@" in upi_id:
        return "@" + upi_id.split("@", 1)[1]
    return ""


def analyze_qrcode(image_bytes: bytes) -> dict:
    """
    Analyze a QR code image for fraudulent UPI payment data.
    
    Philosophy: High-confidence red flags (phishing URLs, suspicious handles)
    result in 80-90% risk.  Trusted patterns are kept safe.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return insufficient_evidence_response("Could not decode image file.")

    decoded_text = _decode_qr_multi_pass(img)
    if not decoded_text:
        return insufficient_evidence_response("No QR code detected in the image.")

    upi_data = _parse_upi_uri(decoded_text)

    risk_score = 0
    reasons = []
    evidence_points = 0

    # ------------------------------------------------------------------
    # Non-UPI content (URLs, random text, malformed URIs)
    # ------------------------------------------------------------------
    if not upi_data.get("is_upi"):
        if decoded_text.startswith("http"):
            risk_score += 95
            reasons.append("CRITICAL BLOCK: QR code contains a hidden phishing link instead of a secure payment address. This is a common method used to steal banking details.")
            evidence_points += 1
        else:
            risk_score += 90
            reasons.append("CRITICAL ALERT: Malformed payment data detected. This QR code does NOT contain a valid UPI payment address.")
            evidence_points += 1

        final_score = clamp_score(risk_score)
        return {
            "risk_score": final_score,
            "status": score_to_status(final_score),
            "payment_to": "",
            "payee_name": "",
            "amount": "",
            "processor": "",
            "upi_uri": "",
            "confidence": "high",
            "reasons": reasons,
            "extracted_fields": {"raw_data": decoded_text[:200]},
            "evidence_summary": "Dangerous non-UPI content detected.",
        }

    # ------------------------------------------------------------------
    # UPI Fraud Detection Rules
    # ------------------------------------------------------------------
    pa = upi_data.get("pa", "")
    pn = upi_data.get("pn", "")
    am = upi_data.get("am", "")
    mc = upi_data.get("mc", "")
    processor = _extract_processor(pa)

    # Flags for baseline safety
    is_suspicious_handle = False
    is_domain_like = False
    has_high_risk_keyword = False
    has_suspicious_prefix = False

    # Rule 1: Missing or invalid UPI ID (critical)
    if not pa:
        risk_score += 85
        reasons.append("HIGH RISK: Missing recipient information in QR code.")
        evidence_points += 1
    elif "@" not in pa:
        risk_score += 85
        reasons.append(f"HIGH RISK: Invalid payment address format ('{pa}'). Legitimate payments require a '@' handle.")
        evidence_points += 1
    else:
        # Check handle against known lists
        is_trusted = any(pa.lower().endswith(s) for s in TRUSTED_UPI_PROCESSORS)
        is_suspicious_handle = any(pa.lower().endswith(s) for s in SUSPICIOUS_HANDLES)

        if is_suspicious_handle:
            risk_score += 90
            reasons.append(f"BLOCK RECOMMENDED: Confirmed scam handle '{processor}' detected. This handle has been flagged for financial fraud.")
            evidence_points += 1
        elif not is_trusted:
            # Unknown processor — significant risk unless merchant is validated
            risk_score += 50
            reasons.append(f"Security Alert: This payment uses an unrecognized bank handle '{processor}'. Scammers often use custom handles to bypass security.")
            evidence_points += 1

        # Suspicious prefix (test/fake/fraud/000)
        if any(pa.lower().startswith(p) for p in ["test", "fake", "fraud", "000", "xxx"]):
            has_suspicious_prefix = True
            risk_score += 90
            reasons.append(f"BLOCK RECOMMENDED: Payment address uses a fraudulent prefix ('{pa[:4]}') common in scam operations.")
            evidence_points += 1

        # Domain-like handle (e.g. @paypal.com)
        if "." in processor:
            is_domain_like = True
            risk_score += 85
            reasons.append(f"SCAM RISK: The handle '{processor}' mimics a website to deceive users. Official UPI handles do not use domain extensions.")
            evidence_points += 1

    # Rule 2: Payee name analysis
    if not pn:
        risk_score += 50
        reasons.append("Security Warning: Merchant name is missing. Scammers often hide their identity by removing the name from the QR code.")
        evidence_points += 1
    else:
        pn_lower = pn.lower().strip()
        # Check for generic names
        is_generic = any(pn_lower == g for g in GENERIC_MERCHANT_NAMES) or \
                     any(pn_lower == f"{g} {i}" for g in GENERIC_MERCHANT_NAMES for i in range(100))
        
        if is_generic:
            risk_score += 45
            reasons.append(f"Security Alert: Generic merchant name '{pn}' detected. Legitimate businesses usually provide their official registered name.")
            evidence_points += 1

        hits = [k for k in SUSPICIOUS_MERCHANT_KEYWORDS if k in pn_lower]
        if hits:
            has_high_risk_keyword = True
            risk_score += 90
            reasons.append(f"BLOCK RECOMMENDED: The name '{pn}' uses scam keywords ({', '.join(hits)}) to lure users.")
            evidence_points += 1

    # Rule 3: Amount anomalies
    if am:
        try:
            val = float(am)
            if val > 100000:
                risk_score += 30
                reasons.append(f"Caution: QR is requesting a very high amount (₹{val:,.2f}).")
                evidence_points += 1
            elif val <= 0:
                risk_score += 20
                reasons.append("Alert: Requested payment amount is invalid.")
                evidence_points += 1
        except ValueError:
            risk_score += 15
            reasons.append("Alert: Payment amount format is incorrect.")
            evidence_points += 1

    # Rule 4: Personal UPI used as merchant (high value, no merchant code)
    if not mc and am:
        try:
            if float(am) > 5000:
                risk_score += 15
                reasons.append("Note: High-value payment to a personal account instead of a registered merchant.")
                evidence_points += 1
        except ValueError:
            pass

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Safe-baseline: if pa is valid AND pn exists AND processor is trusted,
    # AND NO major red flags are triggered.
    # ------------------------------------------------------------------
    has_valid_pa = pa and "@" in pa
    has_pn = bool(pn)
    is_trusted_processor = any(pa.lower().endswith(s) for s in TRUSTED_UPI_PROCESSORS) if has_valid_pa else False
    
    major_red_flags = is_suspicious_handle or is_domain_like or has_high_risk_keyword or has_suspicious_prefix or not has_valid_pa

    if has_valid_pa and has_pn and is_trusted_processor and not major_red_flags:
        risk_score = min(risk_score, 20)
    
    # If multiple risks are detected, significantly increase the score
    if evidence_points >= 2 and risk_score < 90:
        if not is_trusted_processor or not has_pn:
            risk_score = max(risk_score, 95)
            reasons.append("BLOCK RECOMMENDED: Multiple structural anomalies detected. This QR code follows confirmed theft patterns.")

    # ------------------------------------------------------------------
    # Build final response
    # ------------------------------------------------------------------
    final_score = clamp_score(risk_score)
    summary = f"{evidence_points} risk factor(s) identified."
    
    if final_score <= 35:
        summary = "Verified Safe: This QR code matches trusted merchant patterns."
        reasons = ["Validated successfully against KAVACH security standards."]

    base_response = {
        "risk_score": final_score,
        "status": score_to_status(final_score),
        "payment_to": pa,
        "payee_name": pn,
        "amount": am,
        "processor": processor,
        "upi_uri": decoded_text.strip() if score_to_status(final_score) == "safe" else "",
        "confidence": "high",
        "reasons": reasons,
        "extracted_fields": {
            k: v for k, v in {
                "UPI ID": pa,
                "Payee Name": pn,
                "Amount": f"₹{am}" if am else "",
                "Processor": processor,
                "Currency": upi_data.get("cu", ""),
                "Transaction Note": upi_data.get("tn", ""),
                "Merchant Code": mc,
            }.items() if v
        },
        "evidence_summary": summary,
    }

    # Optional ML refinement
    refined_score = refine_with_ml(final_score, base_response)
    base_response["risk_score"] = refined_score
    base_response["status"] = score_to_status(refined_score)

    if base_response["status"] != "safe":
        base_response["upi_uri"] = ""

    return base_response
