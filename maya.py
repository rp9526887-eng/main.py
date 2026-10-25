import json
import os
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException, Request
import time
from collections import defaultdict

# --- ডেভলপার তথ্য ---
DEVELOPER = {
    "name": "Juel Developer",
    "project": "Contact Search API",
    "version": "1.0.0",
    "year": 2026,
}

app = FastAPI(
    title="Contact Search API",
    description=f"Developed by {DEVELOPER['name']}",
    version=DEVELOPER["version"],
    contact={"name": DEVELOPER["name"]},
)

# --- ডেটা লোড ---
DATA_FILE = Path(__file__).parent / "data.json"
with open(DATA_FILE, encoding="utf-8") as f:
    contacts = json.load(f)

phone_index = {c["phone"]: c for c in contacts if c.get("phone")}

# --- কী ও রেট লিমিট ---
API_KEY = os.getenv("API_KEY", "JuelHacker0")
RATE_LIMIT = 60
WINDOW = 60
hits = defaultdict(list)

def check_rate_limit(ip: str):
    now = time.time()
    hits[ip] = [t for t in hits[ip] if now - t < WINDOW]
    if len(hits[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests")
    hits[ip].append(now)

# --- মূল endpoint ---
@app.get("/api")
async def search(
    request: Request,
    key: str = Query(...),
    type: str = Query("mobile"),
    term: str = Query(...),
):
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    check_rate_limit(request.client.host)

    term_clean = term.strip()
    result = []

    if type == "mobile":
        r = phone_index.get(term_clean)
        result = [r] if r else []
    elif type == "name":
        q = term_clean.lower()
        result = [c for c in contacts if q in c.get("name_search", "")]
    elif type == "city":
        q = term_clean.lower()
        result = [c for c in contacts if q in c["city"].lower()]
    elif type == "id":
        if not term_clean.isdigit():
            raise HTTPException(status_code=400, detail="id must be a number")
        result = [c for c in contacts if c["id"] == int(term_clean)]
    else:
        raise HTTPException(status_code=400, detail="type must be one of: mobile, name, city, id")

    return {
        "success": True,
        "count": len(result),
        "data": result,
        "developer": DEVELOPER["name"],
    }

# --- নির্দিষ্ট ফোন নম্বর ইনফো এন্ডপয়েন্ট ---
@app.get("/info/{phone}")
async def get_info(phone: str):
    r = phone_index.get(phone)
    if not r:
        raise HTTPException(status_code=404, detail="Phone number not found")
    return {
        "success": True,
        "data": r
    }

# --- হোমপেজ (ডেভলপার ক্রেডিট) ---
@app.get("/")
def root():
    return {
        "status": "ok",
        "total_contacts": len(contacts),
        "developer": DEVELOPER["name"],
        "project": DEVELOPER["project"],
        "version": DEVELOPER["version"],
        "docs": "/docs",
    }

# --- আলাদা ডেভলপার এন্ডপয়েন্ট ---
@app.get("/developer")
def developer():
    return DEVELOPER
    
