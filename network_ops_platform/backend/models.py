"""
Network Operations Platform - Data Models & Schemas
Defines telemetry schemas, validation models, query filters, and response types.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class RawTelemetryInput(BaseModel):
    """
    Validates raw telemetry records emitted by the MPLS Simulator.
    Ensures data integrity prior to SQLite insertion.
    """
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp string from simulator")
    router_id: str = Field(..., min_length=1, max_length=64, description="Unique router identifier (e.g. R1)")
    latency: float = Field(..., ge=0.0, description="Network latency in milliseconds")
    packet_loss: float = Field(..., ge=0.0, le=100.0, description="Packet loss percentage [0-100]")
    jitter: float = Field(..., ge=0.0, description="Jitter variance in milliseconds")
    bandwidth_usage: float = Field(..., ge=0.0, le=100.0, description="Bandwidth utilization percentage [0-100]")
    cpu_usage: float = Field(..., ge=0.0, le=100.0, description="CPU utilization percentage [0-100]")
    memory_usage: float = Field(..., ge=0.0, le=100.0, description="Memory utilization percentage [0-100]")
    status: str = Field(default="ACTIVE", description="Router operational status")
    active_fault: Optional[str] = Field(default=None, description="Active injected fault description, if any")

    @field_validator("router_id", mode="before")
    @classmethod
    def clean_router_id(cls, v: Any) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("router_id must be a non-empty string")
        return v.strip()

    @field_validator("timestamp", mode="before")
    @classmethod
    def clean_timestamp(cls, v: Any) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("timestamp must be a non-empty string")
        return v.strip()


class TelemetryRecordDB(BaseModel):
    """
    Structured model for telemetry retrieved from the SQLite database.
    """
    id: int
    timestamp: str
    router_id: str
    latency: float
    packet_loss: float
    jitter: float
    bandwidth_usage: float
    cpu_usage: float
    memory_usage: float
    status: str
    active_fault: Optional[str] = None
    imported_at: str


class RouterLatestState(BaseModel):
    """
    Represents the most recently recorded health and performance state of a router.
    """
    router_id: str
    last_timestamp: str
    latency: float
    packet_loss: float
    jitter: float
    bandwidth_usage: float
    cpu_usage: float
    memory_usage: float
    status: str
    active_fault: Optional[str] = None
    total_samples: int = 0


class MetricSummary(BaseModel):
    min: float = 0.0
    max: float = 0.0
    avg: float = 0.0


class TelemetryStats(BaseModel):
    """
    Aggregated statistical summary of telemetry data across the network.
    """
    total_records: int
    router_count: int
    routers: List[str]
    earliest_timestamp: Optional[str] = None
    latest_timestamp: Optional[str] = None
    time_window_minutes: Optional[int] = None
    metrics: Dict[str, MetricSummary]
    status_distribution: Dict[str, int]
    fault_distribution: Dict[str, int]


class CollectorStatusResponse(BaseModel):
    """
    Operational diagnostics for the Log Collector service.
    """
    collector_running: bool
    database_location: str
    log_file_location: str
    log_file_exists: bool
    log_file_size_bytes: int
    total_imported_records: int
    last_imported_timestamp: Optional[str] = None
    number_of_routers_detected: int
    total_lines_read: int
    total_records_inserted: int
    total_errors_encountered: int
    last_poll_time: Optional[str] = None
    last_error: Optional[str] = None
