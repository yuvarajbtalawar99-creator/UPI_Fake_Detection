# -*- coding: utf-8 -*-
import os
import cv2
import numpy as np
import sys

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.utils.layout_validator import analyze_layout, detect_green_checkmark
from backend.utils.ml_feature_extractor import extract_features

DATASET_PATH = 'dataset'

def diagnose():
    for label in ['real', 'fake']:
        dir_path = os.path.join(DATASET_PATH, label)
        if not os.path.exists(dir_path):
            continue
            
        print(f"\n--- {label.upper()} SAMPLES ---")
        files = [f for f in os.listdir(dir_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        for filename in files[:5]: # Check first 5 of each
            file_path = os.path.join(dir_path, filename)
            img = cv2.imread(file_path)
            if img is None: continue
            
            with open(file_path, 'rb') as f:
                image_bytes = f.read()
            
            # 1. Laplacian (Noise)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # 2. Green Check
            has_green = detect_green_checkmark(img)
            
            # 3. Layout Result
            layout_res = analyze_layout(image_bytes)
            
            # 4. Features
            features = extract_features(image_bytes)
            
            print(f"File: {filename}")
            print(f"  Laplacian Var: {laplacian:.2f}")
            print(f"  Green Check: {has_green}")
            print(f"  Identified App: {layout_res.get('template')}")
            print(f"  Layout Score: {layout_res.get('layout_score')}")
            print(f"  Feature Sample (H,S,V): {features[1:4]}") # Sample histogram bins

if __name__ == "__main__":
    diagnose()
