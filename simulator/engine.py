"""
MPLS Network Simulator - Telemetry & Simulation Engine
Simulates virtual routers, realistic network physics, fault injection dynamics,
and generates structured telemetry logs persisted to disk.
"""
import time
import math
import random
import threading
from typing import Dict, List, Optional, Any
from .models import Router, RouterStatus, FaultType, FaultIntensity, ActiveFault, TelemetryRecord
from .storage import LocalTelemetryStorage


class RouterState:
    """Internal simulation state for an individual router."""
    def __init__(self, router_id: str, name: str):
        self.id = router_id
        self.name = name
        self.status = RouterStatus.ACTIVE
        
        # Baselines unique to this router
        # Seed slightly by router hash for subtle individual router personality
        seed = sum(ord(c) for c in router_id)
        self.base_latency = 12.0 + (seed % 7) * 0.8       # ~12 - 17 ms
        self.base_packet_loss = 0.05 + (seed % 3) * 0.05  # ~0.05 - 0.15 %
        self.base_jitter = 1.6 + (seed % 5) * 0.25        # ~1.6 - 2.8 ms
        self.base_bandwidth = 38.0 + (seed % 10) * 1.5    # ~38 - 53 %
        self.base_cpu = 26.0 + (seed % 8) * 1.8          # ~26 - 40 %
        self.base_memory = 36.0 + (seed % 6) * 2.0       # ~36 - 48 %

        # Current smooth values
        self.curr_latency = self.base_latency
        self.curr_packet_loss = self.base_packet_loss
        self.curr_jitter = self.base_jitter
        self.curr_bandwidth = self.base_bandwidth
        self.curr_cpu = self.base_cpu
        self.curr_memory = self.base_memory

        self.last_telemetry: Optional[TelemetryRecord] = None


