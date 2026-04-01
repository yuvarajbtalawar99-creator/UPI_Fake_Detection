# -*- coding: utf-8 -*-
"""
URL feature extractor for KAVACH.
Converts a raw URL into a set of numeric features for ML classification.
"""

import re
from urllib.parse import urlparse

def extract_url_features(url: str) -> list:
    """
    Extracts features from a URL.
    Returns a list of numeric features:
    0: URL Length
    1: Number of dots
    2: Number of hyphens
    3: Presence of IP address (1 if yes, 0 if no)
    4: Presence of suspicious keywords (count)
    5: Is HTTPS (1 if yes, 0 if no)
    6: Number of subdomains
    7: Presence of '@' symbol
    8: Presence of '//' after protocol
    """
    features = []
    
    # Normalize URL for extraction
    clean_url = url.strip().lower()
    if not clean_url.startswith("http"):
        clean_url = "http://" + clean_url
        
    try:
        parsed = urlparse(clean_url)
    except Exception:
        return [0] * 9

    # 0: Length
    features.append(len(url))
    
    # 1: Number of dots
    features.append(url.count('.'))
    
    # 2: Number of hyphens
    features.append(url.count('-'))
    
    # 3: IP Address presence
    domain = parsed.hostname or ""
    has_ip = 1 if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", domain) else 0
    features.append(has_ip)
    
    # 4: Suspicious keywords count
    keywords = ["login", "verify", "secure", "update", "account", "banking", "signin", "password"]
    keyword_count = sum(1 for k in keywords if k in clean_url)
    features.append(keyword_count)
    
    # 5: HTTPS usage
    is_https = 1 if parsed.scheme == "https" else 0
    features.append(is_https)
    
    # 6: Number of subdomains
    subdomains = domain.count('.')
    features.append(subdomains)
    
    # 7: '@' symbol
    has_at = 1 if "@" in url else 0
    features.append(has_at)
    
    # 8: '//' inside URL (redirection)
    # The standard protocol is at index 0, so check from index 7 onwards
    has_double_slash = 1 if url.find("//", 7) != -1 else 0
    features.append(has_double_slash)
    
    return features

def get_feature_names():
    return [
        "url_length", "dot_count", "hyphen_count", "has_ip", 
        "keyword_count", "is_https", "subdomain_count", 
        "has_at_symbol", "has_redirection"
    ]
