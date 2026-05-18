from fastapi import FastAPI, Body, Response, Request
import json
import os

app = FastAPI()

# 1. SPECIFIC CORS HEADERS
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

# 2. LINEAR INTERPOLATION PERCENTILE FUNCTION
def calculate_p95(data):
    if not data:
        return 0.0
    data.sort()
    # (N - 1) * P gives the virtual index for linear interpolation
    n = len(data)
    index = (n - 1) * 0.95
    lower = int(index)
    upper = lower + 1
    weight = index - lower
    
    if upper >= n:
        return float(data[-1])
    
    # Interpolate between the two closest ranks
    result = data[lower] * (1 - weight) + data[upper] * weight
    return float(result)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'q-vercel-latency.json')

@app.get("/api/latency")
async def health_check():
    return {"status": "ready"}

@app.post("/api/latency")
async def get_metrics(payload: dict = Body(...)):
    requested_regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 180)
    
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            
        region_metrics = {}
        for region in requested_regions:
            rows = [row for row in data if row.get('region') == region]
            
            if rows:
                latencies = [row.get('latency_ms', 0) for row in rows]
                uptimes = [row.get('uptime_pct', 0) for row in rows]
                
                region_metrics[region] = {
                    "avg_latency": sum(latencies) / len(latencies),
                    "p95_latency": calculate_p95(latencies),
                    "avg_uptime": sum(uptimes) / len(uptimes),
                    "breaches": sum(1 for lat in latencies if lat > threshold)
                }
        
        return {"regions": region_metrics}

    except Exception as e:
        return {"error": "Processing error", "message": str(e)}

@app.get("/")
async def root():
    return {"status": "healthy"}
