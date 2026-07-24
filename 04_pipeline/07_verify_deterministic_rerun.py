from __future__ import annotations

import csv
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from common import ROOT, VALIDATION_DIR

PIPELINE = ROOT / "04_pipeline"
COMPARE_DIRS = [ROOT / name for name in ("05_processed_data", "06_locked_design", "07_outputs")]

# These six files are manuscript-facing summaries or display sources. They are
# regenerated and checked separately so the analytical comparison contains the
# 202-file inherited V0.4.2 layer plus the new unit-level base-margin output.
REPORTING_ONLY_PATHS = {
    "07_outputs/Base_Model_Benchmark_Margin_Headline.csv",
    "07_outputs/Figure2b_Threshold_Sensitivity_Source.csv",
    "07_outputs/Manuscript_Table1_Data_and_Design.csv",
    "07_outputs/Manuscript_Table3_Setup_Evidence_Long.csv",
    "07_outputs/Manuscript_Table3_Setup_Evidence_Compact.csv",
    "07_outputs/Manuscript_Table4_Final_Synthesis.csv",
}


def manifest(suffix: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for directory in COMPARE_DIRS:
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            relative_path = str(path.relative_to(ROOT))
            if relative_path in REPORTING_ONLY_PATHS:
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            rows.append({
                "relative_path": relative_path,
                f"bytes_{suffix}": path.stat().st_size,
                f"sha256_{suffix}": digest,
            })
    return pd.DataFrame(rows)


def deterministic_env() -> dict[str, str]:
    env = dict(os.environ)
    env.update({
        "PYTHONHASHSEED": "0",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
    })
    return env


def run(args: list[str]) -> None:
    completed = subprocess.run([sys.executable, *args], cwd=ROOT, env=deterministic_env(), text=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        raise RuntimeError(f"Deterministic verification command failed: {args}\n{completed.stderr}")


def run_many(arglists: list[list[str]], workers: int = 2) -> None:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run, args) for args in arglists]
        for future in as_completed(futures):
            future.result()


def sample_ids() -> list[str]:
    path = ROOT / "06_locked_design" / "Matched_Sample_Registry.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        return [row["sample_id"] for row in csv.DictReader(handle)]


def main() -> None:
    first = manifest("A")
    first.to_csv(VALIDATION_DIR / "Deterministic_Manifest_A.csv", index=False)

    # Re-derive the panel, folds, matched samples, and model outputs from the included raw workbooks.
    for step in (
        "01_validate_raw_sources.py",
        "02_build_panel_v3.py",
        "03_assign_country_folds.py",
        "04_lock_samples.py",
    ):
        run([str(PIPELINE / step)])

    audit = str(PIPELINE / "05_run_corrected_audit.py")
    ids = sample_ids()
    run_many([[audit, "--sample-id", sample_id] for sample_id in ids])
    run([audit, "--finalize"])
    bootstrap = str(PIPELINE / "06_bootstrap_uncertainty.py")
    run_many([[bootstrap, "--sample-id", sample_id] for sample_id in ids])
    run([bootstrap, "--finalize"])
    run([bootstrap, "--null-check"])
    run([str(PIPELINE / "06_generate_decisions_and_coverage.py")])
    run([str(PIPELINE / "08_persistence_baseline_forensics.py")])
    run([str(PIPELINE / "07_integrate_bootstrap_verdicts.py")])
    run([str(PIPELINE / "09_generate_manuscript_reporting.py")])

    second = manifest("B")
    comparison = first.merge(second, on="relative_path", how="outer", indicator=True)
    comparison["byte_identical"] = (
        (comparison["bytes_A"] == comparison["bytes_B"])
        & (comparison["sha256_A"] == comparison["sha256_B"])
        & (comparison["_merge"] == "both")
    )
    comparison.to_csv(VALIDATION_DIR / "Reproducibility_Rerun_Comparison.csv", index=False)

    passed = int(comparison["byte_identical"].sum())
    total = int(len(comparison))
    if passed != total:
        failed = comparison.loc[~comparison["byte_identical"], "relative_path"].tolist()
        message = f"FAIL: {passed}/{total} files were byte-identical. Differences: {failed}\n"
        (VALIDATION_DIR / "Reproducibility_Rerun_Result.txt").write_text(message, encoding="utf-8")
        raise RuntimeError(message)

    message = (
        "PASS: two deterministic derivations from the included raw workbooks produced "
        f"byte-identical processed data, locked samples/folds, and corrected outputs ({passed}/{total} files).\n"
    )
    (VALIDATION_DIR / "Reproducibility_Rerun_Result.txt").write_text(message, encoding="utf-8")
    print(message, end="")


if __name__ == "__main__":
    main()
