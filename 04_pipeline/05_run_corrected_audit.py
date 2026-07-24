from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import mean_absolute_error, median_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from common import LOCKED_DIR, OUTPUT_DIR, load_config, safe_r2

PARTIAL_DIR = OUTPUT_DIR / "partials"


def build_estimator(name: str, seed: int):
    if name == "Ridge":
        return Pipeline([("scale", StandardScaler()), ("model", Ridge(alpha=1.0))])
    if name == "ElasticNet":
        return Pipeline([
            ("scale", StandardScaler()),
            ("model", ElasticNet(alpha=0.01, l1_ratio=0.5, max_iter=20000, random_state=seed)),
        ])
    if name == "RandomForest":
        return RandomForestRegressor(
            n_estimators=20,
            min_samples_leaf=5,
            max_features=0.8,
            random_state=seed,
            n_jobs=1,
        )
    raise KeyError(name)


def target_lag(target: str) -> str:
    return {
        "Inward_FDI_Net_Flow_asinh": "Inward_FDI_Net_Flow_asinh_lag1",
        "Inward_FDI_Net_Flow_GDP_Pct_asinh": "Inward_FDI_Net_Flow_GDP_Pct_asinh_lag1",
        "Inward_FDI_Net_Flow_GDP_Pct": "Inward_FDI_Net_Flow_GDP_Pct_lag1",
    }[target]


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[float, float, float]:
    return (
        safe_r2(y_true, y_pred),
        float(mean_absolute_error(y_true, y_pred)),
        float(median_absolute_error(y_true, y_pred)),
    )


def distribution_fields(y_true: np.ndarray, y_pred: np.ndarray | None = None) -> dict[str, float]:
    fields = {
        "target_mean": float(np.mean(y_true)),
        "target_sd": float(np.std(y_true, ddof=1)) if len(y_true) > 1 else float("nan"),
        "target_min": float(np.min(y_true)),
        "target_p01": float(np.quantile(y_true, 0.01)),
        "target_median": float(np.median(y_true)),
        "target_p99": float(np.quantile(y_true, 0.99)),
        "target_max": float(np.max(y_true)),
    }
    if y_pred is not None:
        fields.update({
            "prediction_min": float(np.min(y_pred)),
            "prediction_median": float(np.median(y_pred)),
            "prediction_max": float(np.max(y_pred)),
        })
    return fields




def append_country_contributions(rows: list[dict[str, object]], *, entry: dict[str, object],
                                 validation: str, split_id: str, algorithm: str,
                                 predictor_type: str, predictor_name: str, test: pd.DataFrame,
                                 y_true: np.ndarray, y_pred: np.ndarray) -> None:
    """Freeze per-country sufficient statistics before any bootstrap resampling.

    These contributions permit an exact paired country-cluster bootstrap without
    resampling individual country-years or refitting models inside the loop.
    Duplicate country draws are represented by integer multiplicities later; they
    are never silently deduplicated.
    """
    frame = pd.DataFrame({
        "ISO3": test["ISO3"].astype(str).to_numpy(),
        "y_true": np.asarray(y_true, dtype=float),
        "y_pred": np.asarray(y_pred, dtype=float),
    })
    frame["y2"] = frame["y_true"] ** 2
    frame["sq_error"] = (frame["y_true"] - frame["y_pred"]) ** 2
    frame["abs_error"] = np.abs(frame["y_true"] - frame["y_pred"])
    grouped = frame.groupby("ISO3", sort=True, as_index=False).agg(
        n_rows=("y_true", "size"),
        sum_y=("y_true", "sum"),
        sum_y2=("y2", "sum"),
        sse=("sq_error", "sum"),
        sae=("abs_error", "sum"),
    )
    common = common_fields(entry, validation, split_id, test, test)
    for row in grouped.to_dict("records"):
        rows.append({
            **{key: common[key] for key in (
                "sample_id", "signal", "target_role", "target", "universe",
                "universe_type", "universe_threshold", "validation", "split_id"
            )},
            "algorithm": algorithm,
            "predictor_type": predictor_type,
            "predictor_name": predictor_name,
            **row,
        })

