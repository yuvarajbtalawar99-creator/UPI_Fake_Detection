# -*- coding: utf-8 -*-
"""
Layout and region-based validation for UPI payment screenshots.
Detects if the screenshot matches typical app layouts (PhonePe, GPay, Paytm).
"""

import cv2
import numpy as np

def detect_green_checkmark(img: np.ndarray) -> bool:
    """Detect if there is a green success circle/checkmark in the top half."""
    if img is None:
        return False
        
    height, width = img.shape[:2]
    top_half = img[0:height//2, :]
    
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(top_half, cv2.COLOR_BGR2HSV)
    
    # Define range for green color (success indicators)
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])
    
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # Check if a significant amount of green is detected (a circle or checkmark)
    green_pixels = np.count_nonzero(mask)
    # Heuristic: at least 0.5% of the top half area
    return green_pixels > (top_half.size * 0.005)

def analyze_layout(image_bytes: bytes) -> dict:
    """
    Perform heuristic layout analysis with color signature detection.
    Returns layout_score (0.0 - 1.0) and identified_template.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return {"layout_score": 0.0, "template": "unknown", "reasons": ["Invalid image"]}

    height, width = img.shape[:2]
    aspect_ratio = height / width
    
    reasons = []
    layout_score = 1.0
    
    # 1. Aspect Ratio Check
    if aspect_ratio < 1.3:
        layout_score -= 0.2
        reasons.append("Image aspect ratio does not match a typical mobile screenshot.")
    
    # 2. Success Indicator Check
    has_success_indicator = detect_green_checkmark(img)
    if not has_success_indicator:
        layout_score -= 0.3
        reasons.append("No standard 'Success' color indicator detected (green checkmark/circle).")
    
    # 3. Color Signature & Brand Integrity Detection
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # PhonePe Signature: Purple (#5f259f)
    # DIAGNOSTIC: Most screenshots have shifted Hues. Broadening search.
    lower_purple = np.array([110, 30, 30])
    upper_purple = np.array([170, 255, 255])
    purple_mask = cv2.inRange(hsv[0:height//4, :], lower_purple, upper_purple)
    purple_density = np.count_nonzero(purple_mask) / (width * (height//4))
    is_phonepe = purple_density > 0.02 

    # GPay Signature: High white density + Success Indicator
    lower_white = np.array([0, 0, 150])
    upper_white = np.array([180, 80, 255])
    white_mask = cv2.inRange(hsv, lower_white, upper_white)
    is_gpay = (np.count_nonzero(white_mask) / img.size) > 0.35 and has_success_indicator

    # Paytm Signature: Blue (#00baf2)
    lower_paytm_blue = np.array([80, 30, 30])
    upper_paytm_blue = np.array([120, 255, 255])
    blue_mask = cv2.inRange(hsv[0:height//4, :], lower_paytm_blue, upper_paytm_blue)
    is_paytm = (np.count_nonzero(blue_mask) / (width * (height//4))) > 0.02

    template = "Generic UPI"
    if is_phonepe: template = "PhonePe"
    elif is_gpay: template = "Google Pay"
    elif is_paytm: template = "Paytm"

    # 4. Digital Manipulation Detection (Noise Analysis)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # DIAGNOSTIC: Generated fakes are much SHARPER (>500 var) than real screens (~150 var).
    laplacian = cv2.Laplacian(gray, cv2.CV_64F).var()
    is_too_sharp = laplacian > 500.0 # Artificial sharpness
    is_too_blurry = laplacian < 30.0 # Unreadable
    
    noise_reason = ""
    if is_too_sharp:
        layout_score -= 0.3
        noise_reason = "Artificial digital sharpness detected (typical of generated receipts)."
    elif is_too_blurry:
        layout_score -= 0.2
        noise_reason = "Image is too blurry for reliable verification."

    if noise_reason:
        reasons.append(noise_reason)

    # 5. Text Density Profile
    edges = cv2.Canny(gray, 50, 150)
    v_profile = np.sum(edges, axis=1)
    region_size = height // 5
    region_sums = [np.sum(v_profile[i*region_size : (i+1)*region_size]) for i in range(5)]
    total_edges = sum(region_sums)
    
    if total_edges > 0:
        region_probs = [r / total_edges for r in region_sums]
        # Middle region (amount) should have moderate edge density
        if region_probs[2] < 0.02: 
            layout_score -= 0.2
            reasons.append("Central area (Amount) lacks expected UI complexity.")

    return {
        "layout_score": max(0.0, layout_score),
        "template": template,
        "reasons": reasons,
        "has_success_indicator": has_success_indicator or is_phonepe or is_paytm,
        "is_too_sharp": is_too_sharp,
        "is_too_blurry": is_too_blurry
    }
