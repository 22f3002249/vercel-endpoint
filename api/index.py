from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Robust pathing
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: Ensure the file name matches exactly what you uploaded
DATA_FILE = os.path.join(BASE_DIR, 'q-vercel-latency.json')

@app.post("/api/latency")
async def get_metrics(payload: dict = Body(...)):
    regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 0)
    
    # 1. Check if the file actually exists
    if not os.path.exists(DATA_FILE):
        return {
            "error": "File not found",
            "path_searched": DATA_FILE,
            "files_in_folder": os.listdir(BASE_DIR)
        }

    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            
        results = {}
        for region in regions:
            # Filter rows for this region
            region_rows = [row for row in data if row.get('region') == region]
            
            if region_rows:
                latencies = [row['latency_ms'] for row in region_rows]
                uptimes = [row['uptime'] for row in region_rows]
                
                # Manual P95
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

    except Exception as e:
        # If the code crashes, it will now return the error message instead of a 500
        return {"error": "Processing error", "message": str(e)}
