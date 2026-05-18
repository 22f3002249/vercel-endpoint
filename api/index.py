from fastapi import FastAPI, Body, Response, Request
import json
import os

app = FastAPI()

# 1. Define the specific headers you provided
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Expose-Headers": "Access-Control-Allow-Origin",
}

# 2. Add custom middleware to "force-inject" these headers into EVERY response
@app.middleware("http")
async def add_custom_cors_headers(request: Request, call_next):
    # Handle the Preflight (OPTIONS) request immediately
    if request.method == "OPTIONS":
        response = Response()
        for key, value in CORS_HEADERS.items():
            response.headers[key] = value
        return response
    
    # Handle the actual request (GET or POST)
    response = await call_next(request)
    
    # Add your headers to the response
    for key, value in CORS_HEADERS.items():
        response.headers[key] = value
        
    return response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'q-vercel-latency.json')

# GET handler for the same URL to prevent 405 errors during testing
@app.get("/api/latency")
async def health_check():
    return {"status": "ready"}

# The main POST handler
@app.post("/api/latency")
async def get_metrics(payload: dict = Body(...)):
    regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 180)
    
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            
        results = {}
        for region in regions:
            region_rows = [row for row in data if row.get('region') == region]
            
            if region_rows:
                latencies = [row.get('latency_ms', 0) for row in region_rows]
                # Using 'uptime_pct' as found in your JSON snippet
                uptimes = [row.get('uptime_pct', 0) for row in region_rows]
                
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
async def root():
    return {"status": "healthy"}
