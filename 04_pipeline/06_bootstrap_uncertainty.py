from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from common import LOCKED_DIR, OUTPUT_DIR, load_config


def stable_seed(base_seed: int, *parts: object) -> int:
    text = ":".join([str(base_seed), *[str(p) for p in parts]])
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def pooled_stats(frame: pd.DataFrame, predictor_name: str) -> dict[str, float]:
    sub = frame[frame["predictor_name"] == predictor_name]
    n = float(sub["n_rows"].sum())
    sy = float(sub["sum_y"].sum())
    sy2 = float(sub["sum_y2"].sum())
    sse = float(sub["sse"].sum())
    sae = float(sub["sae"].sum())
    sst = sy2 - (sy * sy / n) if n > 0 else np.nan
    r2 = 1.0 - sse / sst if sst > 0 else np.nan
    mae = sae / n if n > 0 else np.nan
    return {"n": n, "sum_y": sy, "sum_y2": sy2, "sse": sse, "sae": sae, "sst": sst, "r2": r2, "mae": mae}


def align_pair(frame: pd.DataFrame, left: str, right: str) -> pd.DataFrame:
    cols = ["ISO3", "n_rows", "sum_y", "sum_y2", "sse", "sae"]
    a = frame[frame["predictor_name"] == left][cols].copy()
    b = frame[frame["predictor_name"] == right][cols].copy()
    pair = a.merge(b, on="ISO3", suffixes=("_left", "_right"), validate="one_to_one")
    for col in ("n_rows", "sum_y", "sum_y2"):
        if not np.allclose(pair[f"{col}_left"], pair[f"{col}_right"], rtol=0, atol=1e-10):
            raise RuntimeError(f"Paired bootstrap mismatch in {col}: {left} vs {right}")
    return pair.sort_values("ISO3").reset_index(drop=True)


