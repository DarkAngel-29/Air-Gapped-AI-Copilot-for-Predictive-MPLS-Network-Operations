"""
MPLS Network Simulator - Core Models
Defines router entities, fault configurations, and telemetry record structures.
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import time
from datetime import datetime, timezone


class RouterStatus(str, Enum):
    ACTIVE = "ACTIVE"
    FAULTED = "FAULTED"
    OFFLINE = "OFFLINE"


class FaultType(str, Enum):
    LATENCY_SPIKE = "Latency Spike"
    PACKET_LOSS_SPIKE = "Packet Loss Spike"
    HIGH_JITTER = "High Jitter"
    BANDWIDTH_CONGESTION = "Bandwidth Congestion"
    CPU_OVERLOAD = "CPU Overload"
    MEMORY_OVERLOAD = "Memory Overload"
    LINK_FAILURE = "Link Failure"


class FaultIntensity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ActiveFault(BaseModel):
    id: str
    target_router_id: str
    fault_type: FaultType
    duration_seconds: float
    remaining_seconds: float
    intensity: FaultIntensity
    started_at: float = Field(default_factory=time.time)


class Router(BaseModel):
    id: str
    name: str
    status: RouterStatus = RouterStatus.ACTIVE
    created_at: float = Field(default_factory=time.time)


class TelemetryRecord(BaseModel):
    timestamp: str
    router_id: str
    latency: float            # ms
    packet_loss: float        # %
    jitter: float             # ms
    bandwidth_usage: float    # %
    cpu_usage: float          # %
    memory_usage: float       # %
    status: str = "ACTIVE"
    active_fault: Optional[str] = None

    @classmethod
    def create(cls, router_id: str, latency: float, packet_loss: float,
               jitter: float, bandwidth_usage: float, cpu_usage: float,
               memory_usage: float, status: str = "ACTIVE",
               active_fault: Optional[str] = None) -> "TelemetryRecord":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            router_id=router_id,
            latency=round(latency, 2),
            packet_loss=round(packet_loss, 2),
            jitter=round(jitter, 2),
            bandwidth_usage=round(bandwidth_usage, 1),
            cpu_usage=round(cpu_usage, 1),
            memory_usage=round(memory_usage, 1),
            status=status,
            active_fault=active_fault
        )
