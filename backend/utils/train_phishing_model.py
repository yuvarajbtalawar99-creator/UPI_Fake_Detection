# -*- coding: utf-8 -*-
"""
Training script for KAVACH URL Phishing Model.
Loads datasets, extracts features, and trains a RandomForest classifier.
"""

import os
import pickle
import sys
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.utils.url_feature_extractor import extract_url_features

# Paths
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
SAFE_URLS_PATH = os.path.join(BASE_DIR, "datasets", "urls", "safe_urls.txt")
PHISHING_URLS_PATH = os.path.join(BASE_DIR, "datasets", "urls", "phishing_urls.txt")
MODEL_DIR = os.path.join(BASE_DIR, "backend", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "url_phishing_model.pkl")

def load_dataset():
    urls = []
    labels = []
    
    if os.path.exists(SAFE_URLS_PATH):
        with open(SAFE_URLS_PATH, 'r') as f:
            for line in f:
                url = line.strip()
                if url:
                    urls.append(url)
                    labels.append(0) # 0 for Safe
                    
    if os.path.exists(PHISHING_URLS_PATH):
        with open(PHISHING_URLS_PATH, 'r') as f:
            for line in f:
                url = line.strip()
                if url:
                    urls.append(url)
                    labels.append(1) # 1 for Phishing
                    
    return urls, labels

def train():
    print("Loading datasets...")
    urls, labels = load_dataset()
    
    if not urls:
        print("ERROR: No data found in datasets/urls/")
        return
        
    print(f"Dataset Size: {len(urls)} URLs ({labels.count(0)} Safe, {labels.count(1)} Phishing)")
    
    print("Extracting features...")
    X = [extract_url_features(url) for url in urls]
    y = labels
    
    # Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training RandomForest model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {acc*100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save Model
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model saved to: {MODEL_PATH}")

if __name__ == "__main__":
    train()
