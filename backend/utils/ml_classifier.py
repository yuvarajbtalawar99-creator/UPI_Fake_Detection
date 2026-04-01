# -*- coding: utf-8 -*-
"""
Optional ML classifier helper for KAVACH.
Refines rule-based scores using a lightweight classifier.
"""

import os
import pickle
import numpy as np

# Path to the trained meta-model
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "meta_classifier.pkl")

def extract_features_from_result(res: dict) -> np.ndarray:
    """
    Extract numeric features from any standardized analysis result.
    Features:
    1. Base risk score
    2. Count of reasons
    3. Confidence (low=0, med=1, high=2)
    4. Extraction count (how many fields found)
    5. Indicator count (from evidence summary)
    """
    risk = res.get('risk_score', 0) / 100.0
    reason_count = len(res.get('reasons', []))
    
    conf_map = {"low": 0, "medium": 1, "high": 2}
    confidence = conf_map.get(res.get('confidence', 'low'), 0) / 2.0
    
    extracted_count = len(res.get('extracted_fields', {}))
    
    # Try to extract count from evidence summary (e.g. "3 indicator(s) identified")
    summary = res.get('evidence_summary', "0")
    import re
    m = re.search(r'(\d+)', summary)
    indicator_count = int(m.group(1)) if m else 0
    
    return np.array([risk, reason_count, confidence, extracted_count, indicator_count], dtype=np.float32)

def refine_with_ml(rule_score: int, service_result: dict) -> int:
    """
    Optionally refine the rule-based score using ML.
    If no model exists, returns the original score.
    """
    if not os.path.exists(MODEL_PATH):
        return rule_score
        
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
            
        features = extract_features_from_result(service_result).reshape(1, -1)
        # Assuming the model predicts a probability [0, 1]
        ml_prob = model.predict_proba(features)[0][1] 
        
        # Ensemble: 50% Rules + 50% ML
        refined = (rule_score + (ml_prob * 100)) / 2
        return int(refined)
    except Exception:
        return rule_score

def save_model(model):
    """Save a trained scikit-learn model."""
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
