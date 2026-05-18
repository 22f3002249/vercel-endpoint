from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# FIX CORS: allow_credentials must be False to allow the "*" wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Robust pathing for Vercel environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'q-vercel-latency.json')

@app.post("/api/latency")
async def get_metrics(payload: dict = Body(...)):
    regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 180) # default to 180 as per instructions
    
    try:
        # Load the JSON data
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            
        results = {}
        for region in regions:
            # Filter rows matching the requested region
            region_rows = [row for row in data if row.get('region') == region]
            
            if region_rows:
                # Extract columns based on your provided JSON schema
                latencies = [row.get('latency_ms') for row in region_rows]
                # Using 'uptime_pct' as found in your data snippet
                uptimes = [row.get('uptime_pct') for row in region_rows]
                
                # Calculate p95 latency: sort and take the 95th percentile index
                latencies.sort()
                p95_idx = int(len(latencies) * 0.95)
                p95_val = latencies[min(p95_idx, len(latencies)-1)]
                
                results[region] = {
                    "avg_latency": sum(latencies) / len(latencies),
                    "p95_latency": float(p95_val),
                    "avg_uptime": sum(uptimes) / len(uptimes),
                    "breaches": sum(1 for lat in latencies if lat > threshold)
                }
        
        return results

    except Exception as e:
        return {"error": "Processing error", "message": str(e)}

@app.get("/")
async def health_check():
    return {"status": "healthy"}
