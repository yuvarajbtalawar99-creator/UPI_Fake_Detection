# -*- coding: utf-8 -*-
"""Verification script for KAVACH Phishing Detector."""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/url/phishing/analyze"

def test_url(url):
    print(f"\nAnalyzing: {url}")
    try:
        resp = requests.post(BASE_URL, json={"url": url})
        if resp.status_code == 200:
            data = resp.json()
            print(f"Risk Score: {data['risk_score']}")
            print(f"Status: {data['status']}")
            print(f"ML Probability: {data['extracted_fields'].get('ml_risk_probability', 'N/A')}%")
            print("Reasons:")
            for r in data['reasons']:
                print(f"  - {r}")
        else:
            print(f"FAILED: {resp.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    print("KAVACH PHISHING DETECTOR VERIFICATION\n")
    # Test a known safe URL
    test_url("https://www.google.com")
    # Test a known suspicious pattern
    test_url("http://verify-bank-secure-update.xyz/login")
    # Test a typosquatted brand
    test_url("http://paytim-verify.link")
