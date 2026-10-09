"""
Network Operations Platform - SQLite Database Layer
Handles database schema initialization, indexing, deduplication, batch inserts, and analytical queries.
"""
import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from .config import settings
from .models import RawTelemetryInput

logger = logging.getLogger("ops_platform.database")


class TelemetryDatabase:
    """
    Manages local SQLite database operations for telemetry ingestion and querying.
    Enforces deduplication, indexes for fast time-series queries, and safe concurrent access.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else settings.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def get_connection(self):
        """
        Thread-safe context manager yielding a SQLite connection configured for WAL mode.
        """
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        """
        Creates required tables, indexes, and constraints if they do not exist.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Core Telemetry Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    router_id TEXT NOT NULL,
                    latency REAL NOT NULL,
                    packet_loss REAL NOT NULL,
                    jitter REAL NOT NULL,
                    bandwidth_usage REAL NOT NULL,
                    cpu_usage REAL NOT NULL,
                    memory_usage REAL NOT NULL,
                    status TEXT NOT NULL,
                    active_fault TEXT,
                    imported_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                    UNIQUE(router_id, timestamp)
                );
            """)

            # High-performance indexes for time-series and per-router lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_router_id ON telemetry(router_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_router_time ON telemetry(router_id, timestamp DESC);")

            # Checkpoint & state table for collector synchronization
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collector_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                );
            """)

            conn.commit()
            logger.info("Database initialized successfully at %s", self.db_path)

    def insert_telemetry_batch(self, records: List[RawTelemetryInput]) -> int:
        """
        Inserts a batch of validated telemetry records.
        Uses INSERT OR IGNORE to strictly enforce UNIQUE(router_id, timestamp) deduplication.
        Returns the number of genuinely new records inserted.
        """
        if not records:
            return 0

        insert_sql = """
            INSERT OR IGNORE INTO telemetry (
                timestamp, router_id, latency, packet_loss, jitter,
                bandwidth_usage, cpu_usage, memory_usage, status, active_fault
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        data = [
            (
                r.timestamp,
                r.router_id,
                r.latency,
                r.packet_loss,
                r.jitter,
                r.bandwidth_usage,
                r.cpu_usage,
                r.memory_usage,
                r.status,
                r.active_fault
            )
            for r in records
        ]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            count_before = cursor.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]
            cursor.executemany(insert_sql, data)
            conn.commit()
            count_after = cursor.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]
            inserted = count_after - count_before
            return inserted

    def get_latest_telemetry(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves the most recent N telemetry records across all routers.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM telemetry ORDER BY timestamp DESC, id DESC LIMIT ?",
                (max(1, min(limit, 1000)),)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_telemetry(
        self,
        minutes: Optional[int] = None,
        limit: int = 200,
        router_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves telemetry filtered by a rolling time window and/or router ID.
        """
        query = "SELECT * FROM telemetry WHERE 1=1"
        params: List[Any] = []

        if minutes and minutes > 0:
            cutoff = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
            query += " AND timestamp >= ?"
            params.append(cutoff)

        if router_id:
            query += " AND router_id = ?"
            params.append(router_id.strip())

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(max(1, min(limit, 2000)))

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_telemetry_by_router(self, router_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves historical telemetry for a specific router, newest first.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM telemetry WHERE router_id = ? ORDER BY timestamp DESC LIMIT ?",
                (router_id.strip(), max(1, min(limit, 1000)))
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_latest_router_states(self) -> List[Dict[str, Any]]:
        """
        Retrieves the latest telemetry snapshot for each distinct router, along with total sample counts.
        """
        sql = """
            WITH ranked AS (
                SELECT
                    id, timestamp, router_id, latency, packet_loss, jitter,
                    bandwidth_usage, cpu_usage, memory_usage, status, active_fault, imported_at,
                    ROW_NUMBER() OVER(PARTITION BY router_id ORDER BY timestamp DESC, id DESC) as rn
                FROM telemetry
            ),
            counts AS (
                SELECT router_id, COUNT(*) as sample_count
                FROM telemetry
                GROUP BY router_id
            )
            SELECT
                r.router_id,
                r.timestamp AS last_timestamp,
                r.latency,
                r.packet_loss,
                r.jitter,
                r.bandwidth_usage,
                r.cpu_usage,
                r.memory_usage,
                r.status,
                r.active_fault,
                c.sample_count AS total_samples
            FROM ranked r
            JOIN counts c ON r.router_id = c.router_id
            WHERE r.rn = 1
            ORDER BY r.router_id ASC;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]

    def get_telemetry_stats(self, minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculates aggregate network statistics: sample count, router list,
        metric min/max/avg, status distribution, and active fault counts.
        """
        where_clause = ""
        params: List[Any] = []

        if minutes and minutes > 0:
            cutoff = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
            where_clause = " WHERE timestamp >= ?"
            params.append(cutoff)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Basic aggregates
            summary_sql = f"""
                SELECT
                    COUNT(*) as total_records,
                    COUNT(DISTINCT router_id) as router_count,
                    MIN(timestamp) as earliest_timestamp,
                    MAX(timestamp) as latest_timestamp,
                    MIN(latency) as min_latency, MAX(latency) as max_latency, AVG(latency) as avg_latency,
                    MIN(packet_loss) as min_loss, MAX(packet_loss) as max_loss, AVG(packet_loss) as avg_loss,
                    MIN(jitter) as min_jitter, MAX(jitter) as max_jitter, AVG(jitter) as avg_jitter,
                    MIN(bandwidth_usage) as min_bw, MAX(bandwidth_usage) as max_bw, AVG(bandwidth_usage) as avg_bw,
                    MIN(cpu_usage) as min_cpu, MAX(cpu_usage) as max_cpu, AVG(cpu_usage) as avg_cpu,
                    MIN(memory_usage) as min_mem, MAX(memory_usage) as max_mem, AVG(memory_usage) as avg_mem
                FROM telemetry
                {where_clause}
            """
            row = cursor.execute(summary_sql, params).fetchone()

            # Distinct router IDs
            routers_sql = f"SELECT DISTINCT router_id FROM telemetry {where_clause} ORDER BY router_id"
            routers = [r[0] for r in cursor.execute(routers_sql, params).fetchall()]

            # Status distribution
            status_sql = f"""
                SELECT status, COUNT(*) as cnt
                FROM telemetry
                {where_clause}
                GROUP BY status
            """
            status_dist = {r["status"]: r["cnt"] for r in cursor.execute(status_sql, params).fetchall()}

            # Active fault distribution
            fault_sql = f"""
                SELECT active_fault, COUNT(*) as cnt
                FROM telemetry
                WHERE active_fault IS NOT NULL { 'AND timestamp >= ?' if minutes else '' }
                GROUP BY active_fault
            """
            fault_dist = {r["active_fault"]: r["cnt"] for r in cursor.execute(fault_sql, params).fetchall()}

        if not row or row["total_records"] == 0:
            return {
                "total_records": 0,
                "router_count": 0,
                "routers": [],
                "earliest_timestamp": None,
                "latest_timestamp": None,
                "time_window_minutes": minutes,
                "metrics": {
                    k: {"min": 0.0, "max": 0.0, "avg": 0.0}
                    for k in ["latency", "packet_loss", "jitter", "bandwidth_usage", "cpu_usage", "memory_usage"]
                },
                "status_distribution": {},
                "fault_distribution": {}
            }

        def _fmt(min_val, max_val, avg_val):
            return {
                "min": round(min_val or 0.0, 2),
                "max": round(max_val or 0.0, 2),
                "avg": round(avg_val or 0.0, 2),
            }

        return {
            "total_records": row["total_records"],
            "router_count": row["router_count"],
            "routers": routers,
            "earliest_timestamp": row["earliest_timestamp"],
            "latest_timestamp": row["latest_timestamp"],
            "time_window_minutes": minutes,
            "metrics": {
                "latency": _fmt(row["min_latency"], row["max_latency"], row["avg_latency"]),
                "packet_loss": _fmt(row["min_loss"], row["max_loss"], row["avg_loss"]),
                "jitter": _fmt(row["min_jitter"], row["max_jitter"], row["avg_jitter"]),
                "bandwidth_usage": _fmt(row["min_bw"], row["max_bw"], row["avg_bw"]),
                "cpu_usage": _fmt(row["min_cpu"], row["max_cpu"], row["avg_cpu"]),
                "memory_usage": _fmt(row["min_mem"], row["max_mem"], row["avg_mem"]),
            },
            "status_distribution": status_dist,
            "fault_distribution": fault_dist
        }

    def get_collector_metadata(self) -> Dict[str, Any]:
        """
        Returns high-level statistics for operations diagnostics.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            total_records = cursor.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]
            unique_routers = cursor.execute("SELECT COUNT(DISTINCT router_id) FROM telemetry").fetchone()[0]
            time_row = cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM telemetry").fetchone()
            earliest_time = time_row[0] if time_row else None
            latest_time = time_row[1] if time_row else None

        db_size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0

        return {
            "database_location": str(self.db_path.resolve()),
            "database_size_bytes": db_size_bytes,
            "total_records": total_records,
            "unique_routers": unique_routers,
            "earliest_timestamp": earliest_time,
            "latest_timestamp": latest_time
        }

    def get_state(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieves a persistent collector state value by key.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute("SELECT value FROM collector_state WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default

    def set_state(self, key: str, value: str) -> None:
        """
        Sets or updates a persistent collector state value.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO collector_state (key, value, updated_at)
                VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at;
            """, (key, str(value)))
            conn.commit()
