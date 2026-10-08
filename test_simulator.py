"""
Automated Verification Suite for MPLS Network Simulator
Tests:
1. Dynamic router provisioning (R1, R2, ..., R5, R6...)
2. Realistic telemetry generation & fluctuation
3. Fault injection & realistic telemetry perturbation
4. Local persistence in JSON Lines (telemetry.jsonl)
5. Metric schema and data consistency
"""
import sys
import time
import json
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from simulator.models import RouterStatus, FaultType, FaultIntensity
from simulator.storage import LocalTelemetryStorage
from simulator.engine import SimulationEngine


class TestMPLSNetworkSimulator(unittest.TestCase):
    def setUp(self):
        self.test_log_dir = PROJECT_ROOT / "logs"
        self.test_log_file = "test_telemetry.jsonl"
        self.storage = LocalTelemetryStorage(log_dir=str(self.test_log_dir), filename=self.test_log_file)
        self.storage.clear_logs()
        self.engine = SimulationEngine(storage=self.storage)

    def tearDown(self):
        # Clean up test log file
        test_path = self.test_log_dir / self.test_log_file
        if test_path.exists():
            test_path.unlink()

    def test_default_routers(self):
        """Verifies default routers R1, R2, R3, R4 exist."""
        routers = self.engine.list_routers()
        router_ids = [r["id"] for r in routers]
        self.assertEqual(router_ids, ["R1", "R2", "R3", "R4"])
        for r in routers:
            self.assertEqual(r["status"], "ACTIVE")

    def test_dynamic_router_addition(self):
        """Verifies dynamic addition of routers (R5, R6...) with custom names."""
        r5 = self.engine.add_router("R5", "Edge Aggregation Router 5")
        self.assertEqual(r5.id, "R5")
        self.assertEqual(r5.name, "Edge Aggregation Router 5")

        r6 = self.engine.add_router("R6", "Core Transit Router 6")
        self.assertEqual(r6.id, "R6")

        routers = self.engine.list_routers()
        router_ids = [r["id"] for r in routers]
        self.assertIn("R5", router_ids)
        self.assertIn("R6", router_ids)
        self.assertEqual(len(routers), 6)

    def test_telemetry_generation_and_fluctuation(self):
        """Verifies telemetry generation on ticks and natural variation."""
        # Tick 1
        records1 = self.engine.step(1.0)
        self.assertEqual(len(records1), 4)

        # Mandatory fields check
        required_fields = {
            "timestamp", "router_id", "latency", "packet_loss",
            "jitter", "bandwidth_usage", "cpu_usage", "memory_usage"
        }
        for rec in records1:
            rec_dict = rec.model_dump()
            for field in required_fields:
                self.assertIn(field, rec_dict, f"Missing required field {field}")
            # Normal baseline assertions
            self.assertGreater(rec.latency, 5.0)
            self.assertLess(rec.latency, 45.0)
            self.assertLess(rec.packet_loss, 2.0)
            self.assertGreater(rec.bandwidth_usage, 10.0)
            self.assertLess(rec.bandwidth_usage, 80.0)

        # Tick 2
        records2 = self.engine.step(1.0)
        r1_rec1 = next(r for r in records1 if r.router_id == "R1")
        r1_rec2 = next(r for r in records2 if r.router_id == "R1")
        # Telemetry should dynamically fluctuate, not be static
        self.assertNotEqual(
            (r1_rec1.latency, r1_rec1.cpu_usage, r1_rec1.bandwidth_usage),
            (r1_rec2.latency, r1_rec2.cpu_usage, r1_rec2.bandwidth_usage)
        )

    def test_fault_injection_cpu_overload(self):
        """Verifies that injecting CPU Overload pushes CPU to 90-99% and status to FAULTED."""
        fault = self.engine.inject_fault(
            router_id="R3",
            fault_type_str="CPU Overload",
            duration_seconds=10.0,
            intensity_str="High"
        )
        self.assertIsNotNone(fault)
        self.assertEqual(self.engine.routers["R3"].status, RouterStatus.FAULTED)

        records = self.engine.step(1.0)
        r3_record = next(r for r in records if r.router_id == "R3")
        self.assertEqual(r3_record.status, "FAULTED")
        self.assertGreaterEqual(r3_record.cpu_usage, 90.0)
        self.assertLessEqual(r3_record.cpu_usage, 100.0)
        self.assertEqual(r3_record.active_fault, "CPU Overload")

        # Other non-faulted routers should remain ACTIVE with normal CPU
        r1_record = next(r for r in records if r.router_id == "R1")
        self.assertEqual(r1_record.status, "ACTIVE")
        self.assertLess(r1_record.cpu_usage, 65.0)

    def test_fault_injection_latency_spike(self):
        """Verifies Latency Spike fault injection pushes latency up realistically."""
        self.engine.inject_fault(
            router_id="R2",
            fault_type_str="Latency Spike",
            duration_seconds=5.0,
            intensity_str="High"
        )
        records = self.engine.step(1.0)
        r2_record = next(r for r in records if r.router_id == "R2")
        self.assertGreater(r2_record.latency, 100.0)

    def test_fault_expiration_and_recovery(self):
        """Verifies that fault returns toward normal baseline when duration expires."""
        self.engine.inject_fault(
            router_id="R1",
            fault_type_str="Packet Loss Spike",
            duration_seconds=2.0,
            intensity_str="High"
        )
        self.assertEqual(self.engine.routers["R1"].status, RouterStatus.FAULTED)

        # Step 1: fault still active (1s remaining)
        self.engine.step(1.0)
        self.assertEqual(self.engine.routers["R1"].status, RouterStatus.FAULTED)

        # Step 2: fault expires (remaining <= 0)
        self.engine.step(1.5)
        self.assertEqual(self.engine.routers["R1"].status, RouterStatus.ACTIVE)
        self.assertNotIn("R1", self.engine.active_faults)

    def test_local_storage_persistence(self):
        """Verifies that generated records are actually persisted locally in JSON Lines."""
        self.engine.step(1.0)
        self.engine.step(1.0)

        # Check file exists on disk
        test_file_path = self.test_log_dir / self.test_log_file
        self.assertTrue(test_file_path.exists())

        # Read back lines and verify JSON parsing
        with open(test_file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        # 4 routers * 2 steps = 8 records
        self.assertEqual(len(lines), 8)

        for line in lines:
            data = json.loads(line)
            self.assertIn("timestamp", data)
            self.assertIn("router_id", data)
            self.assertIn("latency", data)
            self.assertIn("packet_loss", data)
            self.assertIn("jitter", data)
            self.assertIn("bandwidth_usage", data)
            self.assertIn("cpu_usage", data)
            self.assertIn("memory_usage", data)

        stats = self.storage.get_storage_stats()
        self.assertEqual(stats["total_records"], 8)
        self.assertGreater(stats["size_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
