from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bulletproof pathing for Vercel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'q-vercel-latency.json')

@app.post("/api/latency")
async def get_metrics(payload: dict = Body(...)):
    regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 0)
    
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    
    results = {}
    for region in regions:
        region_rows = [row for row in data if row.get('region') == region]
        
        if region_rows:
            latencies = [row['latency_ms'] for row in region_rows]
            uptimes = [row['uptime'] for row in region_rows]
            
            results[region] = {
                "avg_latency": float(np.mean(latencies)),
                "p95_latency": float(np.percentile(latencies, 95)),
                "avg_uptime": float(np.mean(uptimes)),
                "breaches": int(sum(1 for lat in latencies if lat > threshold))
            }
            
    return results
