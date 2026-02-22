import json
import math
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Enable CORS for POST requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyticsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

# Load data at startup (runs once per cold start)
try:
    with open("telemetry.json", "r") as f:
        raw_data = json.load(f)
except Exception:
    raw_data = []

def get_p95(values):
    if not values: return 0
    values = sorted(values)
    k = (len(values) - 1) * 0.95
    f = math.floor(k)
    c = math.ceil(k)
    if f == c: return values[int(k)]
    return values[int(f)] * (c - k) + values[int(c)] * (k - f)

@app.post("/api")
def process_analytics(req: AnalyticsRequest):
    # Filter by requested regions
    filtered = [d for d in raw_data if d.get("region") in req.regions]
    
    if not filtered:
        return {"avg_latency": 0, "p95_latency": 0, "avg_uptime": 0, "breaches": 0}
        
    latencies = [d["latency"] for d in filtered]
    uptimes = [d["uptime"] for d in filtered]
    
    avg_latency = sum(latencies) / len(latencies)
    avg_uptime = sum(uptimes) / len(uptimes)
    breaches = sum(1 for l in latencies if l > req.threshold_ms)
    p95_latency = get_p95(latencies)
    
    return {
        "avg_latency": avg_latency,
        "p95_latency": p95_latency,
        "avg_uptime": avg_uptime,
        "breaches": breaches
    }
