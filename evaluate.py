# -*- coding: utf-8 -*-
"""
KAVACH Evaluation Pipeline.
Tests the fraud detection services against the labeled dataset.
"""

import os
import sys
import argparse
from typing import List, Dict

# Add backend to path so we can import services
sys.path.append(os.getcwd())

# Import services (mocking FastAPI app context)
from backend.services.screenshot_service import analyze_screenshot
from backend.services.qrcode_service import analyze_qrcode
from backend.services.url_service import analyze_url

try:
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False

def load_urls(file_path: str) -> List[str]:
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def evaluate_url_detector():
    print("\n--- Evaluating URL Phishing Detector ---")
    safe_urls = load_urls('data/urls/safe.txt')
    fake_urls = load_urls('data/urls/fake.txt')
    
    if not safe_urls and not fake_urls:
        print("No URL data found in data/urls/")
        return
    
    y_true = []
    y_pred = []
    
    # Label 0: Safe, 1: Blocked (Fraud)
    
    for url in safe_urls:
        res = analyze_url(url)
        y_true.append(0)
        y_pred.append(1 if res['status'] == 'blocked' else 0)
        
    for url in fake_urls:
        res = analyze_url(url)
        y_true.append(1)
        y_pred.append(1 if res['status'] == 'blocked' else 0)
        
    print_metrics(y_true, y_pred)

def evaluate_image_detector(folder_real: str, folder_fake: str, detector_func, name: str):
    print(f"\n--- Evaluating {name} Detector ---")
    
    y_true = []
    y_pred = []
    
    if not os.path.exists(folder_real) or not os.path.exists(folder_fake):
        print(f"Folders {folder_real} or {folder_fake} missing.")
        return

    # Process Real
    files_real = [f for f in os.listdir(folder_real) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    for fn in files_real:
        with open(os.path.join(folder_real, fn), 'rb') as f:
            res = detector_func(f.read())
            y_true.append(0)
            y_pred.append(1 if res['status'] in ['blocked', 'suspicious'] else 0)
            
    # Process Fake
    files_fake = [f for f in os.listdir(folder_fake) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    for fn in files_fake:
        with open(os.path.join(folder_fake, fn), 'rb') as f:
            res = detector_func(f.read())
            y_true.append(1)
            # For fake data, we count both 'blocked' and 'suspicious' as a successful catch
            y_pred.append(1 if res['status'] in ['blocked', 'suspicious'] else 0)
            
    if not y_true:
        print(f"No image data found in {folder_real} or {folder_fake}")
        return
        
    print_metrics(y_true, y_pred)

def print_metrics(y_true, y_pred):
    if not _HAS_SKLEARN:
        # Simple manual calculation if sklearn is missing
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
        tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
        
        acc = (tp + tn) / len(y_true) if y_true else 0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        print(f"Accuracy:  {acc:.2f}")
        print(f"Precision: {prec:.2f}")
        print(f"Recall:    {rec:.2f}")
        print(f"TP: {tp}, TN: {tn}, FP: {fp}, FN: {fn}")
    else:
        print(f"Accuracy:  {accuracy_score(y_true, y_pred):.2f}")
        print(f"Precision: {precision_score(y_true, y_pred, zero_division=0):.2f}")
        print(f"Recall:    {recall_score(y_true, y_pred, zero_division=0):.2f}")
        print(f"F1-Score:  {f1_score(y_true, y_pred, zero_division=0):.2f}")
        print("Confusion Matrix:")
        print(confusion_matrix(y_true, y_pred))

if __name__ == "__main__":
    print("KAVACH (Real-Time Scam Shield) - Evaluation Script")
    
    # 1. URLs
    evaluate_url_detector()
    
    # 2. QR Codes
    evaluate_image_detector('data/qr/safe', 'data/qr/fake', analyze_qrcode, "QR")
    
    # 3. Screenshots
    evaluate_image_detector('data/screenshots/real', 'data/screenshots/fake', analyze_screenshot, "Screenshot")
