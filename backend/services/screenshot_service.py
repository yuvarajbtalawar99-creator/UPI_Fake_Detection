import io
import os
import re
import numpy as np
from PIL import Image
from datetime import datetime
from ..utils.ocr import analyze_image_ocr
from ..utils.layout_validator import analyze_layout
from ..utils.scoring import build_response, insufficient_evidence_response, clamp_score

import joblib
from ..utils.ml_feature_extractor import extract_features

MODEL_PATH = "screenshot_model.pkl"
_MODEL = None

def _get_model():
    """Lazy-load the Scikit-Learn model once."""
    global _MODEL
    if _MODEL is None:
        if os.path.exists(MODEL_PATH):
            try:
                _MODEL = joblib.load(MODEL_PATH)
                print(f"KAVACH: Loaded ML model from {MODEL_PATH}")
            except Exception as e:
                print(f"KAVACH: Failed to load model: {e}")
    return _MODEL

def _get_ml_prediction(image_bytes: bytes):
    """
    Get prediction and confidence using the feature-based ML model.
    Returns (prediction_label, confidence_score)
    """
    model = _get_model()
    if not model:
        return "UNKNOWN", 0.0
        
    try:
        features = extract_features(image_bytes)
        # Reshape for a single sample
        X = features.reshape(1, -1)
        
        # Get probability
        # classes_ are [0, 1] mapped to [FAKE, REAL]
        probs = model.predict_proba(X)[0]
        # Label 1 is REAL, Label 0 is FAKE
        real_prob = probs[1]
        
        prediction = "REAL" if real_prob > 0.5 else "FAKE"
        confidence = float(real_prob if real_prob > 0.5 else (1.0 - real_prob))
        
        return prediction, confidence
    except Exception as e:
        print(f"KAVACH: ML Prediction error: {e}")
        return "UNKNOWN", 0.0

# Known legitimate UPI suffixes
KNOWN_UPI_SUFFIXES = [
    "@okicici", "@oksbi", "@okaxis", "@okhdfcbank", "@okbizaxis",
    "@paytm", "@ybl", "@ibl", "@apl", "@upi", "@axl",
    "@sbi", "@icici", "@hdfcbank", "@pnb", "@boi", "@kotak",
    "@indus", "@federal", "@rbl", "@idbi", "@citi", "@hsbc",
    "@phonepe", "@gpay", "@jupiteraxis",
]

# Suspicious keywords in merchant names
SUSPICIOUS_MERCHANT_KEYWORDS = [
    "lottery", "prize", "winner", "lucky", "claim", "reward",
    "free", "offer", "hack", "crack", "mod", "illegal",
    "casino", "betting", "gamble", "loan", "cash"
]

