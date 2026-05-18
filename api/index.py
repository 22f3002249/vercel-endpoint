from fastapi import FastAPI, Body, Response, Request
import json
import os

app = FastAPI()

# Your specific CORS headers
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Expose-Headers": "Access-Control-Allow-Origin",
}

@app.middleware("http")
async def add_custom_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response()
        for key, value in CORS_HEADERS.items():
            response.headers[key] = value
        return response
    
    response = await call_next(request)
    for key, value in CORS_HEADERS.items():
        response.headers[key] = value
    return response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'q-vercel-latency.json')

@app.get("/api/latency")
async def health_check():
    return {"status": "ready"}

@app.post("/api/latency")
async def get_metrics(payload: dict = Body(...)):
    # Standardize input extraction
    requested_regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 180)
    
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            
        region_metrics = {}
        for region in requested_regions:
            # Filter rows for this specific region
            rows = [row for row in data if row.get('region') == region]
            
            if rows:
                latencies = [row.get('latency_ms', 0) for row in rows]
                # Your JSON data uses 'uptime_pct'
                uptimes = [row.get('uptime_pct', 0) for row in rows]
                
                # Calculate P95
                latencies.sort()
                p95_idx = int(len(latencies) * 0.95)
                p95_val = latencies[min(p95_idx, len(latencies)-1)]
                
                region_metrics[region] = {
                    "avg_latency": sum(latencies) / len(latencies),
                    "p95_latency": float(p95_val),
                    "avg_uptime": sum(uptimes) / len(uptimes),
                    "breaches": sum(1 for lat in latencies if lat > threshold)
                }
        
        # FIX: Wrap the result in a "regions" key as requested by the error
        return {"regions": region_metrics}

    except Exception as e:
        return {"error": "Processing error", "message": str(e)}

@app.get("/")
async def root():
    return {"status": "healthy"}
