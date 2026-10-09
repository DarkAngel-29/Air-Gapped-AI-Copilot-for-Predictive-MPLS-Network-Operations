"""
Network Operations Platform - Continuous Log Collector
Monitors, validates, and ingests live JSONL telemetry emitted by the MPLS Simulator.
"""
import os
import json
import time
import threading
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import ValidationError

from .config import settings
from .models import RawTelemetryInput, CollectorStatusResponse
from .database import TelemetryDatabase

logger = logging.getLogger("ops_platform.collector")


class LogCollector:
    """
    Continuous ingestion service for the MPLS Simulator telemetry log stream.
    Features offset bookmarking, file truncation handling, data validation,
    and deduplication guarantees.
    """

    STATE_OFFSET_KEY = "simulator_log_byte_offset"
    STATE_LAST_LINE_KEY = "simulator_log_last_line_number"

    def __init__(self, db: Optional[TelemetryDatabase] = None, log_path: Optional[Path] = None):
        self.db = db or TelemetryDatabase()
        self.log_path = Path(log_path) if log_path else settings.simulator_log_path

        # Threading and lifecycle controls
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Operational metrics
        self.total_lines_read = 0
        self.total_records_inserted = 0
        self.total_errors_encountered = 0
        self.last_poll_time: Optional[str] = None
        self.last_imported_timestamp: Optional[str] = None
        self.last_error: Optional[str] = None
        self.poll_interval = settings.collector_poll_interval
        self.batch_size = settings.collector_batch_size

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _get_tracked_offset(self) -> int:
        """
        Retrieves the byte offset bookmark stored in SQLite.
        """
        val = self.db.get_state(self.STATE_OFFSET_KEY, "0")
        try:
            return max(0, int(val or "0"))
        except ValueError:
            return 0

    def _save_tracked_offset(self, offset: int) -> None:
        """
        Persists the updated byte offset bookmark in SQLite.
        """
        self.db.set_state(self.STATE_OFFSET_KEY, str(offset))

    def collect_once(self) -> Dict[str, Any]:
        """
        Executes a single ingestion cycle against the telemetry log file.
        Returns a summary of the cycle's operations.
        """
        with self._lock:
            self.last_poll_time = datetime.now(timezone.utc).isoformat()

            if not self.log_path.exists():
                logger.debug("Simulator log file not found at %s. Waiting for simulator...", self.log_path)
                return {
                    "status": "waiting_for_file",
                    "file_exists": False,
                    "lines_read": 0,
                    "records_inserted": 0,
                    "errors": 0
                }

            file_size = self.log_path.stat().st_size
            last_offset = self._get_tracked_offset()

            # Handle file truncation or rotation
            if file_size < last_offset:
                logger.warning(
                    "Log file size (%d bytes) smaller than tracked offset (%d bytes). Resetting offset to 0.",
                    file_size,
                    last_offset
                )
                last_offset = 0

            # No new bytes written
            if file_size == last_offset:
                return {
                    "status": "up_to_date",
                    "file_exists": True,
                    "lines_read": 0,
                    "records_inserted": 0,
                    "errors": 0
                }

            lines_read = 0
            records_to_insert: List[RawTelemetryInput] = []
            cycle_errors = 0
            new_offset = last_offset

            try:
                with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(last_offset)

                    while True:
                        line = f.readline()
                        if not line:
                            # Reached end of file for this batch
                            break

                        lines_read += 1
                        new_offset = f.tell()

                        stripped = line.strip()
                        if not stripped:
                            continue

                        # Parse JSON line
                        try:
                            raw_data = json.loads(stripped)
                        except json.JSONDecodeError as err:
                            logger.warning("Malformed JSON in log at byte %d: %s", new_offset, err)
                            cycle_errors += 1
                            self.total_errors_encountered += 1
                            self.last_error = f"JSONDecodeError: {err}"
                            continue

                        # Validate fields against Pydantic schema
                        try:
                            record = RawTelemetryInput(**raw_data)
                            records_to_insert.append(record)
                            self.last_imported_timestamp = record.timestamp
                        except ValidationError as err:
                            logger.warning("Telemetry schema validation failed: %s", err)
                            cycle_errors += 1
                            self.total_errors_encountered += 1
                            self.last_error = f"ValidationError: {err.errors()[0]['msg'] if err.errors() else str(err)}"
                            continue

                        # Commit batch if threshold reached
                        if len(records_to_insert) >= self.batch_size:
                            inserted = self.db.insert_telemetry_batch(records_to_insert)
                            self.total_records_inserted += inserted
                            self._save_tracked_offset(new_offset)
                            records_to_insert.clear()

                # Flush remaining records
                if records_to_insert:
                    inserted = self.db.insert_telemetry_batch(records_to_insert)
                    self.total_records_inserted += inserted

                # Finalize new offset bookmark
                self._save_tracked_offset(new_offset)
                self.total_lines_read += lines_read

                return {
                    "status": "success",
                    "file_exists": True,
                    "lines_read": lines_read,
                    "records_inserted": len(records_to_insert),
                    "errors": cycle_errors,
                    "new_offset": new_offset
                }

            except Exception as e:
                logger.error("Unexpected error during telemetry ingestion: %s", e, exc_info=True)
                self.last_error = str(e)
                self.total_errors_encountered += 1
                return {
                    "status": "error",
                    "error": str(e),
                    "lines_read": lines_read,
                    "records_inserted": 0,
                    "errors": cycle_errors + 1
                }

    def _worker_loop(self) -> None:
        """
        Background polling thread loop.
        """
        logger.info("Log Collector background service started. Monitoring: %s", self.log_path)
        while not self._stop_event.is_set():
            try:
                self.collect_once()
            except Exception as e:
                logger.error("Collector loop exception: %s", e)
            self._stop_event.wait(self.poll_interval)
        logger.info("Log Collector background service stopped.")

    def start(self) -> None:
        """
        Starts the continuous collector in a background daemon thread.
        """
        if self.is_running():
            logger.warning("Log Collector is already running.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="LogCollectorWorker")
        self._thread.start()

    def stop(self, timeout: float = 3.0) -> None:
        """
        Gracefully stops the continuous collector background thread.
        """
        if not self.is_running():
            return
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
            self._thread = None

    def get_status(self) -> CollectorStatusResponse:
        """
        Returns comprehensive status for operational health and API inspection.
        """
        meta = self.db.get_collector_metadata()
        file_exists = self.log_path.exists()
        file_size = self.log_path.stat().st_size if file_exists else 0

        return CollectorStatusResponse(
            collector_running=self.is_running(),
            database_location=meta["database_location"],
            log_file_location=str(self.log_path.resolve()),
            log_file_exists=file_exists,
            log_file_size_bytes=file_size,
            total_imported_records=meta["total_records"],
            last_imported_timestamp=self.last_imported_timestamp or meta["latest_timestamp"],
            number_of_routers_detected=meta["unique_routers"],
            total_lines_read=self.total_lines_read,
            total_records_inserted=self.total_records_inserted,
            total_errors_encountered=self.total_errors_encountered,
            last_poll_time=self.last_poll_time,
            last_error=self.last_error
        )
