from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import statistics

app = FastAPI()

# Robust CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bulletproof pathing
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'q-vercel-latency.json')

@app.post("/api/latency")
async def get_metrics(payload: dict = Body(...)):
    regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 0)
    
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    except Exception as e:
        return {"error": f"Could not load data file: {str(e)}"}
    
    results = {}
    for region in regions:
        # Filter rows for this region
        region_rows = [row for row in data if row.get('region') == region]
        
        if region_rows:
            latencies = [row['latency_ms'] for row in region_rows]
            uptimes = [row['uptime'] for row in region_rows]
            
            # Calculate P95 manually using statistics
            latencies.sort()
            idx = int(len(latencies) * 0.95)
            p95 = latencies[min(idx, len(latencies)-1)]
            
            results[region] = {
                "avg_latency": sum(latencies) / len(latencies),
                "p95_latency": float(p95),
                "avg_uptime": sum(uptimes) / len(uptimes),
                "breaches": sum(1 for lat in latencies if lat > threshold)
            }
            
    return results
