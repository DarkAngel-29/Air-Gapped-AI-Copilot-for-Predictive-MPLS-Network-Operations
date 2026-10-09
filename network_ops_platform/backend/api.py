"""
Network Operations Platform - REST API Layer
Exposes endpoints for querying telemetry, router health states, metrics statistics,
and collector operational diagnostics.
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import TelemetryDatabase
from .collector import LogCollector
from .models import (
    TelemetryRecordDB,
    RouterLatestState,
    TelemetryStats,
    CollectorStatusResponse
)

logger = logging.getLogger("ops_platform.api")

# Shared instances
db = TelemetryDatabase()
collector = LogCollector(db=db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages API service lifecycle: boots the background log collector on startup
    and gracefully halts it on shutdown.
    """
    logger.info("Initializing Network Operations Platform Backend...")
    # Perform initial sync
    collector.collect_once()
    # Start continuous background collection
    collector.start()
    yield
    logger.info("Shutting down Network Operations Platform Backend...")
    collector.stop()


app = FastAPI(
    title="MPLS Network Operations Platform API",
    description="Local backend service for ingesting, querying, and monitoring air-gapped MPLS telemetry.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status", summary="Operations Platform Health & Status")
def get_system_status() -> Dict[str, Any]:
    """
    Returns high-level status of the Operations Platform backend, database, and log ingestion.
    """
    collector_status = collector.get_status()
    return {
        "status": "ONLINE",
        "air_gapped": True,
        "database": {
            "location": collector_status.database_location,
            "total_records": collector_status.total_imported_records,
            "unique_routers": collector_status.number_of_routers_detected,
            "last_imported_timestamp": collector_status.last_imported_timestamp
        },
        "collector": {
            "running": collector_status.collector_running,
            "source_log": collector_status.log_file_location,
            "log_exists": collector_status.log_file_exists,
            "last_poll": collector_status.last_poll_time
        }
    }


@app.get("/api/collector/status", response_model=CollectorStatusResponse, summary="Log Collector Status & Diagnostics")
def get_collector_status():
    """
    Exposes diagnostics for the Log Collector service, including records imported,
    byte offsets, errors, and log stream state.
    """
    return collector.get_status()


@app.post("/api/collector/trigger", summary="Trigger Manual Log Collection")
def trigger_collection():
    """
    Forces an immediate collection cycle against the simulator JSONL log file.
    """
    result = collector.collect_once()
    return {
        "message": "Collection cycle executed",
        "result": result,
        "status": collector.get_status()
    }


@app.get("/api/telemetry/latest", response_model=List[TelemetryRecordDB], summary="Get Latest Telemetry")
def get_latest_telemetry(
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of records to return")
):
    """
    Retrieves the most recent N telemetry records across all routers.
    """
    return db.get_latest_telemetry(limit=limit)


@app.get("/api/telemetry/recent", response_model=List[TelemetryRecordDB], summary="Get Recent Telemetry by Window or Router")
def get_recent_telemetry(
    minutes: Optional[int] = Query(None, ge=1, le=1440, description="Rolling time window in minutes"),
    limit: int = Query(200, ge=1, le=2000, description="Maximum number of records to return"),
    router_id: Optional[str] = Query(None, description="Optional router ID filter (e.g. R1)")
):
    """
    Retrieves telemetry filtered by a rolling time window and/or router ID.
    """
    return db.get_recent_telemetry(minutes=minutes, limit=limit, router_id=router_id)


@app.get("/api/telemetry/routers", response_model=List[RouterLatestState], summary="Get Latest State of Each Router")
def get_latest_router_states():
    """
    Retrieves the latest telemetry snapshot and total sample count for every active router in the network.
    """
    return db.get_latest_router_states()


@app.get("/api/telemetry/routers/{router_id}", response_model=List[TelemetryRecordDB], summary="Get Telemetry for a Specific Router")
def get_telemetry_for_router(
    router_id: str,
    limit: int = Query(50, ge=1, le=1000, description="Maximum records to return for this router")
):
    """
    Retrieves recent telemetry records for a single router, newest first.
    """
    records = db.get_telemetry_by_router(router_id=router_id, limit=limit)
    if not records:
        # Check if router exists in db at all
        routers = [r["router_id"] for r in db.get_latest_router_states()]
        if router_id not in routers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Router '{router_id}' not found in telemetry database."
            )
    return records


@app.get("/api/telemetry/stats", response_model=TelemetryStats, summary="Get Basic Telemetry Statistics")
def get_telemetry_stats(
    minutes: Optional[int] = Query(None, ge=1, le=1440, description="Rolling time window in minutes for statistics")
):
    """
    Calculates network telemetry statistics: router count, metric min/max/avg,
    status distributions, and active faults.
    """
    return db.get_telemetry_stats(minutes=minutes)
