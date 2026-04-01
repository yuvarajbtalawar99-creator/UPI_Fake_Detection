# -*- coding: utf-8 -*-
import os
import sys
import cv2
import numpy as np

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.services.screenshot_service import analyze_screenshot

DATASET_PATH = 'dataset'

def evaluate():
    results = {'real': {'correct': 0, 'total': 0}, 'fake': {'correct': 0, 'total': 0}}
    
    for label in ['real', 'fake']:
        dir_path = os.path.join(DATASET_PATH, label)
        if not os.path.exists(dir_path):
            continue
            
        print(f"\nEvaluating {label.upper()} images...")
        files = [f for f in os.listdir(dir_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        for filename in files:
            file_path = os.path.join(dir_path, filename)
            with open(file_path, 'rb') as f:
                image_bytes = f.read()
            
            # Analyze
            res = analyze_screenshot(image_bytes)
            risk = res['risk_score']
            is_fraud = risk >= 50
            
            # For real images, correct = is_fraud is False
            # For fake images, correct = is_fraud is True
            is_correct = (not is_fraud) if label == 'real' else is_fraud
            
            if is_correct:
                results[label]['correct'] += 1
            results[label]['total'] += 1
            
            status = "✅ PASS" if is_correct else "❌ FAIL"
            pred = "FAKE" if is_fraud else "REAL"
            app = res.get('app_identified', 'Unknown')
            ml_p = res.get('ml_prediction', 'N/A')
            print(f"  {filename}: {status} | Score: {risk} | Predict: {pred} | App: {app} | ML: {ml_p}")

    print("\n" + "="*30)
    print("FINAL ACCURACY REPORT")
    print("="*30)
    total_correct = results['real']['correct'] + results['fake']['correct']
    total_images = results['real']['total'] + results['fake']['total']
    
    if total_images > 0:
        accuracy = (total_correct / total_images) * 100
        print(f"Overall Accuracy: {accuracy:.2f}%")
        print(f"Real Captured: {results['real']['correct']}/{results['real']['total']}")
        print(f"Fake Blocked: {results['fake']['correct']}/{results['fake']['total']}")
    else:
        print("No images found for evaluation.")

if __name__ == "__main__":
    evaluate()
