"""
MPLS Network Simulator - Log Storage Module
Persists telemetry records locally in structured JSON Lines format.
"""
import os
import json
import threading
from typing import List, Dict, Any
from pathlib import Path


class LocalTelemetryStorage:
    def __init__(self, log_dir: str = "logs", filename: str = "telemetry.jsonl"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.filepath = self.log_dir / filename
        self._lock = threading.Lock()
        self.total_records_written = 0

        # Count existing lines if file exists
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.total_records_written = sum(1 for line in f if line.strip())
            except Exception:
                self.total_records_written = 0

    def write_record(self, record_dict: Dict[str, Any]) -> None:
        """Appends a single structured telemetry record as JSON Lines."""
        json_line = json.dumps(record_dict) + "\n"
        with self._lock:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(json_line)
                f.flush()
            self.total_records_written += 1

    def write_records_batch(self, records: List[Dict[str, Any]]) -> None:
        """Appends a batch of structured telemetry records."""
        if not records:
            return
        lines = "".join(json.dumps(r) + "\n" for r in records)
        with self._lock:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(lines)
                f.flush()
            self.total_records_written += len(records)

    def get_recent_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Reads the most recent N records from the log file."""
        if not self.filepath.exists():
            return []
        
        with self._lock:
            try:
                # Read last lines efficiently
                records = []
                with open(self.filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        line = line.strip()
                        if line:
                            try:
                                records.append(json.loads(line))
                                if len(records) >= limit:
                                    break
                            except json.JSONDecodeError:
                                continue
                return list(reversed(records))
            except Exception:
                return []

    def get_storage_stats(self) -> Dict[str, Any]:
        """Returns file size and record count for telemetry storage."""
        size_bytes = 0
        if self.filepath.exists():
            size_bytes = self.filepath.stat().st_size

        return {
            "log_path": str(self.filepath.resolve()),
            "total_records": self.total_records_written,
            "size_bytes": size_bytes,
            "size_kb": round(size_bytes / 1024, 2),
            "format": "JSON Lines (.jsonl)"
        }

    def clear_logs(self) -> None:
        """Truncates the log file."""
        with self._lock:
            with open(self.filepath, "w", encoding="utf-8") as f:
                pass
            self.total_records_written = 0