def common_fields(entry: dict[str, object], validation: str, split_id: str,
                  train: pd.DataFrame, test: pd.DataFrame) -> dict[str, object]:
    return {
        "sample_id": str(entry["sample_id"]),
        "signal": str(entry["signal"]),
        "target_role": str(entry["target_role"]),
        "target": str(entry["target"]),
        "universe": str(entry["universe"]),
        "universe_type": str(entry.get("universe_type", "")),
        "universe_threshold": entry.get("universe_threshold", ""),
        "validation": validation,
        "split_id": split_id,
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "train_countries": int(train["ISO3"].nunique()),
        "test_countries": int(test["ISO3"].nunique()),
    }


def record_model(rows: list[dict[str, object]], contribution_rows: list[dict[str, object]], *,
                 entry: dict[str, object], validation: str, split_id: str, algorithm: str,
                 model_name: str, train: pd.DataFrame, test: pd.DataFrame,
                 features: list[str], seed: int) -> None:
    target = str(entry["target"])
    estimator = build_estimator(algorithm, seed)
    estimator.fit(train[features], train[target])
    prediction = np.asarray(estimator.predict(test[features]), dtype=float)
    y_true = test[target].to_numpy(float)
    r2, mae, medae = evaluate_predictions(y_true, prediction)
    append_country_contributions(
        contribution_rows, entry=entry, validation=validation, split_id=split_id,
        algorithm=algorithm, predictor_type="model", predictor_name=model_name,
        test=test, y_true=y_true, y_pred=prediction,
    )
    rows.append({
        **common_fields(entry, validation, split_id, train, test),
        "algorithm": algorithm,
        "model": model_name,
        "r2": r2,
        "mae": mae,
        "median_ae": medae,
        **distribution_fields(y_true, prediction),
        "features_json": json.dumps(features),
    })


def record_benchmarks(rows: list[dict[str, object]], contribution_rows: list[dict[str, object]], *,
                      entry: dict[str, object], validation: str, split_id: str,
                      train: pd.DataFrame, test: pd.DataFrame) -> None:
    target = str(entry["target"])
    y_true = test[target].to_numpy(float)
    lag_col = target_lag(target)
    predictions = {
        "Zero_Flow": np.zeros(len(test), dtype=float),
        "Training_Mean": np.full(len(test), float(train[target].mean()), dtype=float),
        "Lagged_Flow": test[lag_col].to_numpy(float),
    }
    for benchmark, y_pred in predictions.items():
        r2, mae, medae = evaluate_predictions(y_true, y_pred)
        append_country_contributions(
            contribution_rows, entry=entry, validation=validation, split_id=split_id,
            algorithm="Benchmark", predictor_type="benchmark", predictor_name=benchmark,
            test=test, y_true=y_true, y_pred=y_pred,
        )
        rows.append({
            **common_fields(entry, validation, split_id, train, test),
            "benchmark": benchmark,
            "r2": r2,
            "mae": mae,
            "median_ae": medae,
            **distribution_fields(y_true, y_pred),
        })


