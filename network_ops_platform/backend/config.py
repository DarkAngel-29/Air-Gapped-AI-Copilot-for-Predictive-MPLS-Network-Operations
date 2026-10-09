"""
Network Operations Platform - Backend Configuration
Provides centralized configuration for log paths, database storage, and collector settings.
"""
import os
from pathlib import Path
from pydantic import BaseModel, Field

# Base project paths
ROOT_DIR = Path(__file__).resolve().parents[2]  # d:\Projects\Software Engg
OPS_DIR = ROOT_DIR / "network_ops_platform"
DATA_DIR = OPS_DIR / "data"


class OpsSettings(BaseModel):
    # Log source configuration (Simulator telemetry)
    simulator_log_path: Path = Field(
        default_factory=lambda: Path(
            os.getenv("SIMULATOR_LOG_PATH", str(ROOT_DIR / "logs" / "telemetry.jsonl"))
        )
    )

    # Local SQLite database path
    db_path: Path = Field(
        default_factory=lambda: Path(
            os.getenv("OPS_DB_PATH", str(DATA_DIR / "ops_platform.db"))
        )
    )

    # Collector operation parameters
    collector_poll_interval: float = Field(
        default_factory=lambda: float(os.getenv("COLLECTOR_POLL_INTERVAL", "1.0"))
    )
    collector_batch_size: int = Field(
        default_factory=lambda: int(os.getenv("COLLECTOR_BATCH_SIZE", "500"))
    )

    # Backend API server parameters
    api_host: str = Field(
        default_factory=lambda: os.getenv("OPS_API_HOST", "127.0.0.1")
    )
    api_port: int = Field(
        default_factory=lambda: int(os.getenv("OPS_API_PORT", "8001"))
    )


settings = OpsSettings()

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)
