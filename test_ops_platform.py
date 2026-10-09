"""
Test Suite: Network Operations Platform - Log Collector & Local Database Layer
Verifies schema, deduplication, incremental collection, error handling, and analytical queries.
"""
import os
import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone

from network_ops_platform.backend.config import OpsSettings
from network_ops_platform.backend.models import RawTelemetryInput
from network_ops_platform.backend.database import TelemetryDatabase
from network_ops_platform.backend.collector import LogCollector


class TestOpsPlatformBackend(unittest.TestCase):

    def setUp(self):
        # Create temporary directory for isolated database and log testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.db_path = self.temp_path / "test_ops.db"
        self.log_path = self.temp_path / "test_telemetry.jsonl"

        self.db = TelemetryDatabase(db_path=self.db_path)
        self.collector = LogCollector(db=self.db, log_path=self.log_path)

    def tearDown(self):
        self.collector.stop()
        self.temp_dir.cleanup()

    def _create_sample_record(self, router_id="R1", timestamp=None, latency=14.5, active_fault=None):
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        return {
            "timestamp": ts,
            "router_id": router_id,
            "latency": latency,
            "packet_loss": 0.05,
            "jitter": 1.2,
            "bandwidth_usage": 45.0,
            "cpu_usage": 32.5,
            "memory_usage": 40.0,
            "status": "ACTIVE" if not active_fault else "FAULTED",
            "active_fault": active_fault
        }

    def test_database_initialization(self):
        """Verify SQLite database schema and tables are created correctly."""
        self.assertTrue(self.db_path.exists())
        meta = self.db.get_collector_metadata()
        self.assertEqual(meta["total_records"], 0)
        self.assertEqual(meta["unique_routers"], 0)

    def test_record_validation(self):
        """Verify Pydantic models validate constraints and reject malformed fields."""
        valid_data = self._create_sample_record()
        record = RawTelemetryInput(**valid_data)
        self.assertEqual(record.router_id, "R1")
        self.assertEqual(record.latency, 14.5)

        # Invalid: Negative latency
        bad_data = valid_data.copy()
        bad_data["latency"] = -5.0
        with self.assertRaises(Exception):
            RawTelemetryInput(**bad_data)

        # Invalid: Packet loss over 100%
        bad_data = valid_data.copy()
        bad_data["packet_loss"] = 105.0
        with self.assertRaises(Exception):
            RawTelemetryInput(**bad_data)

        # Invalid: Empty router_id
        bad_data = valid_data.copy()
        bad_data["router_id"] = "   "
        with self.assertRaises(Exception):
            RawTelemetryInput(**bad_data)

    def test_incremental_log_collection(self):
        """Verify continuous log collection detects new records without re-importing old ones."""
        # 1. Write initial 4 records (2 for R1, 2 for R2)
        records = [
            self._create_sample_record("R1", timestamp="2026-10-08T12:00:01Z", latency=12.0),
            self._create_sample_record("R2", timestamp="2026-10-08T12:00:01Z", latency=15.0),
            self._create_sample_record("R1", timestamp="2026-10-08T12:00:02Z", latency=13.0),
            self._create_sample_record("R2", timestamp="2026-10-08T12:00:02Z", latency=16.0),
        ]
        with open(self.log_path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        # Ingest
        res1 = self.collector.collect_once()
        self.assertEqual(res1["status"], "success")
        self.assertEqual(res1["records_inserted"], 4)

        meta1 = self.db.get_collector_metadata()
        self.assertEqual(meta1["total_records"], 4)
        self.assertEqual(meta1["unique_routers"], 2)

        # 2. Re-run without changes: Should detect 0 new records
        res2 = self.collector.collect_once()
        self.assertEqual(res2["status"], "up_to_date")
        self.assertEqual(res2["records_inserted"], 0)
        self.assertEqual(self.db.get_collector_metadata()["total_records"], 4)

        # 3. Append 2 new records for R3
        new_records = [
            self._create_sample_record("R3", timestamp="2026-10-08T12:00:03Z", latency=18.0),
            self._create_sample_record("R3", timestamp="2026-10-08T12:00:04Z", latency=19.0),
        ]
        with open(self.log_path, "a", encoding="utf-8") as f:
            for r in new_records:
                f.write(json.dumps(r) + "\n")

        # Ingest incremental records
        res3 = self.collector.collect_once()
        self.assertEqual(res3["status"], "success")
        self.assertEqual(res3["records_inserted"], 2)

        meta3 = self.db.get_collector_metadata()
        self.assertEqual(meta3["total_records"], 6)
        self.assertEqual(meta3["unique_routers"], 3)

    def test_deduplication_guarantee(self):
        """Verify duplicate (router_id, timestamp) pairs are blocked."""
        record = self._create_sample_record("R1", timestamp="2026-10-08T12:00:00Z")
        rec_obj = RawTelemetryInput(**record)

        # Insert first time
        inserted1 = self.db.insert_telemetry_batch([rec_obj])
        self.assertEqual(inserted1, 1)

        # Insert exact duplicate
        inserted2 = self.db.insert_telemetry_batch([rec_obj])
        self.assertEqual(inserted2, 0)

        # Total in DB must remain 1
        self.assertEqual(self.db.get_collector_metadata()["total_records"], 1)

    def test_error_handling_malformed_lines(self):
        """Verify collector safely skips corrupted or malformed lines without crashing."""
        valid_rec1 = self._create_sample_record("R1", timestamp="2026-10-08T12:01:00Z")
        valid_rec2 = self._create_sample_record("R2", timestamp="2026-10-08T12:01:00Z")

        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(valid_rec1) + "\n")
            f.write("{NOT_VALID_JSON: true\n")                      # JSON decode error
            f.write(json.dumps({"incomplete": "record"}) + "\n")     # Validation error (missing required fields)
            f.write(json.dumps(valid_rec2) + "\n")

        res = self.collector.collect_once()
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["errors"], 2)

        # Only the 2 valid records should be inserted
        self.assertEqual(self.db.get_collector_metadata()["total_records"], 2)
        self.assertEqual(self.collector.total_errors_encountered, 2)

    def test_missing_log_file_handling(self):
        """Verify missing log file returns graceful status rather than failing."""
        missing_path = self.temp_path / "does_not_exist.jsonl"
        collector = LogCollector(db=self.db, log_path=missing_path)

        res = collector.collect_once()
        self.assertEqual(res["status"], "waiting_for_file")
        self.assertFalse(res["file_exists"])
        self.assertEqual(res["records_inserted"], 0)

    def test_file_truncation_handling(self):
        """Verify collector recovers when log file is truncated/cleared."""
        # Write 3 records
        with open(self.log_path, "w", encoding="utf-8") as f:
            for i in range(3):
                f.write(json.dumps(self._create_sample_record("R1", timestamp=f"2026-10-08T12:0{i}:00Z")) + "\n")

        self.collector.collect_once()
        self.assertEqual(self.db.get_collector_metadata()["total_records"], 3)

        # Now simulate log file reset/truncation to 1 new record
        new_record = self._create_sample_record("R2", timestamp="2026-10-08T13:00:00Z")
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(new_record) + "\n")

        # Collector should detect file size < offset, reset offset, and ingest the new record
        res = self.collector.collect_once()
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["records_inserted"], 1)
        self.assertEqual(self.db.get_collector_metadata()["total_records"], 4)

    def test_analytical_queries_and_statistics(self):
        """Verify database analytical methods: latest telemetry, per-router query, stats."""
        # Insert known values for R1 and R2
        records = [
            self._create_sample_record("R1", timestamp="2026-10-08T10:00:00Z", latency=10.0),
            self._create_sample_record("R1", timestamp="2026-10-08T10:01:00Z", latency=20.0),
            self._create_sample_record("R2", timestamp="2026-10-08T10:02:00Z", latency=30.0, active_fault="Latency Spike"),
        ]
        with open(self.log_path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        self.collector.collect_once()

        # 1. Latest telemetry
        latest = self.db.get_latest_telemetry(limit=2)
        self.assertEqual(len(latest), 2)
        self.assertEqual(latest[0]["router_id"], "R2")

        # 2. Per router telemetry
        r1_records = self.db.get_telemetry_by_router("R1")
        self.assertEqual(len(r1_records), 2)
        self.assertEqual(r1_records[0]["latency"], 20.0) # Newest first

        # 3. Latest router states
        states = self.db.get_latest_router_states()
        self.assertEqual(len(states), 2)
        r2_state = next(s for s in states if s["router_id"] == "R2")
        self.assertEqual(r2_state["latency"], 30.0)
        self.assertEqual(r2_state["active_fault"], "Latency Spike")
        self.assertEqual(r2_state["total_samples"], 1)

        r1_state = next(s for s in states if s["router_id"] == "R1")
        self.assertEqual(r1_state["latency"], 20.0)
        self.assertEqual(r1_state["total_samples"], 2)

        # 4. Telemetry Statistics
        stats = self.db.get_telemetry_stats()
        self.assertEqual(stats["total_records"], 3)
        self.assertEqual(stats["router_count"], 2)
        self.assertEqual(stats["metrics"]["latency"]["min"], 10.0)
        self.assertEqual(stats["metrics"]["latency"]["max"], 30.0)
        self.assertEqual(stats["metrics"]["latency"]["avg"], 20.0)
        self.assertEqual(stats["fault_distribution"].get("Latency Spike"), 1)


class TestOpsPlatformAPI(unittest.TestCase):
    """Verifies all FastAPI REST endpoints for the Operations Platform."""

    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from network_ops_platform.backend.api import app
        cls.client = TestClient(app)

    def test_status_endpoint(self):
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ONLINE")
        self.assertTrue(data["air_gapped"])
        self.assertIn("database", data)
        self.assertIn("collector", data)

    def test_collector_status_endpoint(self):
        res = self.client.get("/api/collector/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("database_location", data)
        self.assertIn("total_imported_records", data)
        self.assertIn("number_of_routers_detected", data)

    def test_telemetry_latest_endpoint(self):
        res = self.client.get("/api/telemetry/latest?limit=10")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_telemetry_routers_endpoint(self):
        res = self.client.get("/api/telemetry/routers")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_telemetry_stats_endpoint(self):
        res = self.client.get("/api/telemetry/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_records", data)
        self.assertIn("metrics", data)


if __name__ == "__main__":
    unittest.main()