def bootstrap_pair(pair: pd.DataFrame, replicates: int, seed: int, counts: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    """Exact paired country-cluster bootstrap using frozen country contributions.

    Each replicate draws exactly N countries with replacement. Multiplicities from
    duplicate draws are retained in the multinomial counts and applied identically
    to the left and right models. No country-year is sampled independently.
    """
    n_countries = len(pair)
    if n_countries < 2:
        return np.full(replicates, np.nan), np.full(replicates, np.nan), {}
    if counts is None:
        rng = np.random.default_rng(seed)
        counts = rng.multinomial(n_countries, np.full(n_countries, 1.0 / n_countries), size=replicates)
    if counts.shape != (replicates, n_countries):
        raise RuntimeError(f"Shared bootstrap draw matrix has shape {counts.shape}, expected {(replicates, n_countries)}")
    if not np.all(counts.sum(axis=1) == n_countries):
        raise RuntimeError("Bootstrap did not draw exactly N countries per replicate")

    n = counts @ pair["n_rows_left"].to_numpy(float)
    sy = counts @ pair["sum_y_left"].to_numpy(float)
    sy2 = counts @ pair["sum_y2_left"].to_numpy(float)
    sst = sy2 - (sy * sy / n)
    sse_left = counts @ pair["sse_left"].to_numpy(float)
    sse_right = counts @ pair["sse_right"].to_numpy(float)
    sae_left = counts @ pair["sae_left"].to_numpy(float)
    sae_right = counts @ pair["sae_right"].to_numpy(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        r2_left = 1.0 - sse_left / sst
        r2_right = 1.0 - sse_right / sst
        mae_left = sae_left / n
        mae_right = sae_right / n
    delta_r2 = r2_right - r2_left
    delta_mae = mae_right - mae_left
    distinct = (counts > 0).sum(axis=1)
    diagnostics = {
        "countries_N": int(n_countries),
        "replicates": int(replicates),
        "draws_min": int(counts.sum(axis=1).min()),
        "draws_max": int(counts.sum(axis=1).max()),
        "distinct_countries_min": int(distinct.min()),
        "distinct_countries_median": float(np.median(distinct)),
        "distinct_countries_max": int(distinct.max()),
        "duplicate_draws_median": float(np.median(n_countries - distinct)),
        "all_replicates_exact_N_draws": bool(np.all(counts.sum(axis=1) == n_countries)),
        "draw_count_matrix_sha256": hashlib.sha256(counts.tobytes()).hexdigest(),
    }
    return delta_r2, delta_mae, diagnostics


def interval(values: np.ndarray, ci_level: float) -> tuple[float, float]:
    alpha = (1.0 - ci_level) / 2.0
    valid = values[np.isfinite(values)]
    if len(valid) == 0:
        return np.nan, np.nan
    return float(np.quantile(valid, alpha)), float(np.quantile(valid, 1.0 - alpha))


def classify_unit(*, countries: int, rows: int, median: float, ci_low: float, ci_high: float,
                  p_gt_zero: float, p_gt_material: float, cfg: dict) -> str:
    b = cfg["bootstrap"]
    if countries < int(b["minimum_countries"]) or rows < int(b["minimum_rows"]):
        return "Coverage-limited"
    if ci_low > 0 and p_gt_material >= float(b["material_probability"]):
        return "Supported and practically material"
    if median > 0 and p_gt_zero >= float(b["directional_probability"]):
        return "Directionally positive but marginal"
    if ci_high <= 0 or p_gt_zero <= (1.0 - float(b["directional_probability"])):
        return "Unsupported"
    return "Setup-dependent"


def summarize_unit(meta: dict[str, object], delta_r2: np.ndarray, delta_mae: np.ndarray,
                   point_delta_r2: float, point_delta_mae: float, diagnostics: dict[str, object], cfg: dict,
                   comparison_type: str, left_name: str, right_name: str) -> dict[str, object]:
    b = cfg["bootstrap"]
    ci_low, ci_high = interval(delta_r2, float(b["ci_level"]))
    mae_low, mae_high = interval(delta_mae, float(b["ci_level"]))
    valid = delta_r2[np.isfinite(delta_r2)]
    practical = float(b["material_threshold_delta_r2"])
    med = float(np.median(valid)) if len(valid) else np.nan
    p0 = float(np.mean(valid > 0)) if len(valid) else np.nan
    pm = float(np.mean(valid > practical)) if len(valid) else np.nan
    verdict = classify_unit(
        countries=int(diagnostics.get("countries_N", 0)), rows=int(meta["test_rows"]), median=med,
        ci_low=ci_low, ci_high=ci_high, p_gt_zero=p0, p_gt_material=pm, cfg=cfg,
    )
    return {
        **meta,
        "comparison_type": comparison_type,
        "left_predictor": left_name,
        "right_predictor": right_name,
        "bootstrap_seed": int(meta["bootstrap_seed"]),
        "bootstrap_replicates": int(b["replicates"]),
        "point_delta_r2": point_delta_r2,
        "bootstrap_median_delta_r2": med,
        "bootstrap_mean_delta_r2": float(np.mean(valid)) if len(valid) else np.nan,
        "bootstrap_ci_low_delta_r2": ci_low,
        "bootstrap_ci_high_delta_r2": ci_high,
        "bootstrap_median_minus_point_delta_r2": med - point_delta_r2,
        "bootstrap_abs_median_minus_point_delta_r2": abs(med - point_delta_r2),
        "p_delta_r2_gt_0": p0,
        "p_delta_r2_gt_0p0025": float(np.mean(valid > 0.0025)) if len(valid) else np.nan,
        "p_delta_r2_gt_0p005": float(np.mean(valid > 0.005)) if len(valid) else np.nan,
        "p_delta_r2_gt_0p01": float(np.mean(valid > 0.01)) if len(valid) else np.nan,
        "point_delta_mae": point_delta_mae,
        "bootstrap_median_delta_mae": float(np.median(delta_mae[np.isfinite(delta_mae)])),
        "bootstrap_ci_low_delta_mae": mae_low,
        "bootstrap_ci_high_delta_mae": mae_high,
        "five_way_unit_verdict": verdict,
        **diagnostics,
    }


def unit_frame(contributions: pd.DataFrame, sample_id: str, validation: str, split_id: str,
               algorithm: str) -> pd.DataFrame:
    frame = contributions[
        (contributions["sample_id"] == sample_id)
        & (contributions["validation"] == validation)
        & (contributions["algorithm"].isin([algorithm, "Benchmark"]))
    ].copy()
    if validation == "Future_Period":
        frame = frame[frame["split_id"] == split_id].copy()
    else:
        # OOF predictions: each country belongs to exactly one persisted holdout fold.
        frame = frame[frame["validation"] == "Country_Holdout_CV"].copy()
        frame["split_id"] = "OOF_ALL_FOLDS"
        keys = [
            "sample_id", "signal", "target_role", "target", "universe", "universe_type",
            "universe_threshold", "validation", "split_id", "algorithm", "predictor_type",
            "predictor_name", "ISO3",
        ]
        frame = frame.groupby(keys, dropna=False, as_index=False).agg(
            n_rows=("n_rows", "sum"), sum_y=("sum_y", "sum"), sum_y2=("sum_y2", "sum"),
            sse=("sse", "sum"), sae=("sae", "sum"),
        )
    return frame


def strongest_benchmark(frame: pd.DataFrame) -> str:
    names = frame.loc[frame["predictor_type"] == "benchmark", "predictor_name"].unique()
    scores = [(name, pooled_stats(frame, str(name))["r2"]) for name in names]
    return str(sorted(scores, key=lambda x: (-x[1], x[0]))[0][0])


def build_threshold_curve(summary_meta: dict[str, object], values: np.ndarray, cfg: dict) -> list[dict[str, object]]:
    b = cfg["bootstrap"]
    thresholds = np.arange(float(b["threshold_min"]), float(b["threshold_max"]) + 1e-12,
                           float(b["threshold_step"]))
    valid = values[np.isfinite(values)]
    return [{**summary_meta, "threshold_delta_r2": float(t), "p_delta_r2_gt_threshold": float(np.mean(valid > t))}
            for t in thresholds]


def permute_within_year(frame: pd.DataFrame, column: str, rng: np.random.Generator) -> pd.DataFrame:
    result = frame.copy()
    for _, idx in result.groupby("Year", sort=True).groups.items():
        idx = np.asarray(list(idx), dtype=int)
        values = result.loc[idx, column].to_numpy(copy=True)
        result.loc[idx, column] = values[rng.permutation(len(values))]
    return result


def ridge_model() -> Pipeline:
    return Pipeline([("scale", StandardScaler()), ("model", Ridge(alpha=1.0))])


def raw_contribution(test: pd.DataFrame, y_pred: np.ndarray) -> pd.DataFrame:
    f = pd.DataFrame({"ISO3": test["ISO3"].astype(str).to_numpy(), "y": test["__y__"].to_numpy(float),
                      "pred": np.asarray(y_pred, dtype=float)})
    f["y2"] = f["y"] ** 2
    f["sse"] = (f["y"] - f["pred"]) ** 2
    f["sae"] = np.abs(f["y"] - f["pred"])
    return f.groupby("ISO3", as_index=False).agg(n_rows=("y", "size"), sum_y=("y", "sum"),
                                                   sum_y2=("y2", "sum"), sse=("sse", "sum"), sae=("sae", "sum"))


def null_signal_check(registry: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    settings = cfg["bootstrap"]["null_signal"]
    per_rows: list[dict[str, object]] = []
    pooled_by_signal: dict[str, list[np.ndarray]] = {}
    selected = registry[
        (registry["target_role"] == settings["target_role"])
        & (registry["universe"] == settings["universe"])
    ].copy()
    for _, entry in selected.iterrows():
        sample = pd.read_csv(LOCKED_DIR / str(entry["file"]))
        target = str(entry["target"])
        signal = str(entry["signal"])
        base_features = json.loads(str(entry["base_features_json"]))
        added_features = json.loads(str(entry["added_features_json"]))
        pooled_by_signal.setdefault(signal, [])
        for perm in range(int(settings["permutations"])):
            base_parts, null_parts = [], []
            rng_perm = np.random.default_rng(stable_seed(int(settings["seed"]), signal, perm, "permutation"))
            for fold in sorted(sample["Country_Fold"].astype(int).unique()):
                train = sample[sample["Country_Fold"].astype(int) != fold].copy()
                test = sample[sample["Country_Fold"].astype(int) == fold].copy()
                train["__y__"] = train[target]
                test["__y__"] = test[target]
                base = ridge_model().fit(train[base_features], train[target])
                base_pred = base.predict(test[base_features])
                train_null = permute_within_year(train, signal, rng_perm)
                test_null = permute_within_year(test, signal, rng_perm)
                added = ridge_model().fit(train_null[added_features], train_null[target])
                null_pred = added.predict(test_null[added_features])
                base_parts.append(raw_contribution(test, base_pred))
                null_parts.append(raw_contribution(test, null_pred))
            base_c = pd.concat(base_parts).groupby("ISO3", as_index=False).sum(numeric_only=True)
            null_c = pd.concat(null_parts).groupby("ISO3", as_index=False).sum(numeric_only=True)
            pair = base_c.merge(null_c, on="ISO3", suffixes=("_left", "_right"), validate="one_to_one").sort_values("ISO3")
            seed = stable_seed(int(settings["seed"]), signal, perm, "bootstrap")
            dr2, _, diag = bootstrap_pair(pair, int(settings["bootstrap_replicates_per_permutation"]), seed)
            pooled_by_signal[signal].append(dr2)
            per_rows.append({
                "signal": signal, "permutation": perm, "permutation_seed": stable_seed(int(settings["seed"]), signal, perm, "permutation"),
                "bootstrap_seed": seed, "countries_N": diag["countries_N"],
                "bootstrap_replicates": int(settings["bootstrap_replicates_per_permutation"]),
                "bootstrap_median_delta_r2": float(np.nanmedian(dr2)),
                "p_delta_r2_gt_0": float(np.nanmean(dr2 > 0)),
                "ci_low_delta_r2": interval(dr2, float(cfg["bootstrap"]["ci_level"]))[0],
                "ci_high_delta_r2": interval(dr2, float(cfg["bootstrap"]["ci_level"]))[1],
                "exact_N_draws": diag["all_replicates_exact_N_draws"],
            })
    summaries = []
    for signal, arrays in pooled_by_signal.items():
        pooled = np.concatenate(arrays)
        low, high = interval(pooled, float(cfg["bootstrap"]["ci_level"]))
        summaries.append({
            "signal": signal,
            "null_permutations": int(settings["permutations"]),
            "bootstrap_replicates_per_permutation": int(settings["bootstrap_replicates_per_permutation"]),
            "pooled_null_draws": int(len(pooled)),
            "pooled_null_median_delta_r2": float(np.nanmedian(pooled)),
            "pooled_null_ci_low_delta_r2": low,
            "pooled_null_ci_high_delta_r2": high,
            "pooled_null_p_delta_r2_gt_0": float(np.nanmean(pooled > 0)),
            "expected_probability_under_null": 0.5,
            "absolute_distance_from_0p5": abs(float(np.nanmean(pooled > 0)) - 0.5),
            "sanity_interpretation": "Near 0.5 is expected; material deviation triggers review rather than automatic validation.",
        })
    return pd.DataFrame(per_rows), pd.DataFrame(summaries)


def aggregate_setup_verdicts(unit_summary: pd.DataFrame, registry: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    rows = []
    candidate = unit_summary[unit_summary["comparison_type"] == "signal_increment"].copy()
    order = cfg["five_way_verdict_scheme"]
    for sample_id, group in candidate.groupby("sample_id", sort=True):
        entry = registry[registry["sample_id"] == sample_id].iloc[0]
        counts = group["five_way_unit_verdict"].value_counts()
        total = len(group)
        material = int(counts.get("Supported and practically material", 0))
        marginal = int(counts.get("Directionally positive but marginal", 0))
        unsupported = int(counts.get("Unsupported", 0))
        coverage = int(counts.get("Coverage-limited", 0))
        positive = material + marginal
        if coverage == total:
            verdict = "Coverage-limited"
        elif material / total >= 0.6 and unsupported == 0:
            verdict = "Supported and practically material"
        elif positive / total >= 0.6 and unsupported == 0:
            verdict = "Directionally positive but marginal"
        elif unsupported / total >= 0.8 and material == 0:
            verdict = "Unsupported"
        else:
            verdict = "Setup-dependent"
        rows.append({
            "sample_id": sample_id, "signal": entry["signal"], "target_role": entry["target_role"],
            "target": entry["target"], "universe": entry["universe"],
            "bootstrap_units": total, "material_units": material, "marginal_units": marginal,
            "setup_dependent_units": int(counts.get("Setup-dependent", 0)),
            "unsupported_units": unsupported, "coverage_limited_units": coverage,
            "positive_or_better_share": positive / total if total else np.nan,
            "bootstrap_five_way_setup_verdict": verdict,
            "verdict_scheme_order": " | ".join(order),
        })
    return pd.DataFrame(rows)


def final_role_table(setup_summary: pd.DataFrame) -> pd.DataFrame:
    rows = [{
        "variable_or_block": "Core macroeconomic block",
        "decision_role": "Predictive control block",
        "five_way_classification": "Not classified as a candidate weighted signal",
        "interpretation": "GDP, population, inflation and electricity access define the control baseline; predictive usefulness does not automatically justify normative weighting.",
    }]
    for signal, group in setup_summary.groupby("signal", sort=True):
        verdicts = set(group["bootstrap_five_way_setup_verdict"])
        if verdicts == {"Coverage-limited"}:
            final = "Coverage-limited"
        elif verdicts == {"Unsupported"}:
            final = "Unsupported"
        elif verdicts.issubset({"Supported and practically material", "Directionally positive but marginal"}):
            final = "Directionally positive but marginal" if "Directionally positive but marginal" in verdicts else "Supported and practically material"
        else:
            final = "Setup-dependent"
        rows.append({
            "variable_or_block": signal,
            "decision_role": "Candidate pre-weighting signal",
            "five_way_classification": final,
            "interpretation": "Read across all prespecified targets, universes, algorithms and validation geometries; no single favourable setup controls the classification.",
        })
    rows.extend([
        {"variable_or_block": "CPI and restricted policy indicators", "decision_role": "Appendix sensitivity variables",
         "five_way_classification": "Coverage-limited", "interpretation": "Not admitted to the core ladder without traceable provenance and adequate country-time support."},
        {"variable_or_block": "Legacy inward FDI stock target", "decision_role": "Forensic exhibit only",
         "five_way_classification": "Unsupported", "interpretation": "Not admissible as an annual-flow outcome; retained solely to document target-provenance failure."},
    ])
    return pd.DataFrame(rows)



def paired_label_swap_calibration(registry: pd.DataFrame, contributions: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Symmetry calibration for the paired resampling arithmetic.

    This is separate from the permuted-signal placebo. Within each country, the
    base/added labels are randomly swapped under a sharp exchangeability null;
    a correctly paired implementation should yield P(delta R2 > 0) near 0.5.
    """
    settings = cfg["bootstrap"]["null_signal"]
    rows = []
    selected = registry[(registry["target_role"] == settings["target_role"]) &
                        (registry["universe"] == settings["universe"])]
    reps = 10000
    for _, entry in selected.iterrows():
        sample_id = str(entry["sample_id"]); base = str(entry["base_model"]); added = str(entry["added_model"])
        frame = unit_frame(contributions, sample_id, "Country_Holdout_CV", "OOF_ALL_FOLDS", "Ridge")
        pair = align_pair(frame[frame["algorithm"] == "Ridge"], base, added)
        n_countries = len(pair)
        rng = np.random.default_rng(stable_seed(int(settings["seed"]), str(entry["signal"]), "label_swap"))
        counts = rng.multinomial(n_countries, np.full(n_countries, 1.0 / n_countries), size=reps)
        swaps = rng.integers(0, 2, size=(reps, n_countries), dtype=np.int8)
        n = counts @ pair["n_rows_left"].to_numpy(float)
        sy = counts @ pair["sum_y_left"].to_numpy(float)
        sy2 = counts @ pair["sum_y2_left"].to_numpy(float)
        sst = sy2 - sy * sy / n
        sse_l = pair["sse_left"].to_numpy(float); sse_r = pair["sse_right"].to_numpy(float)
        left_matrix = np.where(swaps == 1, sse_r, sse_l)
        right_matrix = np.where(swaps == 1, sse_l, sse_r)
        sse_left = np.sum(counts * left_matrix, axis=1)
        sse_right = np.sum(counts * right_matrix, axis=1)
        delta = (1.0 - sse_right / sst) - (1.0 - sse_left / sst)
        low, high = interval(delta, float(cfg["bootstrap"]["ci_level"]))
        p0 = float(np.mean(delta > 0))
        rows.append({
            "signal": str(entry["signal"]), "calibration_replicates": reps,
            "countries_N": n_countries, "median_delta_r2": float(np.median(delta)),
            "ci_low_delta_r2": low, "ci_high_delta_r2": high,
            "p_delta_r2_gt_0": p0, "absolute_distance_from_0p5": abs(p0 - 0.5),
            "all_replicates_exact_N_draws": bool(np.all(counts.sum(axis=1) == n_countries)),
            "calibration_interpretation": "Paired label-swap symmetry check; P(delta>0) should be near 0.5.",
        })
    return pd.DataFrame(rows)

def safe_name(value: str) -> str:
    return value.replace("/", "_").replace(" ", "_")


def run_sample(entry: pd.Series, contributions: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    b = cfg["bootstrap"]
    rows, curves, diagnostics_rows = [], [], []
    sample_id = str(entry["sample_id"])
    base = str(entry["base_model"])
    added = str(entry["added_model"])
    for validation in ("Country_Holdout_CV", "Future_Period"):
        split_ids = ["OOF_ALL_FOLDS"] if validation == "Country_Holdout_CV" else sorted(
            contributions.loc[(contributions["sample_id"] == sample_id) &
                              (contributions["validation"] == validation), "split_id"].unique()
        )
        for split_id in split_ids:
            shared_counts = None
            shared_seed = stable_seed(int(b["seed"]), sample_id, validation, split_id, "shared_country_draws")
            for algorithm in cfg["algorithms"]:
                frame = unit_frame(contributions, sample_id, validation, split_id, algorithm)
                if frame.empty:
                    continue
                meta_base = {
                    "sample_id": sample_id, "signal": str(entry["signal"]),
                    "target_role": str(entry["target_role"]), "target": str(entry["target"]),
                    "universe": str(entry["universe"]), "validation": validation,
                    "split_id": split_id, "algorithm": algorithm,
                    "test_rows": int(frame[frame["predictor_name"] == added]["n_rows"].sum()),
                    "test_countries": int(frame[frame["predictor_name"] == added]["ISO3"].nunique()),
                }
                seed = shared_seed
                meta = {**meta_base, "bootstrap_seed": seed}
                pair = align_pair(frame[frame["algorithm"] == algorithm], base, added)
                if shared_counts is None:
                    rng_shared = np.random.default_rng(shared_seed)
                    shared_counts = rng_shared.multinomial(
                        len(pair), np.full(len(pair), 1.0 / len(pair)), size=int(b["replicates"])
                    )
                if shared_counts.shape[1] != len(pair):
                    raise RuntimeError("Algorithms do not share identical country bootstrap units")
                dr2, dmae, diag = bootstrap_pair(pair, int(b["replicates"]), shared_seed, counts=shared_counts)
                point_base = pooled_stats(frame[frame["algorithm"] == algorithm], base)
                point_added = pooled_stats(frame[frame["algorithm"] == algorithm], added)
                summary = summarize_unit(meta, dr2, dmae, point_added["r2"] - point_base["r2"],
                                         point_added["mae"] - point_base["mae"], diag, cfg,
                                         "signal_increment", base, added)
                rows.append(summary)
                curves.extend(build_threshold_curve({k: summary[k] for k in (
                    "sample_id", "signal", "target_role", "universe", "validation", "split_id",
                    "algorithm", "comparison_type")}, dr2, cfg))
                diagnostics_rows.append({k: summary[k] for k in (
                    "sample_id", "signal", "target_role", "universe", "validation", "split_id",
                    "algorithm", "comparison_type", "countries_N", "replicates", "draws_min", "draws_max",
                    "distinct_countries_min", "distinct_countries_median", "distinct_countries_max",
                    "duplicate_draws_median", "all_replicates_exact_N_draws", "draw_count_matrix_sha256")})

                best = strongest_benchmark(frame)
                benchmark_frame = frame[(frame["algorithm"] == "Benchmark") | (frame["algorithm"] == algorithm)]
                seed_b = shared_seed
                meta_b = {**meta_base, "bootstrap_seed": seed_b}
                pair_b = align_pair(benchmark_frame, best, added)
                br2, bmae, diag_b = bootstrap_pair(pair_b, int(b["replicates"]), seed_b, counts=shared_counts)
                point_bench = pooled_stats(benchmark_frame, best)
                summary_b = summarize_unit(meta_b, br2, bmae, point_added["r2"] - point_bench["r2"],
                                           point_added["mae"] - point_bench["mae"], diag_b, cfg,
                                           "added_model_vs_strongest_benchmark", best, added)
                rows.append(summary_b)
                curves.extend(build_threshold_curve({k: summary_b[k] for k in (
                    "sample_id", "signal", "target_role", "universe", "validation", "split_id",
                    "algorithm", "comparison_type")}, br2, cfg))
                diagnostics_rows.append({k: summary_b[k] for k in (
                    "sample_id", "signal", "target_role", "universe", "validation", "split_id",
                    "algorithm", "comparison_type", "countries_N", "replicates", "draws_min", "draws_max",
                    "distinct_countries_min", "distinct_countries_median", "distinct_countries_max",
                    "duplicate_draws_median", "all_replicates_exact_N_draws", "draw_count_matrix_sha256")})
    return pd.DataFrame(rows), pd.DataFrame(curves), pd.DataFrame(diagnostics_rows)


def finalize_outputs(registry: pd.DataFrame, cfg: dict) -> None:
    partial = OUTPUT_DIR / "bootstrap_partials"
    summaries, curves, diagnostics = [], [], []
    missing = []
    for sample_id in registry["sample_id"].astype(str):
        stem = safe_name(sample_id)
        paths = [partial / f"summary__{stem}.csv", partial / f"curve__{stem}.csv", partial / f"diagnostics__{stem}.csv"]
        if not all(path.exists() for path in paths):
            missing.append(sample_id); continue
        summaries.append(pd.read_csv(paths[0])); curves.append(pd.read_csv(paths[1])); diagnostics.append(pd.read_csv(paths[2]))
    if missing:
        raise RuntimeError("Missing bootstrap partials: " + "; ".join(missing))
    unit_summary = pd.concat(summaries, ignore_index=True).sort_values([
        "comparison_type", "signal", "target_role", "universe", "validation", "split_id", "algorithm"
    ]).reset_index(drop=True)
    unit_summary.to_csv(OUTPUT_DIR / "Bootstrap_Unit_Summary.csv", index=False)
    pd.concat(curves, ignore_index=True).sort_values([
        "comparison_type", "signal", "target_role", "universe", "validation", "split_id", "algorithm", "threshold_delta_r2"
    ]).to_csv(OUTPUT_DIR / "Bootstrap_Threshold_Probability_Curve.csv", index=False)
    pd.concat(diagnostics, ignore_index=True).sort_values([
        "comparison_type", "signal", "target_role", "universe", "validation", "split_id", "algorithm"
    ]).to_csv(OUTPUT_DIR / "Bootstrap_Draw_Diagnostics.csv", index=False)

    alignment = unit_summary[[
        "sample_id", "signal", "target_role", "universe", "validation", "split_id", "algorithm",
        "comparison_type", "point_delta_r2", "bootstrap_median_delta_r2",
        "bootstrap_median_minus_point_delta_r2", "bootstrap_abs_median_minus_point_delta_r2",
    ]].copy()
    alignment["alignment_flag"] = np.where(alignment["bootstrap_abs_median_minus_point_delta_r2"] <= 0.005,
                                             "Within_0.005", "Review")
    alignment.to_csv(OUTPUT_DIR / "Bootstrap_Point_Estimate_Alignment.csv", index=False)
    setup_summary = aggregate_setup_verdicts(unit_summary, registry, cfg)
    setup_summary.to_csv(OUTPUT_DIR / "Bootstrap_Five_Way_Setup_Verdicts.csv", index=False)
    final_role_table(setup_summary).to_csv(OUTPUT_DIR / "Final_Signal_Role_and_Admissibility.csv", index=False)

    b = cfg["bootstrap"]
    protocol = pd.DataFrame([
        {"parameter": "cluster_unit", "value": "ISO3 country; all country-years move together"},
        {"parameter": "paired_design", "value": "same country multiplicities applied to base and added model within every replicate"},
        {"parameter": "country_draws_per_replicate", "value": "exactly N countries with replacement, where N is the number of test countries"},
        {"parameter": "duplicate_handling", "value": "retained as integer multiplicities; never deduplicated"},
        {"parameter": "frozen_contributions", "value": "per-country n, sum(y), sum(y^2), SSE and SAE frozen before resampling"},
        {"parameter": "bootstrap_seed", "value": int(b["seed"])},
        {"parameter": "replicates", "value": int(b["replicates"])},
        {"parameter": "ci_level", "value": float(b["ci_level"])},
        {"parameter": "threshold_curve", "value": f"{b['threshold_min']} to {b['threshold_max']} by {b['threshold_step']}"},
        {"parameter": "null_seed", "value": int(b["null_signal"]["seed"])},
        {"parameter": "null_permutations", "value": int(b["null_signal"]["permutations"])},
        {"parameter": "null_bootstrap_replicates_per_permutation", "value": int(b["null_signal"]["bootstrap_replicates_per_permutation"])},
    ])
    protocol.to_csv(OUTPUT_DIR / "Bootstrap_Protocol_Parameters.csv", index=False)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-id")
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--null-check", action="store_true")
    args = parser.parse_args()
    cfg = load_config()
    registry = pd.read_csv(LOCKED_DIR / "Matched_Sample_Registry.csv")
    if args.null_check:
        per, summary = null_signal_check(registry, cfg)
        null_cfg = cfg["bootstrap"]["null_signal"]
        median_tol = float(null_cfg["median_zero_tolerance_delta_r2"])
        pass_prob_tol = float(null_cfg["probability_pass_tolerance_from_0p5"])
        caution_prob_tol = float(null_cfg["probability_caution_tolerance_from_0p5"])
        summary["zero_centered_pass"] = (summary["pooled_null_median_delta_r2"].abs() <= median_tol)
        summary["ci_crosses_zero_pass"] = ((summary["pooled_null_ci_low_delta_r2"] <= 0) & (summary["pooled_null_ci_high_delta_r2"] >= 0))
        summary["no_manufactured_positive_evidence_pass"] = (summary["pooled_null_p_delta_r2_gt_0"] < float(cfg["bootstrap"]["directional_probability"]))
        summary["overall_null_signal_sanity_pass"] = summary[["zero_centered_pass", "ci_crosses_zero_pass", "no_manufactured_positive_evidence_pass"]].all(axis=1)

        def null_status(row: pd.Series) -> tuple[str, str]:
            if not bool(row["overall_null_signal_sanity_pass"]):
                return (
                    "REVIEW",
                    "The null check failed at least one predeclared centering, interval, or no-manufactured-evidence rule.",
                )
            distance = float(row["absolute_distance_from_0p5"])
            if distance <= pass_prob_tol:
                return (
                    "PASS",
                    "The null median is near zero, the 95% interval crosses zero, and P(ΔR²>0) is within the predeclared ±0.10 reference band around 0.5.",
                )
            if distance <= caution_prob_tol:
                return (
                    "PASS_WITH_CAUTION",
                    "The null median is near zero and the 95% interval crosses zero, but P(ΔR²>0) lies outside the ±0.10 pass band while remaining within the predeclared ±0.15 caution band.",
                )
            return (
                "REVIEW",
                "The null distribution is centered near zero but P(ΔR²>0) lies outside the predeclared ±0.15 caution band.",
            )

        annotations = summary.apply(null_status, axis=1, result_type="expand")
        summary["null_check_status"] = annotations[0]
        summary["interpretation"] = annotations[1]
        per.to_csv(OUTPUT_DIR / "Null_Signal_Sanity_Per_Permutation.csv", index=False)
        summary.to_csv(OUTPUT_DIR / "Null_Signal_Sanity_Summary.csv", index=False)
        contributions = pd.read_csv(OUTPUT_DIR / "Bootstrap_Country_Contributions.csv")
        calibration = paired_label_swap_calibration(registry, contributions, cfg)
        calibration.to_csv(OUTPUT_DIR / "Paired_Label_Swap_Calibration.csv", index=False)
        print(summary.to_string(index=False))
        print("\nPaired label-swap calibration")
        print(calibration.to_string(index=False)); return
    if args.finalize:
        finalize_outputs(registry, cfg); return
    if not args.sample_id:
        parser.error("Provide --sample-id, --finalize, or --null-check")
    selected = registry[registry["sample_id"].astype(str) == args.sample_id]
    if len(selected) != 1:
        raise KeyError(args.sample_id)
    contributions = pd.read_csv(OUTPUT_DIR / "Bootstrap_Country_Contributions.csv")
    summary, curve, diagnostics = run_sample(selected.iloc[0], contributions, cfg)
    partial = OUTPUT_DIR / "bootstrap_partials"; partial.mkdir(exist_ok=True)
    stem = safe_name(args.sample_id)
    summary.to_csv(partial / f"summary__{stem}.csv", index=False)
    curve.to_csv(partial / f"curve__{stem}.csv", index=False)
    diagnostics.to_csv(partial / f"diagnostics__{stem}.csv", index=False)
    print(f"Completed bootstrap {args.sample_id}: {len(summary)} unit rows")


if __name__ == "__main__":
    main()
