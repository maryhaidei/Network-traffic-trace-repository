import csv
import os
import subprocess
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
LOCUSTFILE = BASE_DIR / "locustfile.py"

HOST = os.getenv("LOADTEST_HOST", "http://localhost:8000")
USERS_LIST = [int(x.strip()) for x in os.getenv("LOCUST_USERS_LIST", "20,50,70,100").split(",") if x.strip()]
REPEATS = int(os.getenv("LOCUST_REPEATS", "10"))
SPAWN_RATE = os.getenv("LOCUST_SPAWN_RATE", "1")
RUN_TIME = os.getenv("LOCUST_RUN_TIME", "5m")
LOCUST_BIN = os.getenv("LOCUST_BIN", "locust")


def to_float(value, default=None):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def read_aggregated_stats(stats_csv: Path) -> dict:
    if not stats_csv.exists():
        raise RuntimeError("stats.csv was not created")

    with stats_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        aggregated_row = None
        for row in reader:
            if row.get("Name") == "Aggregated":
                aggregated_row = row
                break

    if aggregated_row is None:
        raise RuntimeError("Aggregated row not found in stats csv")

    total_requests = to_float(aggregated_row.get("Request Count"), 0.0)
    failures = to_float(aggregated_row.get("Failure Count"), 0.0)
    avg_response_time = to_float(aggregated_row.get("Average Response Time"))
    rps = to_float(aggregated_row.get("Requests/s"))
    p95 = to_float(aggregated_row.get("95%"))

    error_rate_pct = 0.0
    if total_requests and total_requests > 0:
        error_rate_pct = failures / total_requests * 100.0

    return {
        "processed_requests": total_requests,
        "failures": failures,
        "error_rate_pct": error_rate_pct,
        "avg_response_time_ms": avg_response_time,
        "p95_response_time_ms": p95,
        "throughput_rps": rps,
    }


def read_failures_csv(failures_csv: Path) -> list[dict]:
    if not failures_csv.exists():
        return []

    rows = []
    with failures_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                {
                    "method": row.get("Method"),
                    "name": row.get("Name"),
                    "error": row.get("Error"),
                    "occurrences": row.get("Occurrences"),
                }
            )
    return rows


def save_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        with path.open("w", encoding="utf-8", newline="") as f:
            f.write("")
        return

    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_mean_summary(run_rows: list[dict]) -> list[dict]:
    grouped = {}

    metric_fields = [
        "processed_requests",
        "failures",
        "error_rate_pct",
        "avg_response_time_ms",
        "p95_response_time_ms",
        "throughput_rps",
    ]

    for row in run_rows:
        users = row["users"]
        if users not in grouped:
            grouped[users] = {
                "users": users,
                "runs": 0,
                "failed_runs": 0,
                "metric_sums": {field: 0.0 for field in metric_fields},
                "metric_counts": {field: 0 for field in metric_fields},
            }

        g = grouped[users]
        g["runs"] += 1

        if row.get("exit_code", 0) != 0:
            g["failed_runs"] += 1

        for field in metric_fields:
            value = row.get(field)
            if isinstance(value, (int, float)):
                g["metric_sums"][field] += value
                g["metric_counts"][field] += 1

    result = []
    for users in sorted(grouped.keys()):
        g = grouped[users]
        out = {
            "users": g["users"],
            "runs": g["runs"],
            "failed_runs": g["failed_runs"],
        }

        for field in metric_fields:
            count = g["metric_counts"][field]
            out[f"{field}_mean"] = g["metric_sums"][field] / count if count > 0 else None

        result.append(out)

    return result


def run_one(users: int, repeat: int) -> tuple[dict, list[dict]]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    prefix = RESULTS_DIR / f"u{users}_run{repeat}"
    stats_csv = Path(f"{prefix}_stats.csv")
    failures_csv = Path(f"{prefix}_failures.csv")

    start_ts = datetime.now()

    cmd = [
        LOCUST_BIN,
        "-f",
        str(LOCUSTFILE),
        "--host",
        HOST,
        "--headless",
        "-u",
        str(users),
        "-r",
        str(SPAWN_RATE),
        "--run-time",
        str(RUN_TIME),
        "--csv",
        str(prefix),
    ]

    completed = subprocess.run(
        cmd,
        cwd=str(BASE_DIR.parent),
        capture_output=True,
        text=True,
    )

    end_ts = datetime.now()

    stdout_path = RESULTS_DIR / f"u{users}_run{repeat}.stdout.log"
    stderr_path = RESULTS_DIR / f"u{users}_run{repeat}.stderr.log"
    stdout_path.write_text(completed.stdout or "", encoding="utf-8")
    stderr_path.write_text(completed.stderr or "", encoding="utf-8")

    run_row = {
        "users": users,
        "repeat": repeat,
        "started_at": start_ts.isoformat(timespec="seconds"),
        "finished_at": end_ts.isoformat(timespec="seconds"),
        "exit_code": completed.returncode,
        "status": "ok" if completed.returncode == 0 else "failed",
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        "stats_csv_exists": stats_csv.exists(),
        "failures_csv_exists": failures_csv.exists(),
    }

    parse_error = None
    if stats_csv.exists():
        try:
            run_row.update(read_aggregated_stats(stats_csv))
        except Exception as e:
            parse_error = str(e)
    else:
        parse_error = "stats.csv was not created"

    if parse_error:
        run_row["parse_error"] = parse_error

    failure_rows = []
    parsed_failures = read_failures_csv(failures_csv)

    if parsed_failures:
        for row in parsed_failures:
            failure_rows.append(
                {
                    "users": users,
                    "repeat": repeat,
                    "exit_code": completed.returncode,
                    "method": row.get("method"),
                    "name": row.get("name"),
                    "error": row.get("error"),
                    "occurrences": row.get("occurrences"),
                }
            )
    elif completed.returncode != 0:
        error_text = (completed.stderr or completed.stdout or "").strip()
        if not error_text:
            error_text = "Locust finished with non-zero exit code and no failure details"
        failure_rows.append(
            {
                "users": users,
                "repeat": repeat,
                "exit_code": completed.returncode,
                "method": None,
                "name": "run_series",
                "error": error_text[-3000:],
                "occurrences": 1,
            }
        )

    return run_row, failure_rows


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    all_run_rows = []
    all_failure_rows = []

    for users in USERS_LIST:
        for repeat in range(1, REPEATS + 1):
            print(f"Running users={users}, repeat={repeat}")
            run_row, failure_rows = run_one(users, repeat)
            all_run_rows.append(run_row)
            all_failure_rows.extend(failure_rows)

    runs_csv = RESULTS_DIR / "summary_runs.csv"
    failures_csv = RESULTS_DIR / "summary_failures.csv"
    mean_csv = RESULTS_DIR / "summary_mean_by_users.csv"

    save_csv(runs_csv, all_run_rows)
    save_csv(failures_csv, all_failure_rows)
    save_csv(mean_csv, build_mean_summary(all_run_rows))

    print(f"Saved: {runs_csv}")
    print(f"Saved: {failures_csv}")
    print(f"Saved: {mean_csv}")


if __name__ == "__main__":
    main()
