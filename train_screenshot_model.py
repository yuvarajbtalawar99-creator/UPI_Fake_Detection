# -*- coding: utf-8 -*-
"""
KAVACH - Screenshot Classification Training Pipeline (v2).
Uses Random Forest and Feature Engineering for REAL vs FAKE detection.
"""

import os
import sys
import argparse
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Import our custom feature extractor
# We need to add the parent directory to sys.path to import from backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.utils.ml_feature_extractor import extract_features

# Configuration
DATASET_PATH = 'dataset/'
MODEL_NAME = 'screenshot_model.pkl'

def load_dataset():
    """Loads images from dataset/real and dataset/fake and extracts features."""
    X = []
    y = []
    
    classes = {'fake': 0, 'real': 1}
    
    for label, value in classes.items():
        dir_path = os.path.join(DATASET_PATH, label)
        if not os.path.exists(dir_path):
            continue
            
        print(f"Processing '{label}' folder...")
        files = [f for f in os.listdir(dir_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        for i, filename in enumerate(files):
            file_path = os.path.join(dir_path, filename)
            try:
                with open(file_path, 'rb') as f:
                    image_bytes = f.read()
                
                features = extract_features(image_bytes)
                X.append(features)
                y.append(value)
                
                if (i + 1) % 10 == 0:
                    print(f"  Processed {i+1}/{len(files)} images...")
            except Exception as e:
                print(f"  Error processing {filename}: {e}")
                
    return np.array(X), np.array(y)

def train_model():
    print("KAVACH - Starting Feature-Based Model Training...")
    
    # 1. Load Dataset
    X, y = load_dataset()
    if len(X) == 0:
        print("Error: No images found in dataset. Please add image files to dataset/real and dataset/fake.")
        return

    print(f"Dataset loaded: {len(X)} samples, {X.shape[1]} features.")
    
    # 2. Split Data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 3. Initialize and Train Model
    # RandomForest is robust to small datasets and feature scales
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)
    
    # 4. Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nModel Evaluation:")
    print(f"Accuracy: {acc:.2%}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['FAKE', 'REAL']))
    
    # 5. Save Model
    print(f"Saving model to {MODEL_NAME}...")
    joblib.dump(model, MODEL_NAME)
    
    print("\nTraining Complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train KAVACH Screenshot Classifier')
    args = parser.parse_args()
    
    # Check if dataset path exists
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset path '{DATASET_PATH}' not found.")
        sys.exit(1)
        
    train_model()
