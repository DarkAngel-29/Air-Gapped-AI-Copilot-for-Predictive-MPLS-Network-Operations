"""
Air-Gapped AI Copilot for Predictive MPLS Network Operations
Module 1: MPLS Network Simulator Launcher
--------------------------------------------------------------
Starts the local simulator backend, begins stochastic telemetry generation,
persists records to ./logs/telemetry.jsonl, and serves the tactile web interface.
"""
import sys
import os
import time
import webbrowser
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from simulator.server import app, storage, engine


def main():
    parser = argparse.ArgumentParser(description="Run MPLS Network Simulator")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open web browser")
    args = parser.parse_args()

    log_path = storage.filepath.resolve()
    print("=" * 70)
    print("  AIR-GAPPED MPLS NETWORK SIMULATOR")
    print("  Air-Gapped AI Copilot for Predictive MPLS Network Operations")
    print("=" * 70)
    print(f"[*] Engine Status:       ACTIVE (Tick rate: {engine.speed}x)")
    print(f"[*] Active Routers:      {', '.join(engine.routers.keys())}")
    print(f"[*] Log Storage Path:    {log_path}")
    print(f"[*] Web Simulator UI:    http://{args.host}:{args.port}")
    print("=" * 70)
    print("[*] Logs are actively persisted locally in JSON Lines format.")
    print("[*] Press Ctrl+C to shut down simulator gracefully.\n")

    if not args.no_browser:
        # Open browser shortly after server starts
        import threading
        def open_tab():
            time.sleep(1.0)
            webbrowser.open(f"http://{args.host}:{args.port}")
        threading.Thread(target=open_tab, daemon=True).start()

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
