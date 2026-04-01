# -*- coding: utf-8 -*-
"""
Feature extraction for UPI payment screenshot ML classification.
Converts images into numerical vectors for Scikit-Learn.
"""

import cv2
import numpy as np
import io
from PIL import Image

def extract_features(image_bytes: bytes) -> np.ndarray:
    """
    Extract a numerical feature vector from image bytes.
    Returns a 1D numpy array.
    """
    # Load image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        # Return a zero vector of size 20 if image is invalid
        return np.zeros(25)

    height, width = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    features = []

    # 1. Aspect Ratio
    features.append(height / width)

    # 2. Color Distribution (Histograms)
    # Simplified histograms for H, S, V channels
    for i in range(3):
        hist = cv2.calcHist([hsv], [i], None, [4], [0, 256])
        cv2.normalize(hist, hist)
        features.extend(hist.flatten().tolist()) # 4*3 = 12 features

    # 3. Brightness & Saturation stats
    features.append(np.mean(hsv[:,:,1]) / 255.0) # Avg Saturation
    features.append(np.mean(hsv[:,:,2]) / 255.0) # Avg Value (Brightness)

    # 4. Texture / Sharpness
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    features.append(min(laplacian_var / 500.0, 1.0)) # Normalized sharpness

    # 5. Edge Density (Canny)
    edges = cv2.Canny(gray, 100, 200)
    edge_density = np.count_nonzero(edges) / (width * height)
    features.append(edge_density)

    # 6. Top-Bar Color Signature (PhonePe/Paytm check)
    top_bar = hsv[0:height//10, :]
    features.append(np.mean(top_bar[:,:,0]) / 180.0) # Avg Hue of top bar
    features.append(np.mean(top_bar[:,:,1]) / 255.0) # Avg Sat of top bar

    # 7. Overall contrast
    features.append((np.max(gray) - np.min(gray)) / 255.0)

    # 8. Vertical Density Profile (structural layout)
    edges = cv2.Canny(gray, 50, 150)
    v_profile = np.sum(edges, axis=1)
    region_size = height // 5
    region_sums = [np.sum(v_profile[i*region_size : (i+1)*region_size]) for i in range(5)]
    total_edges = sum(region_sums)
    if total_edges > 0:
        features.extend([r / total_edges for r in region_sums]) # 5 features
    else:
        features.extend([0.0] * 5)

    # Ensure we have exactly 30 features (pad if necessary)
    feature_vec = np.array(features, dtype=np.float32)
    if len(feature_vec) < 30:
        feature_vec = np.pad(feature_vec, (0, 30 - len(feature_vec)))
    elif len(feature_vec) > 30:
        feature_vec = feature_vec[:30]
        
    return feature_vec
