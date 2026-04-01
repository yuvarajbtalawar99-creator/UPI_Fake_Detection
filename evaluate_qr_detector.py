# -*- coding: utf-8 -*-
"""
KAVACH - QR Code Detector Evaluation Script
Runs the QR fraud detection engine against the labeled dataset
and reports accuracy, precision, recall, F1-score, and confusion matrix.

Usage:
    python evaluate_qr_detector.py
    python evaluate_qr_detector.py --safe datasets/qr/safe --fake datasets/qr/fake
"""

import io
import sys
# Ensure stdout handles unicode on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import argparse

# Add project root to path
sys.path.insert(0, os.getcwd())

from backend.services.qrcode_service import analyze_qrcode

try:
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score,
        f1_score, confusion_matrix, classification_report,
    )
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False


def load_images(folder: str) -> list:
    """Load all image file paths from a directory."""
    if not os.path.isdir(folder):
        return []
    exts = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
    return sorted([
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(exts)
    ])


def run_detection(image_path: str) -> dict:
    """Run the QR detector on a single image."""
    with open(image_path, 'rb') as f:
        return analyze_qrcode(f.read())


def evaluate(safe_dir: str, fake_dir: str):
    """Evaluate the detector against the labeled dataset."""
    safe_images = load_images(safe_dir)
    fake_images = load_images(fake_dir)

    if not safe_images and not fake_images:
        print(f"ERROR: No images found.\n  Safe dir: {safe_dir}\n  Fake dir: {fake_dir}")
        return

    print(f"Dataset loaded:")
    print(f"  Safe samples : {len(safe_images)}")
    print(f"  Fake samples : {len(fake_images)}")
    print(f"  Total        : {len(safe_images) + len(fake_images)}\n")

    y_true = []
    y_pred = []
    details = {"tp": [], "fp": [], "tn": [], "fn": []}

    # Process safe images (expected label = 0 = safe)
    print("Processing safe samples...")
    for path in safe_images:
        res = run_detection(path)
        y_true.append(0)
        pred = 1 if res.get("status") in ("blocked", "suspicious") else 0
        y_pred.append(pred)
        key = "fp" if pred == 1 else "tn"
        details[key].append((os.path.basename(path), res.get("risk_score"), res.get("status")))

    # Process fake images (expected label = 1 = fraud)
    print("Processing fake samples...")
    for path in fake_images:
        res = run_detection(path)
        y_true.append(1)
        pred = 1 if res.get("status") in ("blocked", "suspicious") else 0
        y_pred.append(pred)
        key = "tp" if pred == 1 else "fn"
        details[key].append((os.path.basename(path), res.get("risk_score"), res.get("status")))

    # ---- Print Results ----
    print("\n" + "=" * 60)
    print("  KAVACH QR CODE DETECTOR — EVALUATION RESULTS")
    print("=" * 60)

    if _HAS_SKLEARN:
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        print(f"\n  Accuracy  : {acc:.4f} ({acc*100:.1f}%)")
        print(f"  Precision : {prec:.4f}")
        print(f"  Recall    : {rec:.4f}")
        print(f"  F1-Score  : {f1:.4f}")
        print(f"\n  Confusion Matrix:")
        cm = confusion_matrix(y_true, y_pred)
        print(f"                  Predicted Safe  Predicted Fraud")
        print(f"  Actual Safe   :   {cm[0][0]:>8}        {cm[0][1]:>8}")
        print(f"  Actual Fraud  :   {cm[1][0]:>8}        {cm[1][1]:>8}")
        print(f"\n  Classification Report:")
        print(classification_report(y_true, y_pred, target_names=["Safe", "Fraud"], zero_division=0))
    else:
        # Manual calculation
        tp = len(details["tp"])
        tn = len(details["tn"])
        fp = len(details["fp"])
        fn = len(details["fn"])
        total = tp + tn + fp + fn

        acc = (tp + tn) / total if total > 0 else 0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0

        print(f"\n  Accuracy  : {acc:.4f} ({acc*100:.1f}%)")
        print(f"  Precision : {prec:.4f}")
        print(f"  Recall    : {rec:.4f}")
        print(f"  F1-Score  : {f1:.4f}")
        print(f"\n  Confusion Matrix:")
        print(f"  TP: {tp}  |  FP: {fp}")
        print(f"  FN: {fn}  |  TN: {tn}")

    # ---- Misclassifications ----
    if details["fp"]:
        print(f"\n  [!] False Positives ({len(details['fp'])} safe images flagged as fraud):")
        for name, score, status in details["fp"][:10]:
            print(f"    - {name}  (score={score}, status={status})")

    if details["fn"]:
        print(f"\n  [!] False Negatives ({len(details['fn'])} fake images missed):")
        for name, score, status in details["fn"][:10]:
            print(f"    - {name}  (score={score}, status={status})")

    if details["tp"]:
        print(f"\n  [*] Score Distribution for Correctly Blocked Scams (TP):")
        scores = [s[1] for s in details["tp"]]
        print(f"    - Min Score: {min(scores)}")
        print(f"    - Max Score: {max(scores)}")
        print(f"    - Avg Score: {sum(scores)/len(scores):.1f}")
        
        # Ranges
        r80_90 = len([s for s in scores if 80 <= s <= 90])
        r91_100 = len([s for s in scores if s > 90])
        r_low = len([s for s in scores if s < 80])
        print(f"    - Scores 80-90%: {r80_90} samples")
        print(f"    - Scores 91-100%: {r91_100} samples")
        print(f"    - Scores < 80%:    {r_low} samples")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KAVACH QR Code Detector Evaluation")
    parser.add_argument("--safe", default="datasets/qr/safe", help="Path to safe QR images")
    parser.add_argument("--fake", default="datasets/qr/fake", help="Path to fake QR images")
    args = parser.parse_args()

    print("KAVACH – QR Code Detector Evaluation Pipeline\n")
    evaluate(args.safe, args.fake)
