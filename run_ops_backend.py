"""
Air-Gapped AI Copilot for Predictive MPLS Network Operations
Module 2B: Network Operations Platform - Log Collector & Local Database Launcher
---------------------------------------------------------------------------------
Starts the local Log Collector service, synchronizes telemetry from ./logs/telemetry.jsonl
into local SQLite database (./network_ops_platform/data/ops_platform.db), and serves the REST API.
"""
import sys
import os
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from network_ops_platform.backend.config import settings
from network_ops_platform.backend.api import app, collector, db


def main():
    parser = argparse.ArgumentParser(
        description="Run Network Operations Platform - Log Collector & Local Database Backend"
    )
    parser.add_argument("--host", default=settings.api_host, help=f"Host to bind (default: {settings.api_host})")
    parser.add_argument("--port", type=int, default=settings.api_port, help=f"Port to bind (default: {settings.api_port})")
    parser.add_argument("--log-path", default=None, help="Custom path to simulator telemetry.jsonl")
    parser.add_argument("--db-path", default=None, help="Custom path to SQLite database")
    args = parser.parse_args()

    if args.log_path:
        collector.log_path = Path(args.log_path)
    if args.db_path:
        db.db_path = Path(args.db_path)
        db.init_db()

    collector_meta = db.get_collector_metadata()

    print("=" * 75)
    print("  AIR-GAPPED NETWORK OPERATIONS PLATFORM - BACKEND & DATA LAYER")
    print("  Air-Gapped AI Copilot for Predictive MPLS Network Operations (Part 2B)")
    print("=" * 75)
    print(f"[*] Operational Mode:     AIR-GAPPED (100% Local Ingestion & Storage)")
    print(f"[*] Simulator Log Target: {collector.log_path.resolve()}")
    print(f"[*] SQLite Database:      {collector_meta['database_location']}")
    print(f"[*] Existing Records:     {collector_meta['total_records']}")
    print(f"[*] Detected Routers:     {collector_meta['unique_routers']}")
    print(f"[*] REST API Base URL:    http://{args.host}:{args.port}")
    print(f"[*] API Documentation:    http://{args.host}:{args.port}/docs")
    print("=" * 75)
    print("[*] Continuous Log Collector runs in background daemon mode.")
    print("[*] Deduplication is strictly enforced at database schema level.")
    print("[*] Press Ctrl+C to stop the Operations Backend gracefully.\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
