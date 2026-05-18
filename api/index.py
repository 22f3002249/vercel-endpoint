from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load the data once when the server starts
# Assuming the file is named q-vercel-latency.json and is in the root
data_path = os.path.join(os.path.dirname(__file__), '..', 'q-vercel-latency.json')
df = pd.read_json(data_path, orient='records')

@app.post("/api/latency")
async def get_metrics(payload: dict = Body(...)):
    regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 0)
    
    results = {}
    
    for region in regions:
        # Filter data for the specific region
        region_data = df[df['region'] == region]
        
        if not region_data.empty:
            latencies = region_data['latency_ms']
            
            results[region] = {
                "avg_latency": float(latencies.mean()),
                "p95_latency": float(np.percentile(latencies, 95)),
                "avg_uptime": float(region_data['uptime'].mean()),
                "breaches": int((latencies > threshold).sum())
            }
        else:
            results[region] = "No data found for this region"
            
    return results