class SimulationEngine:
    def __init__(self, storage: Optional[LocalTelemetryStorage] = None):
        self.storage = storage or LocalTelemetryStorage()
        self.routers: Dict[str, RouterState] = {}
        self.active_faults: Dict[str, ActiveFault] = {} # target_router_id -> ActiveFault
        
        self.is_running = True
        self.speed = 1.0 # 0.5, 1.0, 2.0, 5.0
        self.base_interval = 1.0 # 1 second per tick at 1x
        
        self._lock = threading.Lock()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.recent_records_buffer: List[TelemetryRecord] = []
        self.max_recent_records = 100

        # Initialize default routers: R1, R2, R3, R4
        self._initialize_default_routers()

    def _initialize_default_routers(self):
        defaults = [
            ("R1", "Ingress Router 1"),
            ("R2", "Core Router 2"),
            ("R3", "Core Router 3"),
            ("R4", "Egress Router 4")
        ]
        for r_id, r_name in defaults:
            self.routers[r_id] = RouterState(r_id, r_name)

    # ---------------- Router Management ----------------
    def add_router(self, router_id: str, name: Optional[str] = None) -> Router:
        with self._lock:
            router_id = router_id.strip().upper()
            if not router_id:
                # Auto-generate next ID R5, R6...
                num = len(self.routers) + 1
                while f"R{num}" in self.routers:
                    num += 1
                router_id = f"R{num}"
            
            router_name = name.strip() if name and name.strip() else f"Router {router_id}"
            
            if router_id in self.routers:
                # Update name if already exists
                self.routers[router_id].name = router_name
            else:
                self.routers[router_id] = RouterState(router_id, router_name)
            
            return Router(
                id=router_id,
                name=self.routers[router_id].name,
                status=self.routers[router_id].status
            )

    def remove_router(self, router_id: str) -> bool:
        with self._lock:
            router_id = router_id.strip().upper()
            if router_id in self.routers:
                del self.routers[router_id]
                if router_id in self.active_faults:
                    del self.active_faults[router_id]
                return True
            return False

    def list_routers(self) -> List[Dict[str, Any]]:
        with self._lock:
            res = []
            for r_id, state in sorted(self.routers.items(), key=lambda x: (len(x[0]), x[0])):
                latest = state.last_telemetry
                res.append({
                    "id": state.id,
                    "name": state.name,
                    "status": state.status.value,
                    "has_fault": r_id in self.active_faults,
                    "active_fault": self.active_faults[r_id].model_dump() if r_id in self.active_faults else None,
                    "telemetry": latest.model_dump() if latest else None
                })
            return res

    # ---------------- Simulation Controls ----------------
    def start(self):
        with self._lock:
            self.is_running = True

    def pause(self):
        with self._lock:
            self.is_running = False

    def set_speed(self, speed: float):
        with self._lock:
            if speed in [0.5, 1.0, 2.0, 5.0]:
                self.speed = speed

    def reset(self):
        with self._lock:
            self.active_faults.clear()
            self.routers.clear()
            self._initialize_default_routers()
            self.recent_records_buffer.clear()
            self.is_running = True
            self.speed = 1.0

    # ---------------- Fault Injection ----------------
    def inject_fault(self, router_id: str, fault_type_str: str,
                     duration_seconds: float = 30.0,
                     intensity_str: str = "High") -> Optional[ActiveFault]:
        with self._lock:
            router_id = router_id.strip().upper()
            if router_id not in self.routers:
                return None
            
            try:
                fault_type = FaultType(fault_type_str)
            except ValueError:
                fault_type = FaultType.CPU_OVERLOAD
                
            try:
                intensity = FaultIntensity(intensity_str)
            except ValueError:
                intensity = FaultIntensity.HIGH

            fault = ActiveFault(
                id=f"fault_{int(time.time()*1000)}",
                target_router_id=router_id,
                fault_type=fault_type,
                duration_seconds=duration_seconds,
                remaining_seconds=duration_seconds,
                intensity=intensity
            )
            self.active_faults[router_id] = fault
            self.routers[router_id].status = RouterStatus.FAULTED
            return fault

    def clear_faults(self, router_id: Optional[str] = None):
        with self._lock:
            if router_id:
                router_id = router_id.strip().upper()
                if router_id in self.active_faults:
                    del self.active_faults[router_id]
                if router_id in self.routers:
                    self.routers[router_id].status = RouterStatus.ACTIVE
            else:
                self.active_faults.clear()
                for r in self.routers.values():
                    r.status = RouterStatus.ACTIVE

    # ---------------- Step & Telemetry Generation ----------------
    def step(self, delta_time: float) -> List[TelemetryRecord]:
        """Calculates one tick of telemetry across all routers and persists to storage."""
        records: List[TelemetryRecord] = []
        
        with self._lock:
            if not self.is_running:
                return []

            # 1. Update active faults countdown
            expired_faults = []
            for r_id, fault in list(self.active_faults.items()):
                fault.remaining_seconds -= delta_time * self.speed
                if fault.remaining_seconds <= 0:
                    expired_faults.append(r_id)

            for r_id in expired_faults:
                del self.active_faults[r_id]
                if r_id in self.routers:
                    self.routers[r_id].status = RouterStatus.ACTIVE

            # 2. Generate telemetry for each router
            for r_id, state in self.routers.items():
                fault = self.active_faults.get(r_id)
                record = self._compute_router_telemetry(state, fault)
                state.last_telemetry = record
                records.append(record)
                
                # Keep in memory ring buffer
                self.recent_records_buffer.append(record)
                if len(self.recent_records_buffer) > self.max_recent_records:
                    self.recent_records_buffer.pop(0)

        # 3. Persist batch to local JSON Lines storage
        if records:
            dict_records = [r.model_dump() for r in records]
            self.storage.write_records_batch(dict_records)

        return records

    def _compute_router_telemetry(self, state: RouterState, fault: Optional[ActiveFault]) -> TelemetryRecord:
        """Applies realistic stochastic physics and sensible metric relationships."""
        # Mean reversion random walk for baseline metrics
        # Bandwidth natural drift (±3.5%, mean reversion to base)
        bw_pull = (state.base_bandwidth - state.curr_bandwidth) * 0.1
        bw_noise = random.gauss(0, 1.8)
        state.curr_bandwidth = max(10.0, min(85.0, state.curr_bandwidth + bw_pull + bw_noise))

        # CPU natural drift (correlates lightly with bandwidth)
        cpu_pull = (state.base_cpu - state.curr_cpu) * 0.1
        cpu_bw_impact = (state.curr_bandwidth - state.base_bandwidth) * 0.15
        cpu_noise = random.gauss(0, 1.5)
        state.curr_cpu = max(15.0, min(80.0, state.curr_cpu + cpu_pull + cpu_bw_impact + cpu_noise))

        # Memory natural drift (slow moving, ±0.5%)
        mem_pull = (state.base_memory - state.curr_memory) * 0.05
        mem_noise = random.gauss(0, 0.4)
        state.curr_memory = max(20.0, min(75.0, state.curr_memory + mem_pull + mem_noise))

        # Latency natural drift with queueing model
        lat_pull = (state.base_latency - state.curr_latency) * 0.15
        lat_noise = random.gauss(0, 0.6)
        # Latency increases when bandwidth is congested (>65%)
        lat_queue = max(0.0, (state.curr_bandwidth - 65.0) * 0.35)
        # Latency also affected if CPU is high (>65%)
        lat_cpu = max(0.0, (state.curr_cpu - 65.0) * 0.25)
        state.curr_latency = max(8.0, state.curr_latency + lat_pull + lat_noise + lat_queue + lat_cpu)

        # Jitter natural drift
        jit_pull = (state.base_jitter - state.curr_jitter) * 0.15
        jit_noise = random.gauss(0, 0.25)
        jit_queue = max(0.0, (state.curr_bandwidth - 70.0) * 0.1)
        state.curr_jitter = max(0.8, min(10.0, state.curr_jitter + jit_pull + jit_noise + jit_queue))

        # Packet Loss natural drift
        loss_pull = (state.base_packet_loss - state.curr_packet_loss) * 0.2
        loss_noise = random.uniform(-0.03, 0.04)
        loss_queue = max(0.0, (state.curr_bandwidth - 75.0) * 0.04)
        state.curr_packet_loss = max(0.0, min(1.5, state.curr_packet_loss + loss_pull + loss_noise + loss_queue))

        # Default normal telemetry
        lat = state.curr_latency
        loss = state.curr_packet_loss
        jit = state.curr_jitter
        bw = state.curr_bandwidth
        cpu = state.curr_cpu
        mem = state.curr_memory
        status = RouterStatus.ACTIVE.value
        fault_name = None

        # Apply Fault Modifiers if target router has an active fault
        if fault is not None:
            status = RouterStatus.FAULTED.value
            fault_name = fault.fault_type.value
            
            # Multiplier based on intensity
            intensity_factor = {
                FaultIntensity.LOW: 0.4,
                FaultIntensity.MEDIUM: 0.7,
                FaultIntensity.HIGH: 1.0
            }.get(fault.intensity, 1.0)

            ft = fault.fault_type

            if ft == FaultType.LATENCY_SPIKE:
                # Latency jumps to 120 - 280ms
                added_lat = (140.0 + random.uniform(-15.0, 45.0)) * intensity_factor
                lat = state.base_latency + added_lat
                jit = state.base_jitter + (12.0 + random.uniform(-2.0, 8.0)) * intensity_factor
                loss = state.base_packet_loss + (0.3 + random.uniform(0.0, 0.5)) * intensity_factor

            elif ft == FaultType.PACKET_LOSS_SPIKE:
                # Packet loss jumps to 5% - 22%
                added_loss = (12.0 + random.uniform(-2.0, 8.0)) * intensity_factor
                loss = min(35.0, state.base_packet_loss + added_loss)
                lat = state.base_latency + (18.0 + random.uniform(-3.0, 10.0)) * intensity_factor
                jit = state.base_jitter + (6.0 + random.uniform(-1.0, 4.0)) * intensity_factor

            elif ft == FaultType.HIGH_JITTER:
                # High jitter (20 - 55 ms) with fluctuating latency
                added_jit = (32.0 + random.uniform(-6.0, 15.0)) * intensity_factor
                jit = state.base_jitter + added_jit
                lat = state.base_latency + (35.0 + random.uniform(-10.0, 25.0)) * intensity_factor

            elif ft == FaultType.BANDWIDTH_CONGESTION:
                # Congestion: Bandwidth 88 - 98%, queue buildup causing high latency & jitter
                bw = min(98.5, 88.0 + (random.uniform(0.0, 9.5) * intensity_factor))
                lat = state.base_latency + (95.0 + random.uniform(-10.0, 35.0)) * intensity_factor
                jit = state.base_jitter + (18.0 + random.uniform(-3.0, 8.0)) * intensity_factor
                loss = state.base_packet_loss + (2.2 + random.uniform(-0.4, 1.2)) * intensity_factor
                cpu = min(92.0, state.base_cpu + (30.0 + random.uniform(-5.0, 10.0)) * intensity_factor)

            elif ft == FaultType.CPU_OVERLOAD:
                # CPU Overload: CPU 91 - 99%, scheduler delays raise latency & drop packets
                cpu = min(99.4, 91.0 + (random.uniform(0.0, 8.0) * intensity_factor))
                lat = state.base_latency + (65.0 + random.uniform(-10.0, 25.0)) * intensity_factor
                jit = state.base_jitter + (14.0 + random.uniform(-2.0, 7.0)) * intensity_factor
                loss = state.base_packet_loss + (1.6 + random.uniform(-0.3, 0.9)) * intensity_factor

            elif ft == FaultType.MEMORY_OVERLOAD:
                # Memory Overload: Memory 88 - 98%, buffer exhaustion
                mem = min(98.8, 88.0 + (random.uniform(0.0, 9.5) * intensity_factor))
                cpu = min(82.0, state.base_cpu + (20.0 + random.uniform(-3.0, 7.0)) * intensity_factor)
                loss = state.base_packet_loss + (1.2 + random.uniform(-0.2, 0.8)) * intensity_factor

            elif ft == FaultType.LINK_FAILURE:
                # Link Failure: Complete link degradation, 100% loss, timeout latency
                loss = 100.0
                lat = 999.0
                jit = 0.0
                bw = 0.0
                status = RouterStatus.FAULTED.value

        return TelemetryRecord.create(
            router_id=state.id,
            latency=lat,
            packet_loss=loss,
            jitter=jit,
            bandwidth_usage=bw,
            cpu_usage=cpu,
            memory_usage=mem,
            status=status,
            active_fault=fault_name
        )

    # ---------------- Background Runner ----------------
    def start_background_loop(self):
        """Starts background loop that ticks simulation at defined interval."""
        if self._worker_thread and self._worker_thread.is_alive():
            return
            
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._worker_thread.start()

    def stop_background_loop(self):
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=2.0)

    def _run_loop(self):
        last_time = time.time()
        while not self._stop_event.is_set():
            now = time.time()
            dt = now - last_time
            last_time = now

            if self.is_running:
                self.step(dt)

            # Sleep dynamic duration based on speed
            # At 1.0x -> sleeps ~1.0s. At 2.0x -> sleeps ~0.5s. At 5.0x -> sleeps ~0.2s.
            sleep_duration = max(0.1, self.base_interval / max(0.1, self.speed))
            time.sleep(sleep_duration)
