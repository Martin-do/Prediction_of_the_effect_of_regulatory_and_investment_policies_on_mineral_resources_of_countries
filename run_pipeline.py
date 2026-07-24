from __future__ import annotations

import csv
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PIPELINE = ROOT / "04_pipeline"
GENERATED_DIRS = [ROOT / name for name in ("05_processed_data", "06_locked_design", "07_outputs", "08_validation")]


def run_step(args: list[str], log_lines: list[str]) -> None:
    command = [sys.executable, *args]
    header = f"\n=== {' '.join(str(item) for item in command)} ==="
    print(header, flush=True)
    env = dict(__import__("os").environ)
    env.update({
        "PYTHONHASHSEED": "0",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
    })
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, env=env)
    log_lines.extend([header, completed.stdout, completed.stderr])
    if completed.stdout:
        print(completed.stdout, end="", flush=True)
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr, flush=True)
    if completed.returncode != 0:
        raise subprocess.CalledProcessError(completed.returncode, command)


def reset_generated_directories() -> None:
    for directory in GENERATED_DIRS:
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)


def run_many(arglists: list[list[str]], log_lines: list[str], workers: int = 2) -> None:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_step, args, log_lines): args for args in arglists}
        for future in as_completed(futures):
            future.result()


def sample_ids() -> list[str]:
    registry = ROOT / "06_locked_design" / "Matched_Sample_Registry.csv"
    with registry.open(newline="", encoding="utf-8") as handle:
        return [row["sample_id"] for row in csv.DictReader(handle)]


def main() -> None:
    reset_generated_directories()
    started = datetime.now(timezone.utc).isoformat()
    log_lines = [f"MS2 clean pipeline run started: {started}"]

    for step in (
        "01_validate_raw_sources.py",
        "02_build_panel_v3.py",
        "03_assign_country_folds.py",
        "04_lock_samples.py",
    ):
        run_step([str(PIPELINE / step)], log_lines)

    audit_script = str(PIPELINE / "05_run_corrected_audit.py")
    ids = sample_ids()
    run_many([[audit_script, "--sample-id", sample_id] for sample_id in ids], log_lines)
    run_step([audit_script, "--finalize"], log_lines)
    bootstrap_script = str(PIPELINE / "06_bootstrap_uncertainty.py")
    run_many([[bootstrap_script, "--sample-id", sample_id] for sample_id in ids], log_lines)
    run_step([bootstrap_script, "--finalize"], log_lines)
    run_step([bootstrap_script, "--null-check"], log_lines)
    run_step([str(PIPELINE / "06_generate_decisions_and_coverage.py")], log_lines)
    run_step([str(PIPELINE / "08_persistence_baseline_forensics.py")], log_lines)
    run_step([str(PIPELINE / "07_integrate_bootstrap_verdicts.py")], log_lines)
    run_step([str(PIPELINE / "09_generate_manuscript_reporting.py")], log_lines)
    run_step([str(PIPELINE / "07_verify_deterministic_rerun.py")], log_lines)
    run_step([str(PIPELINE / "07_build_reproducibility_report.py")], log_lines)

    ended = datetime.now(timezone.utc).isoformat()
    log_lines.append(f"\nMS2 clean pipeline run completed: {ended}\n")
    (ROOT / "08_validation" / "Clean_Run_Log.txt").write_text("\n".join(log_lines), encoding="utf-8")
    print("\nPipeline completed successfully from included raw files.")


if __name__ == "__main__":
    main()
