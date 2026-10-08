"""
MPLS Network Simulator - HTTP & REST API Server
Provides endpoints for UI interactions, router management, simulation playback,
fault injection, and telemetry retrieval.
"""
import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from .engine import SimulationEngine
from .storage import LocalTelemetryStorage

# Initialize storage in ./logs/telemetry.jsonl
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
storage = LocalTelemetryStorage(log_dir=str(LOG_DIR), filename="telemetry.jsonl")
engine = SimulationEngine(storage=storage)

# Start background simulation ticking immediately
engine.start_background_loop()

app = FastAPI(
    title="MPLS Network Simulator",
    description="Independent telemetry generation engine for virtual MPLS routers",
    version="1.0.0"
)

# Enable CORS for local browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request schemas
class AddRouterRequest(BaseModel):
    id: str = Field(..., description="Router ID e.g. R5")
    name: Optional[str] = Field(None, description="Router descriptive name")


class SpeedRequest(BaseModel):
    speed: float = Field(..., ge=0.5, le=5.0)


class FaultInjectRequest(BaseModel):
    router_id: str
    fault_type: str
    duration: float = Field(default=30.0, ge=1.0)
    intensity: str = Field(default="High")


class FaultClearRequest(BaseModel):
    router_id: Optional[str] = None


# ---------------- API Endpoints ----------------

@app.get("/api/status")
def get_status():
    storage_stats = storage.get_storage_stats()
    return {
        "status": "RUNNING" if engine.is_running else "PAUSED",
        "is_running": engine.is_running,
        "speed": engine.speed,
        "total_routers": len(engine.routers),
        "active_faults_count": len(engine.active_faults),
        "storage": storage_stats
    }


@app.post("/api/simulation/start")
def start_simulation():
    engine.start()
    return {"message": "Simulation started", "is_running": True}


@app.post("/api/simulation/pause")
def pause_simulation():
    engine.pause()
    return {"message": "Simulation paused", "is_running": False}


@app.post("/api/simulation/reset")
def reset_simulation():
    engine.reset()
    return {"message": "Simulation reset to default state", "is_running": True}


@app.post("/api/simulation/speed")
def set_speed(req: SpeedRequest):
    if req.speed not in [0.5, 1.0, 2.0, 5.0]:
        raise HTTPException(status_code=400, detail="Speed must be 0.5, 1.0, 2.0, or 5.0")
    engine.set_speed(req.speed)
    return {"message": f"Speed set to {req.speed}x", "speed": engine.speed}


@app.get("/api/routers")
def list_routers():
    return {
        "routers": engine.list_routers()
    }


@app.post("/api/routers")
def add_router(req: AddRouterRequest):
    created = engine.add_router(req.id, req.name)
    return {
        "message": f"Router {created.id} added successfully",
        "router": created.model_dump()
    }


@app.delete("/api/routers/{router_id}")
def delete_router(router_id: str):
    success = engine.remove_router(router_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Router {router_id} not found")
    return {"message": f"Router {router_id} removed"}


@app.post("/api/faults/inject")
def inject_fault(req: FaultInjectRequest):
    fault = engine.inject_fault(
        router_id=req.router_id,
        fault_type_str=req.fault_type,
        duration_seconds=req.duration,
        intensity_str=req.intensity
    )
    if not fault:
        raise HTTPException(status_code=404, detail=f"Target router {req.router_id} not found")
    return {
        "message": f"Fault '{req.fault_type}' injected into {req.router_id}",
        "fault": fault.model_dump()
    }


@app.post("/api/faults/clear")
def clear_faults(req: FaultClearRequest = None):
    r_id = req.router_id if req else None
    engine.clear_faults(r_id)
    return {"message": f"Faults cleared" if not r_id else f"Faults cleared for {r_id}"}


@app.get("/api/telemetry/live")
def get_live_telemetry():
    """Returns current telemetry for all active routers."""
    routers_data = engine.list_routers()
    recent_records = [r.model_dump() for r in engine.recent_records_buffer[-20:]]
    return {
        "is_running": engine.is_running,
        "speed": engine.speed,
        "routers": routers_data,
        "recent_logs": recent_records,
        "storage": storage.get_storage_stats()
    }


@app.get("/api/telemetry/logs")
def get_persisted_logs(limit: int = 50):
    """Retrieves actual persisted telemetry records from local JSON Lines log file."""
    records = storage.get_recent_records(limit=limit)
    return {
        "records": records,
        "count": len(records),
        "storage": storage.get_storage_stats()
    }


# Static web UI serving
STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    gen_file = BASE_DIR / "Generator UI" / "code.html"
    if gen_file.exists():
        return FileResponse(gen_file)
    return {"message": "MPLS Network Simulator Backend Running"}