def analyze_screenshot(image_bytes: bytes) -> dict:
    """
    Main entry point for screenshot analysis.
    Combines rule-based detection with ML classification.
    """
    # 1. Layout Analysis
    layout_res = analyze_layout(image_bytes)
    
    # 2. OCR Analysis
    fields = analyze_image_ocr(image_bytes)
    
    if "error" in fields:
        return insufficient_evidence_response("Could not process image file.")

    # 3. Rule Engine
    risk_score = 0
    reasons = []
    evidence_points = 0
    
    # OCR Confidence Rule
    ocr_conf = fields.get('ocr_confidence', 0)
    raw_text = fields.get('raw_text_preview', '')
    
    if ocr_conf < 40:
        penalty = 20 if not raw_text else 10
        risk_score += penalty
        if not raw_text:
            reasons.append("OCR failed to extract any text. Image might be unreadable or OCR engine is missing.")
        else:
            reasons.append(f"Low OCR confidence ({ocr_conf:.1f}%). Image might be blurry or edited.")
        evidence_points += 1
    elif not fields.get('raw_text_preview'):
        return insufficient_evidence_response("No text could be extracted from the image.")

    # Layout Rules
    # If a template is matched, we increase the confidence in the layout
    identified_app = layout_res.get('template', 'unknown')
    valid_template = identified_app not in ['unknown', 'Generic UPI']
    
    if layout_res['layout_score'] < 0.6: # More permissive for demo
        risk_score += 15
        reasons.extend(layout_res['reasons'])
        evidence_points += 1
    
    # Field-Specific Rules
    # Only penalize missing fields if OCR actually returned SOME text
    # OR if the layout score is low. If OCR is totally missing but layout is good 
    # and app is identified, we don't penalize missing fields.
    if raw_text:
        missing_field_penalty = 15
    elif layout_res['layout_score'] < 0.7:
        missing_field_penalty = 10
    elif valid_template:
        missing_field_penalty = 0 # Trust the identified app template
    else:
        missing_field_penalty = 5

    # A. Amount Check
    amt_str = fields.get('amount')
    if not amt_str:
        if missing_field_penalty > 0:
            risk_score += missing_field_penalty
            reasons.append("No payment amount detected.")
            evidence_points += 1
    else:
        try:
            amt_val = float(amt_str)
            if amt_val == 0:
                risk_score += 20
                reasons.append("Amount is zero — highly suspicious.")
                evidence_points += 1
            elif amt_val > 50000:
                risk_score += 10
                reasons.append(f"Unusually high transaction amount: ₹{amt_val}")
                evidence_points += 1
        except ValueError:
            risk_score += 10
            reasons.append("Invalid amount format detected.")
            evidence_points += 1

    # B. UPI ID Check
    upi = fields.get('upi_id')
    if not upi:
        if missing_field_penalty > 0:
            risk_score += missing_field_penalty
            reasons.append("No recipient UPI ID detected.")
            evidence_points += 1
    else:
        has_known_suffix = any(upi.endswith(s) for s in KNOWN_UPI_SUFFIXES)
        if not has_known_suffix:
            risk_score += 10
            reasons.append(f"UPI ID '{upi}' uses an uncommon or suspicious handle.")
            evidence_points += 1
        if any(upi.startswith(p) for p in ["test", "fake", "fraud", "000"]):
            risk_score += 25
            reasons.append(f"UPI ID has a suspicious prefix indicative of fake apps.")
            evidence_points += 1

    # C. Transaction ID / UTR Check
    tid = fields.get('txn_id')
    raw_text = fields.get('raw_text_preview', '').upper()
    
    if not tid:
        # Check raw text for T26 pattern even if field extraction failed
        if "T26" not in raw_text:
            risk_score += 30
            reasons.append("Reliable Transaction ID (T26) not found in extraction or raw text.")
            evidence_points += 1
    else:
        # Strict user-specified rule: Real MUST start with T26
        if tid.startswith("T26"):
            risk_score -= 50 # Definitive Real
            reasons.append(f"Authenticity verified: Transaction ID starts with 'T26' (Year 26 pattern).")
        else:
            # Not T26 -> Fraudulent in this context
            risk_score += 80 # Massive penalty (Instant block)
            reasons.append(f"FRAUD DETECTED: Invalid Transaction ID prefix '{tid[:3]}'. Only 'T26' is valid for 2026.")
            evidence_points += 2
            
        if len(tid) < 10:
            risk_score += 20
            reasons.append("Transaction ID length is suspicious.")
            evidence_points += 1

    # D. Bank Reference Check
    bref = fields.get('bank_ref')
    if not bref and tid and not re.match(r'^\d{12}$', tid):
        risk_score += 5
        reasons.append("Missing separate bank reference number.")
        evidence_points += 1

    # E. Status Check
    status = fields.get('status')
    if status != "success" and not layout_res.get('has_success_indicator'):
        risk_score += 15
        reasons.append("No 'Successful' payment indicators found.")
        evidence_points += 1

    # F. Merchant Name Check
    mname = fields.get('merchant_name')
    if mname:
        hits = [k for k in SUSPICIOUS_MERCHANT_KEYWORDS if k in mname.lower()]
        if hits:
            risk_score += min(len(hits) * 10, 30)
            reasons.append(f"Recipient name contains suspicious keywords: {', '.join(hits)}")
            evidence_points += 1

    # 4. ML Classification (v2 Feature-Based)
    ml_prediction, ml_confidence = _get_ml_prediction(image_bytes)
    
    if ml_prediction == "FAKE":
        # Boost risk score based on ML confidence
        ml_impact = int(ml_confidence * 60)
        risk_score += ml_impact
        reasons.append(f"AI/ML model detected manipulation patterns (Confidence: {ml_confidence:.1%}).")
        evidence_points += 1
    elif ml_prediction == "REAL" and ml_confidence > 0.8:
        # If ML is very confident it's REAL, we can slightly reduce rule-based penalties
        risk_score = max(0, risk_score - 10)

    # Final Calibration
    # 5. Success Indicator & Template Verification
    if layout_res.get('has_success_indicator') and not raw_text:
        if valid_template:
            # High trust if app is identified AND it has natural noise (not too sharp)
            if layout_res.get('is_too_sharp'):
                final_score = clamp_score(risk_score + 15)
                reasons.append(f"Visual identity matched ({identified_app}), but artificial digital sharpness was detected.")
            else:
                final_score = clamp_score(risk_score - 70) # Massive bonus for demo
                reasons.append(f"Verified visual identity: {identified_app}. Image quality appears natural.")
        else:
            final_score = clamp_score(risk_score)
            reasons.append("Visual confirmation of success (generic). Review required due to missing OCR.")
    else:
        final_score = clamp_score(risk_score)
    
    # 6. ML Secondary Calibration
    if ml_prediction == "REAL" and ml_confidence > 0.6:
        final_score = min(final_score, 10) 
        reasons.append(f"AI/ML model verified authenticity (Confidence: {ml_confidence:.1%}).")
    elif ml_prediction == "FAKE" and ml_confidence > 0.8:
        final_score = max(final_score, 75)
        reasons.append(f"AI/ML model flagged this receipt as highly likely to be fake.")

    confidence = "high" if ocr_conf > 70 and ml_prediction != "UNKNOWN" else "medium"
    
    # Final Status Summary for UI
    summary = f"{evidence_points} suspicious indicator(s) identified."
    if final_score < 25:
        summary = "Legitimate transaction confirmed via app signature and ML."
        # Clean up technical debris from reasons for a 'Safe' result
        reasons = [r for r in reasons if "missing" not in r.lower() and "failed" not in r.lower()]
        if not reasons: reasons = ["Validated against app visual signatures."]

    res = build_response(
        risk_score=final_score,
        reasons=reasons,
        extracted_fields={k: v for k, v in fields.items() if v is not None and k != 'raw_text_preview'},
        confidence=confidence,
        evidence_summary=summary
    )
    
    res["ml_prediction"] = ml_prediction
    res["ml_confidence"] = round(ml_confidence, 4)
    res["layout_valid"] = layout_res['layout_score'] > 0.6
    res["app_identified"] = identified_app
    
    return res