def run_one(entry: dict[str, object], cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sample_id = str(entry["sample_id"])
    sample = pd.read_csv(LOCKED_DIR / str(entry["file"]))
    target = str(entry["target"])
    base_features = json.loads(str(entry["base_features_json"]))
    added_features = json.loads(str(entry["added_features_json"]))
    base_model = str(entry["base_model"])
    added_model = str(entry["added_model"])

    ordered = sample.sort_values(["ISO3", "Year", "Row_ID"]).reset_index(drop=True)
    if list(sample["Row_ID"]) != list(ordered["Row_ID"]):
        raise RuntimeError(f"Sample is not deterministically ordered: {sample_id}")
    for field in added_features + [target, "Country_Fold", "ISO3", "Year", "Row_ID"]:
        if field not in sample.columns:
            raise RuntimeError(f"Locked sample missing field {field}: {sample_id}")
        if sample[field].isna().any():
            raise RuntimeError(f"Locked sample contains missing core field {field}: {sample_id}")

    model_rows: list[dict[str, object]] = []
    benchmark_rows: list[dict[str, object]] = []
    contribution_rows: list[dict[str, object]] = []
    for fold in sorted(sample["Country_Fold"].astype(int).unique()):
        train = sample[sample["Country_Fold"].astype(int) != int(fold)].copy()
        test = sample[sample["Country_Fold"].astype(int) == int(fold)].copy()
        if len(train) < 10 or len(test) < 2:
            continue
        split_id = f"fold_{int(fold)}"
        record_benchmarks(benchmark_rows, contribution_rows, entry=entry, validation="Country_Holdout_CV",
                          split_id=split_id, train=train, test=test)
        for algorithm in cfg["algorithms"]:
            seed = int(cfg["random_seed"])
            record_model(model_rows, contribution_rows, entry=entry, validation="Country_Holdout_CV", split_id=split_id,
                         algorithm=algorithm, model_name=base_model, train=train, test=test,
                         features=base_features, seed=seed)
            record_model(model_rows, contribution_rows, entry=entry, validation="Country_Holdout_CV", split_id=split_id,
                         algorithm=algorithm, model_name=added_model, train=train, test=test,
                         features=added_features, seed=seed)

    for cutoff in cfg["future_cutoffs"]:
        train_end = int(cutoff["train_end"])
        test_start = int(cutoff["test_start"])
        train = sample[sample["Year"] <= train_end].copy()
        test = sample[sample["Year"] >= test_start].copy()
        if len(train) < 10 or len(test) < 2:
            continue
        split_id = f"train_to_{train_end}__test_from_{test_start}"
        record_benchmarks(benchmark_rows, contribution_rows, entry=entry, validation="Future_Period",
                          split_id=split_id, train=train, test=test)
        for algorithm in cfg["algorithms"]:
            seed = int(cfg["random_seed"])
            record_model(model_rows, contribution_rows, entry=entry, validation="Future_Period", split_id=split_id,
                         algorithm=algorithm, model_name=base_model, train=train, test=test,
                         features=base_features, seed=seed)
            record_model(model_rows, contribution_rows, entry=entry, validation="Future_Period", split_id=split_id,
                         algorithm=algorithm, model_name=added_model, train=train, test=test,
                         features=added_features, seed=seed)

    return pd.DataFrame(model_rows), pd.DataFrame(benchmark_rows), pd.DataFrame(contribution_rows)


def safe_name(sample_id: str) -> str:
    return sample_id.replace("/", "_").replace(" ", "_")


def finalize(registry: pd.DataFrame) -> None:
    expected = set(registry["sample_id"].astype(str))
    perf_frames, bench_frames, contribution_frames = [], [], []
    missing: list[str] = []
    for sample_id in sorted(expected):
        stem = safe_name(sample_id)
        perf_path = PARTIAL_DIR / f"performance__{stem}.csv"
        bench_path = PARTIAL_DIR / f"benchmarks__{stem}.csv"
        contribution_path = PARTIAL_DIR / f"contributions__{stem}.csv"
        if not perf_path.exists() or not bench_path.exists() or not contribution_path.exists():
            missing.append(sample_id)
            continue
        perf_frames.append(pd.read_csv(perf_path))
        bench_frames.append(pd.read_csv(bench_path))
        contribution_frames.append(pd.read_csv(contribution_path))
    if missing:
        raise RuntimeError("Missing sample-level outputs: " + "; ".join(missing))

    performance = pd.concat(perf_frames, ignore_index=True).sort_values(
        ["sample_id", "validation", "split_id", "algorithm", "model"]
    ).reset_index(drop=True)
    benchmarks = pd.concat(bench_frames, ignore_index=True).sort_values(
        ["sample_id", "validation", "split_id", "benchmark"]
    ).reset_index(drop=True)
    contributions = pd.concat(contribution_frames, ignore_index=True).sort_values(
        ["sample_id", "validation", "split_id", "algorithm", "predictor_type", "predictor_name", "ISO3"]
    ).reset_index(drop=True)
    performance.to_csv(OUTPUT_DIR / "Corrected_Model_Performance.csv", index=False)
    benchmarks.to_csv(OUTPUT_DIR / "Corrected_Benchmark_Performance.csv", index=False)
    contributions.to_csv(OUTPUT_DIR / "Bootstrap_Country_Contributions.csv", index=False)

    registry_small = registry[["sample_id", "base_model", "added_model"]].drop_duplicates()
    merged = performance.merge(registry_small, on="sample_id", how="left", validate="many_to_one")
    base_rows = merged[merged["model"] == merged["base_model"]].copy()
    added_rows = merged[merged["model"] == merged["added_model"]].copy()
    key = ["sample_id", "signal", "target_role", "target", "universe", "validation", "split_id", "algorithm"]
    delta = base_rows[key + ["r2", "mae", "median_ae", "base_model", "added_model"]].merge(
        added_rows[key + ["r2", "mae", "median_ae"]], on=key, suffixes=("_base", "_added"), validate="one_to_one"
    )
    delta["delta_r2"] = delta["r2_added"] - delta["r2_base"]
    delta["delta_mae"] = delta["mae_added"] - delta["mae_base"]
    delta["delta_median_ae"] = delta["median_ae_added"] - delta["median_ae_base"]
    delta = delta.sort_values(key).reset_index(drop=True)
    delta.to_csv(OUTPUT_DIR / "Corrected_Incremental_Delta.csv", index=False)

    summary = (
        delta.groupby(["signal", "target_role", "target", "universe", "validation"], dropna=False)
        .agg(
            comparisons=("delta_r2", "count"),
            median_delta_r2=("delta_r2", "median"),
            mean_delta_r2=("delta_r2", "mean"),
            positive_share=("delta_r2", lambda values: float((values > 0).mean())),
            median_delta_mae=("delta_mae", "median"),
            mae_improvement_share=("delta_mae", lambda values: float((values < 0).mean())),
            minimum_delta_r2=("delta_r2", "min"),
            maximum_delta_r2=("delta_r2", "max"),
        )
        .reset_index()
        .sort_values(["signal", "target_role", "universe", "validation"])
        .reset_index(drop=True)
    )
    summary.to_csv(OUTPUT_DIR / "Corrected_Incremental_Summary.csv", index=False)

    best_benchmark = (
        benchmarks.sort_values(["sample_id", "validation", "split_id", "r2"], ascending=[True, True, True, False])
        .groupby(["sample_id", "validation", "split_id"], as_index=False)
        .first()[["sample_id", "validation", "split_id", "benchmark", "r2", "mae", "median_ae"]]
        .rename(columns={
            "benchmark": "best_benchmark", "r2": "best_benchmark_r2",
            "mae": "best_benchmark_mae", "median_ae": "best_benchmark_median_ae",
        })
    )
    added_only = added_rows[key + ["r2", "mae", "median_ae", "added_model"]].copy()
    benchmark_delta = added_only.merge(
        best_benchmark, on=["sample_id", "validation", "split_id"], how="left", validate="many_to_one"
    )
    benchmark_delta["model_minus_best_benchmark_r2"] = benchmark_delta["r2"] - benchmark_delta["best_benchmark_r2"]
    benchmark_delta["model_minus_best_benchmark_mae"] = benchmark_delta["mae"] - benchmark_delta["best_benchmark_mae"]
    benchmark_delta["model_minus_best_benchmark_median_ae"] = benchmark_delta["median_ae"] - benchmark_delta["best_benchmark_median_ae"]
    benchmark_delta = benchmark_delta.sort_values(key).reset_index(drop=True)
    benchmark_delta.to_csv(OUTPUT_DIR / "Corrected_Model_vs_Best_Benchmark.csv", index=False)

    benchmark_summary = (
        benchmark_delta.groupby(["signal", "target_role", "target", "universe", "validation"], dropna=False)
        .agg(
            comparisons=("model_minus_best_benchmark_r2", "count"),
            median_model_minus_benchmark_r2=("model_minus_best_benchmark_r2", "median"),
            mean_model_minus_benchmark_r2=("model_minus_best_benchmark_r2", "mean"),
            benchmark_positive_share=("model_minus_best_benchmark_r2", lambda values: float((values > 0).mean())),
            median_model_minus_benchmark_mae=("model_minus_best_benchmark_mae", "median"),
            benchmark_mae_improvement_share=("model_minus_best_benchmark_mae", lambda values: float((values < 0).mean())),
            minimum_model_minus_benchmark_r2=("model_minus_best_benchmark_r2", "min"),
            maximum_model_minus_benchmark_r2=("model_minus_best_benchmark_r2", "max"),
        )
        .reset_index()
        .sort_values(["signal", "target_role", "universe", "validation"])
        .reset_index(drop=True)
    )
    benchmark_summary.to_csv(OUTPUT_DIR / "Corrected_Benchmark_Competitiveness_Summary.csv", index=False)

    # Split-level target/prediction audit: makes extreme raw-ratio folds visible rather than hiding them.
    audit_columns = [
        "sample_id", "signal", "target_role", "target", "universe", "validation", "split_id",
        "algorithm", "model", "test_rows", "test_countries", "r2", "mae", "median_ae",
        "target_mean", "target_sd", "target_min", "target_p01", "target_median", "target_p99", "target_max",
        "prediction_min", "prediction_median", "prediction_max",
    ]
    performance[audit_columns].to_csv(OUTPUT_DIR / "Split_Level_Target_and_Prediction_Audit.csv", index=False)

    print(summary.to_string(index=False))
    print("\nBenchmark competitiveness")
    print(benchmark_summary.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic sample-level MS2 audit or finalize all partial outputs.")
    parser.add_argument("--sample-id", help="Exact sample_id from Matched_Sample_Registry.csv")
    parser.add_argument("--finalize", action="store_true", help="Merge all sample-level outputs and build summaries")
    parser.add_argument("--list", action="store_true", help="List available sample IDs")
    args = parser.parse_args()

    cfg = load_config()
    registry = pd.read_csv(LOCKED_DIR / "Matched_Sample_Registry.csv")
    PARTIAL_DIR.mkdir(parents=True, exist_ok=True)

    if args.list:
        print("\n".join(registry["sample_id"].astype(str)))
        return
    if args.finalize:
        finalize(registry)
        return
    if not args.sample_id:
        parser.error("Provide --sample-id, --finalize, or --list")

    selected = registry[registry["sample_id"].astype(str) == args.sample_id]
    if len(selected) != 1:
        raise KeyError(f"Unknown or duplicate sample_id: {args.sample_id}")
    entry = selected.iloc[0].to_dict()
    performance, benchmarks, contributions = run_one(entry, cfg)
    stem = safe_name(str(entry["sample_id"]))
    performance.sort_values(["validation", "split_id", "algorithm", "model"]).to_csv(
        PARTIAL_DIR / f"performance__{stem}.csv", index=False
    )
    benchmarks.sort_values(["validation", "split_id", "benchmark"]).to_csv(
        PARTIAL_DIR / f"benchmarks__{stem}.csv", index=False
    )
    contributions.sort_values(["validation", "split_id", "algorithm", "predictor_type", "predictor_name", "ISO3"]).to_csv(
        PARTIAL_DIR / f"contributions__{stem}.csv", index=False
    )
    print(
        f"Completed {entry['sample_id']}: {len(performance)} model rows, "
        f"{len(benchmarks)} benchmark rows, {len(contributions)} frozen country contributions"
    )


if __name__ == "__main__":
    main()
