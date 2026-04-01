import os
import json
from fastapi import APIRouter
from pydantic import BaseModel
from ..services.url_service import analyze_url


class URLRequest(BaseModel):
    url: str


# Persistent report storage
REPORTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "reports.json")


def get_reports():
    """Load reported URLs and their counts."""
    if not os.path.exists(REPORTS_FILE):
        return {}
    try:
        with open(REPORTS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_report(url: str):
    """Increment report count for a URL."""
    reports = get_reports()
    url_key = url.strip().lower()
    reports[url_key] = reports.get(url_key, 0) + 1
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(REPORTS_FILE), exist_ok=True)
    
    with open(REPORTS_FILE, "w") as f:
        json.dump(reports, f, indent=2)
    return reports[url_key]


router = APIRouter(prefix="/api/url", tags=["URL"])


@router.post("/analyze")
async def analyze_url_endpoint(request: URLRequest):
    """Analyze URL via standard endpoint."""
    result = analyze_url(request.url)
    result["url"] = request.url
    reports = get_reports()
    url_key = request.url.strip().lower()
    result["report_count"] = reports.get(url_key, 0)
    return result


@router.post("/phishing/analyze")
async def analyze_phishing_endpoint(request: URLRequest):
    """
    Dedicated phishing analysis endpoint.
    Returns hybrid risk score (ML + Rules).
    """
    result = analyze_url(request.url)
    result["url"] = request.url
    reports = get_reports()
    url_key = request.url.strip().lower()
    result["report_count"] = reports.get(url_key, 0)
    return result


@router.post("/report")
async def report_url_endpoint(request: URLRequest):
    """Report a URL as a scam."""
    new_count = save_report(request.url)
    return {
        "status": "success",
        "message": "URL reported successfully",
        "url": request.url,
        "report_count": new_count
    }
