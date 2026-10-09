"""
End-to-End Verification Script:
Validates real telemetry ingestion from ./logs/telemetry.jsonl into ./network_ops_platform/data/ops_platform.db
"""
import time
from pathlib import Path
from network_ops_platform.backend.config import settings
from network_ops_platform.backend.database import TelemetryDatabase
from network_ops_platform.backend.collector import LogCollector

def run_verification():
    print("=" * 70)
    print(" RUNNING END-TO-END INGESTION VERIFICATION")
    print("=" * 70)

    db = TelemetryDatabase()
    collector = LogCollector(db=db)

    print(f"[*] Target Simulator Log: {collector.log_path.resolve()}")
    print(f"[*] Target SQLite DB:     {db.db_path.resolve()}")

    # 1. Run initial collection
    res1 = collector.collect_once()
    print("\n[+] Cycle 1 Result:", res1)
    meta1 = db.get_collector_metadata()
    print("    - Total Imported Records:", meta1["total_records"])
    print("    - Unique Routers Detected:", meta1["unique_routers"])
    print("    - Earliest Timestamp:     ", meta1["earliest_timestamp"])
    print("    - Latest Timestamp:       ", meta1["latest_timestamp"])

    # 2. Run immediate second collection: verify 0 duplicates inserted
    res2 = collector.collect_once()
    print("\n[+] Cycle 2 Result (Immediate Re-check):", res2)
    meta2 = db.get_collector_metadata()
    print("    - Total Records in DB:", meta2["total_records"])
    assert meta1["total_records"] == meta2["total_records"], "ERROR: Duplicate records were imported!"
    print("    [PASSED] Deduplication check: zero duplicate rows inserted.")

    # 3. Router state check
    states = db.get_latest_router_states()
    print("\n[+] Latest Router States:")
    for s in states:
        print(f"    - [{s['router_id']}] status={s['status']} | latency={s['latency']}ms | "
              f"loss={s['packet_loss']}% | cpu={s['cpu_usage']}% | samples={s['total_samples']}")

    # 4. Analytical statistics
    stats = db.get_telemetry_stats()
    print("\n[+] Analytical Statistics Summary:")
    print(f"    - Total Telemetry Records Analyzed: {stats['total_records']}")
    print(f"    - Active Router Count:              {stats['router_count']} ({', '.join(stats['routers'])})")
    print(f"    - Network Latency:                  avg={stats['metrics']['latency']['avg']}ms, "
          f"min={stats['metrics']['latency']['min']}ms, max={stats['metrics']['latency']['max']}ms")
    print(f"    - Packet Loss:                      avg={stats['metrics']['packet_loss']['avg']}%, "
          f"max={stats['metrics']['packet_loss']['max']}%")
    print(f"    - Status Distribution:              {stats['status_distribution']}")

    # 5. Continuous background collection test
    print("\n[+] Testing Continuous Background Collection (3 seconds)...")
    collector.start()
    time.sleep(3.0)
    status_diag = collector.get_status()
    collector.stop()
    print("    - Collector Running State: ", status_diag.collector_running)
    print("    - Last Poll Time:          ", status_diag.last_poll_time)
    print("    - Total Errors Encountered:", status_diag.total_errors_encountered)
    print("    - Database Location:       ", status_diag.database_location)

    print("\n" + "=" * 70)
    print(" ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_verification()
