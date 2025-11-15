# app.py
import os
import random
import asyncio
from typing import Literal
from datetime import datetime

import httpx
import sentry_sdk
from fastapi import FastAPI, HTTPException, Request
from sentry_sdk.integrations.fastapi import FastApiIntegration
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT", "production"),
    release=os.getenv("RELEASE", "v1.0.0"),
    traces_sample_rate=1.0,
    enable_logs=True
)

app = FastAPI(title="E-Commerce Demo", version="1.0.0")
BASE_URL = os.getenv("SCENARIO_BASE_URL", "http://localhost:8000")

@app.get("/")
async def home():
    await asyncio.sleep(random.uniform(0.02, 0.08))
    return {"status": "ok", "service": "demo-shop"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/catalog")
async def catalog():
    await asyncio.sleep(random.uniform(0.05, 0.15))
    if random.random() < 0.01:
        raise RuntimeError("Catalog service temporarily unavailable")
    return {"items": ["shirt", "shoes", "hat"], "total": 3}

@app.get("/product/{product_id}")
async def product_detail(product_id: int):
    # Simulate DB query
    await asyncio.sleep(random.uniform(0.03, 0.12))
    if random.random() < 0.02:
        raise LookupError(f"Product {product_id} not found")
    return {"id": product_id, "name": f"Product {product_id}", "price": 42}

@app.get("/checkout")
async def checkout(mode: Literal["normal", "slow", "error"] = "normal"):
    """
    Main checkout endpoint - currently active
    """
    await asyncio.sleep(random.uniform(0.05, 0.15))
    
    if mode == "error":
        raise ValueError("Checkout failed: payment token missing")
    
    base_latency = max(0.05, random.gauss(0.2, 0.06))
    if mode == "slow":
        base_latency *= 4
    
    await asyncio.sleep(base_latency)
    return {"status": "ok", "mode": mode, "latency_s": round(base_latency, 3)}

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/api/orders")
async def create_order(request: Request):
    """
    Order creation endpoint
    """
    data = await request.json()
    
    # BUG: Missing validation - will crash if payment_method not provided
    payment_method = data["payment_method"]  # KeyError possible!
    
    if payment_method not in ["credit_card", "paypal"]:
        raise ValueError(f"Invalid payment method: {payment_method}")
    
    await asyncio.sleep(random.uniform(0.1, 0.3))
    return {"order_id": random.randint(1000, 9999), "status": "created"}

@app.get("/api/inventory/{sku}")
async def check_inventory(sku: str):
    """
    Inventory check endpoint
    """
    await asyncio.sleep(random.uniform(0.05, 0.2))
    
    # Simulate occasional database timeout
    if random.random() < 0.03:
        await asyncio.sleep(5.0)  # Timeout!
        raise TimeoutError("Inventory database timeout")
    
    return {"sku": sku, "available": random.randint(0, 100)}

@app.post("/api/refunds")
async def process_refund(request: Request):
    """
    Refund processing endpoint
    """
    data = await request.json()
    
    # Simulate external payment processor call
    await asyncio.sleep(random.uniform(0.2, 0.5))
    
    # 5% failure rate - too high for refunds!
    if random.random() < 0.05:
        raise HTTPException(status_code=502, detail="Payment processor unavailable")
    
    return {"refund_id": f"REF-{random.randint(10000, 99999)}", "status": "processed"}

@app.get("/api/recommendations/{user_id}")
async def get_recommendations(user_id: int):
    """
    ML recommendation endpoint
    """
    # Simulate ML model inference
    await asyncio.sleep(random.uniform(0.3, 1.5))  # Wide variance!
    
    return {
        "user_id": user_id,
        "recommendations": [f"product_{i}" for i in range(5)]
    }

@app.delete("/api/cache/clear")
async def clear_cache():
    """
    Admin cache clearing endpoint
    """
    await asyncio.sleep(0.05)
    
    # Simulate occasional permission error
    if random.random() < 0.1:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return {"status": "cache cleared"}

# ============================================================================
# SCENARIO ENDPOINTS (for generating test data)
# ============================================================================

async def _fire_requests(path: str, params: dict | None, count: int, method: str = "GET", json_data: dict | None = None):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        for _ in range(count):
            try:
                if method == "POST":
                    await client.post(path, params=params, json=json_data)
                else:
                    await client.get(path, params=params)
            except httpx.HTTPError:
                pass

@app.post("/scenario/baseline")
async def scenario_baseline(requests: int = 50):
    """Generate normal baseline traffic on active endpoints"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        for _ in range(requests):
            route = random.choice(["/", "/catalog", "/product/123", "/checkout"])
            params = {"mode": "normal"} if route == "/checkout" else None
            try:
                await client.get(route, params=params)
                # Small delay to respect Render free tier rate limits (0.1 CPU)
                await asyncio.sleep(0.1)
            except httpx.HTTPError:
                pass

    return {"scenario": "baseline", "requests": requests}

@app.post("/scenario/checkout-error-spike")
async def scenario_checkout_error_spike(requests: int = 80):
    """Generate error spike on checkout - triggers Flow 1"""
    await _fire_requests("/checkout", {"mode": "error"}, requests)
    return {"scenario": "checkout-error-spike", "requests": requests}

@app.post("/scenario/checkout-latency-spike")
async def scenario_checkout_latency_spike(requests: int = 80):
    """Generate latency spike on checkout - triggers Flow 1"""
    await _fire_requests("/checkout", {"mode": "slow"}, requests)
    return {"scenario": "checkout-latency-spike", "requests": requests}

@app.post("/scenario/trigger-orders")
async def scenario_trigger_orders(requests: int = 50):
    """Trigger the /api/orders endpoint - some will fail"""
    for _ in range(requests):
        # Some requests missing payment_method = errors
        json_data = {"items": [1, 2, 3]}
        if random.random() > 0.3:  # 30% will have the bug
            json_data["payment_method"] = "credit_card"
        
        await _fire_requests("/api/orders", None, 1, method="POST", json_data=json_data)
    
    return {"scenario": "trigger-orders", "requests": requests}

@app.post("/scenario/inventory-timeouts")
async def scenario_inventory_timeouts(requests: int = 40):
    """Trigger inventory timeouts"""
    await _fire_requests("/api/inventory/SKU123", None, requests)
    return {"scenario": "inventory-timeouts", "requests": requests}