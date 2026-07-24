# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: Python [conda env:base] *
#     language: python
#     name: conda-base-py
# ---

# %% [markdown]
# # Investment Signal Audit — M0–M6 Nested Model Ladder
#
# **Research question:** After correcting the commodity base from metals rents
# to oil rents and controlling for market size, do governance and
# regulatory-quality indicators predict investment attractiveness?
#
# **Input:** `INVESTMENT_SIGNAL_AUDIT_OIL_UPGRADED.csv`
# (built by fetch_mineral_data.py → build_upgraded_dataset.py → build_lagged_features.py)
#
# | Model | Feature set |
# |-------|-------------|
# | M0 | Oil rents only |
# | M1 | Market-size / macro baseline |
# | M2 | Core governance only |
# | M3 | Market + oil rents (strong non-governance baseline) |
# | M4 | Market + oil rents + governance  ← **main model** |
# | M5 | M4 + IMF reform indices + FDI restriction |
# | M6 | M5 + lagged features (dynamic robustness) |

# %% [markdown]
# ## 0 · Imports and configuration

# %%
import os
import warnings
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# Optional boosting libraries
try:
    from xgboost import XGBRegressor
    HAS_XGB = True
    print("✓ XGBoost available")
except ImportError:
    HAS_XGB = False
    print("⚠ XGBoost not installed  →  pip install xgboost")

try:
    from lightgbm import LGBMRegressor
    HAS_LGB = True
    print("✓ LightGBM available")
except ImportError:
    HAS_LGB = False
    print("⚠ LightGBM not installed  →  pip install lightgbm")

# ── Config ────────────────────────────────────────────────────────────────────
INPUT_FILE      = 'INVESTMENT_SIGNAL_AUDIT_OIL_UPGRADED.csv'
EITI_FILE       = 'INVESTMENT_SIGNAL_AUDIT_EITI_FOCUSED.csv'
OUTPUT_DIR      = 'audit_outputs'
PRIMARY_TARGET  = 'FDI_asinh'       # arcsinh(FDI_Flows_Millions_USD)
ROBUST_TARGET   = 'FDI_GDP_Pct'     # FDI / GDP × 100
GROUP_COL       = 'ISO3'
YEAR_COL        = 'Year'
TRAIN_CUTOFF    = 2015              # time-split: train ≤ 2015
VAL_CUTOFF      = 2019              #             val 2016–2019, test 2020+

os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"\nOutputs  →  {OUTPUT_DIR}/")


# %% [markdown]
# ## 1 · Load and preprocess

# %%
print(f"Loading {INPUT_FILE} …")
df = pd.read_csv(INPUT_FILE)
print(f"  {df.shape[0]:,} rows × {df.shape[1]} cols  "
      f"| {df[GROUP_COL].nunique()} countries "
      f"| {df[YEAR_COL].min()}–{df[YEAR_COL].max()}")

# Log transforms (idempotent — only creates if missing)
for raw, log in [('GDP_Current_USD',   'GDP_log'),
                 ('GDP_Per_Capita_USD','GDP_Per_Capita_log'),
                 ('Population',         'Population_log')]:
    if raw in df.columns and log not in df.columns:
        df[log] = np.log(df[raw].where(df[raw] > 0))
        print(f"  ✓ {log}")

# FDI targets
if 'FDI_asinh' not in df.columns and 'FDI_Flows_Millions_USD' in df.columns:
    df['FDI_asinh'] = np.arcsinh(df['FDI_Flows_Millions_USD'])
    print("  ✓ FDI_asinh")

# Persistence baseline: t-1 FDI (built in lagged features, but ensure it exists)
if 'FDI_asinh_lag1' not in df.columns and 'FDI_asinh' in df.columns:
    df = df.sort_values([GROUP_COL, YEAR_COL])
    df['FDI_asinh_lag1'] = df.groupby(GROUP_COL)['FDI_asinh'].shift(1)
    print("  ✓ FDI_asinh_lag1 (persistence baseline)")

print(f"\nFinal: {df.shape}")

# %% [markdown]
# ### 1b · Resource-Performance Residual
# Residual from regressing `Mineral_Rents_GDP_Percent` on income level, region
# dummies, and total NR rents. Captures underperformance relative to structurally
# similar countries — closer to the "decision quality" framing in the doc.

# %%
from sklearn.linear_model import LinearRegression

def avail(*cols):
    """Return only columns present in df."""
    return [c for c in cols if c in df.columns]

resid_y = 'Mineral_Rents_GDP_Percent'
resid_x = (avail('GDP_Per_Capita_log', 'Total_NR_Rents_GDP_Percent') +
           [c for c in df.columns if c.startswith('Region_') or
            c.startswith('IncomeGroup_')])

if resid_y in df.columns and resid_x:
    resid_sub = df[resid_x + [resid_y]].dropna()
    if len(resid_sub) >= 50:
        lr = LinearRegression()
        lr.fit(resid_sub[resid_x].values, resid_sub[resid_y].values)
        fitted   = lr.predict(resid_sub[resid_x].values)
        residuals = resid_sub[resid_y].values - fitted
        df.loc[resid_sub.index, 'Resource_Performance_Residual'] = residuals
        r2_resid = 1 - residuals.var() / resid_sub[resid_y].var()
        print(f"✓ Resource_Performance_Residual computed")
        print(f"  Baseline model R²: {r2_resid:.3f}  "
              f"({len(resid_sub):,} obs, {len(resid_x)} predictors)")
        print(f"  Positive residual = country extracts MORE than peers at same income/region")
        print(f"  Negative residual = underperformance relative to structural peers")
    else:
        print(f"⚠ Too few complete cases ({len(resid_sub)}) — "
              f"Resource_Performance_Residual skipped")
else:
    print("⚠ Required columns for residual not available")


# %% [markdown]
# ## 2 · Feature set definitions (M0–M6)

# %%
def avail(*cols):
    """Return only columns present in df."""
    return [c for c in cols if c in df.columns]

MARKET = avail('GDP_log','GDP_Per_Capita_log','Population_log',
               'Trade_GDP_Percent','Inflation_CPI_Annual_Pct',
               'Electricity_Access_Pct','Broadband_Per100','Oil_Price_Global_USD')

GOVERNANCE = avail('Regulatory_Quality','CPI_Score','Political_Stability_Score')

IMF_FDI = avail('IMF_Trade_Reform_Index','Domestic finance','External finance',
                'Labor market','Product market','Avg_FDI_Restriction_Index')

LAGS = avail(
    'Oil_Rents_GDP_Percent_lag1','Oil_Rents_GDP_Percent_lag2',
    'Regulatory_Quality_lag1','CPI_Score_lag1','Political_Stability_Score_lag1',
    'Avg_FDI_Restriction_Index_lag1',
    'Oil_Rents_GDP_Percent_roll3yr','Regulatory_Quality_roll3yr',
    'Trade_GDP_Percent_lag1','Inflation_CPI_Annual_Pct_lag1',
    'Electricity_Access_Pct_lag1','Broadband_Per100_lag1','Oil_Price_Global_USD_lag1'
)

OIL = avail('Oil_Rents_GDP_Percent')

FEATURE_SETS = {
    'M0': OIL,
    'M1': MARKET,
    'M2': GOVERNANCE,
    'M3': MARKET + OIL,
    'M4': MARKET + OIL + GOVERNANCE,
    'M5': MARKET + OIL + GOVERNANCE + IMF_FDI,
    'M6': MARKET + OIL + GOVERNANCE + IMF_FDI + LAGS,
}

DESCRIPTIONS = {
    'M0': 'Oil rents only',
    'M1': 'Market / macro baseline',
    'M2': 'Core governance only',
    'M3': 'Market + oil rents',
    'M4': 'Market + oil rents + governance  ← MAIN MODEL',
    'M5': 'M4 + IMF reform + FDI restriction',
    'M6': 'M5 + lagged features (dynamic robustness)',
}

print("FEATURE SETS:")
for name, cols in FEATURE_SETS.items():
    flag = " ⚠ EMPTY" if not cols else ""
    print(f"  {name}  ({DESCRIPTIONS[name]}): {len(cols)} features{flag}")


# %% [markdown]
# ## 3 · Table 1 — Dataset coverage

# %%
key_vars = [
    'Oil_Rents_GDP_Percent','Gas_Rents_GDP_Percent','Coal_Rents_GDP_Percent',
    'Mineral_Rents_GDP_Percent','Mineral_Rents_Excl_OilGas',
    'Total_NR_Rents_GDP_Percent','Hydrocarbon_Rents_GDP_Percent','Mining_GDP_Proxy',
    'FDI_Flows_Millions_USD','FDI_asinh','FDI_GDP_Pct',
    'Avg_FDI_Restriction_Index','Regulatory_Quality','CPI_Score',
    'GDP_log','GDP_Per_Capita_log','Population_log',
    'Trade_GDP_Percent','Inflation_CPI_Annual_Pct',
    'Exchange_Rate_LCU_USD','Political_Stability_Score','Electricity_Access_Pct',
    'Oil_Price_Global_USD',
    'IMF_Trade_Reform_Index','Domestic finance','External finance',
    'Labor market','Product market',
    'Total_Revenue_USD',
]

rows = []
for v in [v for v in key_vars if v in df.columns]:
    sub = df[df[v].notna()]
    rows.append({
        'Variable':    v,
        'N_obs':       len(sub),
        'N_countries': sub[GROUP_COL].nunique(),
        'Year_min':    sub[YEAR_COL].min() if len(sub) else None,
        'Year_max':    sub[YEAR_COL].max() if len(sub) else None,
        'Pct_missing': round(df[v].isna().mean() * 100, 1),
    })

table1 = pd.DataFrame(rows)
table1.to_csv(f'{OUTPUT_DIR}/Table1_Dataset_Coverage.csv', index=False)
print("TABLE 1 — DATASET COVERAGE")
print(table1.to_string(index=False))


# %% [markdown]
# ## 4 · Table 2 — Target comparison

# %%
targets = [
    ('Mineral_Rents_GDP_Percent',  'Original target (metals rents, excl. oil/gas/coal)'),
    ('Oil_Rents_GDP_Percent',      'Corrected resource base (oil rents) — main signal'),
    ('Total_NR_Rents_GDP_Percent', 'Robustness resource base (total NR rents)'),
    ('FDI_Flows_Millions_USD',     'FDI inflows raw USD millions'),
    ('FDI_asinh',                  'FDI inflows — arcsinh transform  [PRIMARY TARGET]'),
    ('FDI_GDP_Pct',                'FDI / GDP × 100  [ROBUSTNESS TARGET]'),
]

t2_rows = []
for col, desc in targets:
    if col not in df.columns:
        continue
    s = df[col].dropna()
    t2_rows.append({
        'Variable':    col,
        'Description': desc,
        'N_obs':       len(s),
        'Mean':        round(s.mean(),   4),
        'Std':         round(s.std(),    4),
        'Min':         round(s.min(),    4),
        'Median':      round(s.median(), 4),
        'Max':         round(s.max(),    4),
        'Pct_zero':    round((s == 0).mean() * 100, 1),
        'Pct_neg':     round((s  < 0).mean() * 100, 1),
    })

table2 = pd.DataFrame(t2_rows)
table2.to_csv(f'{OUTPUT_DIR}/Table2_Target_Comparison.csv', index=False)
print("TABLE 2 — TARGET COMPARISON")
print(table2[['Variable','Description','N_obs','Mean','Std','Min','Max']].to_string(index=False))


# %% [markdown]
# ## 5 · Model factory

# %%
def build_models():
    models = {
        'Dummy_mean':   DummyRegressor(strategy='mean'),
        'Ridge':        Pipeline([('sc', StandardScaler()),
                                   ('m',  Ridge(alpha=1.0))]),
        'ElasticNet':   Pipeline([('sc', StandardScaler()),
                                   ('m',  ElasticNet(alpha=0.1, l1_ratio=0.5,
                                                     max_iter=5000))]),
        'RandomForest': RandomForestRegressor(n_estimators=200, min_samples_leaf=5,
                                               random_state=42, n_jobs=-1),
        'GradBoost':    GradientBoostingRegressor(n_estimators=200, max_depth=3,
                                                   learning_rate=0.05, random_state=42),
    }
    if HAS_XGB:
        models['XGBoost'] = XGBRegressor(n_estimators=200, max_depth=3,
                                          learning_rate=0.05, random_state=42,
                                          verbosity=0, n_jobs=-1)
    if HAS_LGB:
        models['LightGBM'] = LGBMRegressor(n_estimators=200, max_depth=3,
                                             learning_rate=0.05, random_state=42,
                                             verbose=-1, n_jobs=-1)
    return models


# %% [markdown]
# ## 6 · Country-grouped cross-validation

# %%
def run_cv(df, features, target, group_col=GROUP_COL, n_splits=5):
    """
    5-fold GroupKFold: each fold withholds entire countries.
    Tests generalisation to unseen countries, not just unseen years.
    """
    sub = df[features + [target, group_col]].dropna()
    if len(sub) < 50 or sub[group_col].nunique() < n_splits:
        return None

    X      = sub[features].values
    y      = sub[target].values
    groups = sub[group_col].values
    gkf    = GroupKFold(n_splits=n_splits)
    rows   = []

    for name, mdl in build_models().items():
        r2s, rmses, maes = [], [], []
        for tr, te in gkf.split(X, y, groups):
            try:
                mdl.fit(X[tr], y[tr])
                p = mdl.predict(X[te])
                r2s.append(r2_score(y[te], p))
                rmses.append(np.sqrt(mean_squared_error(y[te], p)))
                maes.append(mean_absolute_error(y[te], p))
            except Exception:
                r2s.append(np.nan); rmses.append(np.nan); maes.append(np.nan)

        rows.append({'Model': name,
                     'N_obs': len(sub), 'N_countries': sub[group_col].nunique(),
                     'R2_mean': np.nanmean(r2s), 'R2_std': np.nanstd(r2s),
                     'R2_min':  np.nanmin(r2s),  'R2_max': np.nanmax(r2s),
                     'RMSE_mean': np.nanmean(rmses), 'RMSE_std': np.nanstd(rmses),
                     'MAE_mean':  np.nanmean(maes),  'MAE_std':  np.nanstd(maes)})
    return pd.DataFrame(rows)


# %% [markdown]
# ## 7 · Run CV — primary target

# %%
print("RUNNING COUNTRY-GROUPED CV  (target: FDI_asinh)  …")
cv_all = []
for fs, feats in FEATURE_SETS.items():
    if not feats:
        print(f"  {fs}: skipped (empty feature set)")
        continue
    print(f"  {fs} ({len(feats)} features) …", end=" ", flush=True)
    res = run_cv(df, feats, PRIMARY_TARGET)
    if res is not None:
        res.insert(0, 'Feature_Set', fs)
        cv_all.append(res)
        best = res['R2_mean'].max()
        print(f"best R²={best:.3f}")
    else:
        print("skipped (insufficient data)")

cv_df = pd.concat(cv_all, ignore_index=True) if cv_all else pd.DataFrame()


# %% [markdown]
# ## 8 · Table 3 — CV results

# %%
if not cv_df.empty:
    out = cv_df.sort_values(['Feature_Set','R2_mean'], ascending=[True, False])
    out.to_csv(f'{OUTPUT_DIR}/Table3_CV_Results.csv', index=False)
    print("TABLE 3 — COUNTRY-GROUPED CV RESULTS")
    disp = ['Feature_Set','Model','N_obs','N_countries',
            'R2_mean','R2_std','RMSE_mean','RMSE_std','MAE_mean']
    print(out[disp].to_string(index=False))


# %% [markdown]
# ## 9 · Robustness CV — FDI/GDP target

# %%
print("\nRUNNING CV ON ROBUSTNESS TARGET  (FDI_GDP_Pct) …")
cv_rob = []
for fs, feats in FEATURE_SETS.items():
    if not feats or ROBUST_TARGET not in df.columns:
        continue
    res = run_cv(df, feats, ROBUST_TARGET)
    if res is not None:
        res.insert(0, 'Feature_Set', fs)
        res.insert(0, 'Target', ROBUST_TARGET)
        cv_rob.append(res)
if cv_rob:
    pd.concat(cv_rob, ignore_index=True).to_csv(
        f'{OUTPUT_DIR}/Table3b_CV_Robustness_Target.csv', index=False)
    print("  ✓ Saved Table3b_CV_Robustness_Target.csv")


# %% [markdown]
# ## 10 · Time-split validation

# %%
def run_time_split(df, features, target, persistence_col=None):
    sub = df[features + [target, YEAR_COL] +
             ([persistence_col] if persistence_col else [])].dropna(
                 subset=features + [target])
    if len(sub) < 30:
        return None

    train = sub[sub[YEAR_COL] <= TRAIN_CUTOFF]
    val   = sub[(sub[YEAR_COL] > TRAIN_CUTOFF) & (sub[YEAR_COL] <= VAL_CUTOFF)]
    test  = sub[sub[YEAR_COL]  > VAL_CUTOFF]

    if len(train) < 20 or len(test) < 5:
        return None

    X_tr, y_tr = train[features].values, train[target].values
    X_va, y_va = val[features].values,   val[target].values
    X_te, y_te = test[features].values,  test[target].values

    def score(X, y):
        if len(y) == 0:
            return np.nan, np.nan, np.nan
        p = mdl.predict(X)
        return (r2_score(y, p),
                np.sqrt(mean_squared_error(y, p)),
                mean_absolute_error(y, p))

    rows = []
    for name, mdl in build_models().items():
        try:
            mdl.fit(X_tr, y_tr)
            tr_r2, _, _        = score(X_tr, y_tr)
            va_r2, _, _        = score(X_va, y_va)
            te_r2, te_rmse, te_mae = score(X_te, y_te)

            row = {'Model': name,
                   'Train_N': len(train), 'Val_N': len(val), 'Test_N': len(test),
                   'Train_R2': round(tr_r2, 4),
                   'Val_R2':   round(va_r2,  4) if not np.isnan(va_r2) else None,
                   'Test_R2':  round(te_r2,  4),
                   'Test_RMSE':round(te_rmse,4),
                   'Test_MAE': round(te_mae, 4)}

            # Persistence baseline
            if persistence_col and persistence_col in test.columns:
                p_sub = test.dropna(subset=[persistence_col, target])
                if len(p_sub) > 0:
                    p_r2   = r2_score(p_sub[target], p_sub[persistence_col])
                    p_rmse = np.sqrt(mean_squared_error(p_sub[target],
                                                        p_sub[persistence_col]))
                    row['Persistence_R2']    = round(p_r2,   4)
                    row['Persistence_RMSE']  = round(p_rmse, 4)
                    row['Beats_Persistence'] = 'Yes' if te_r2 > p_r2 else 'No'

            rows.append(row)
        except Exception as exc:
            print(f"    ⚠ {name}: {exc}")

    return pd.DataFrame(rows)


print("RUNNING TIME-SPLIT VALIDATION …")
print(f"  Train ≤ {TRAIN_CUTOFF}  |  Val {TRAIN_CUTOFF+1}–{VAL_CUTOFF}  |  Test {VAL_CUTOFF+1}+\n")

ts_all = []
for fs, feats in FEATURE_SETS.items():
    if not feats:
        continue
    print(f"  {fs} …", end=" ", flush=True)
    res = run_time_split(df, feats, PRIMARY_TARGET, persistence_col='FDI_asinh_lag1')
    if res is not None:
        res.insert(0, 'Feature_Set', fs)
        ts_all.append(res)
        print(f"test R² range: {res['Test_R2'].min():.3f}–{res['Test_R2'].max():.3f}")
    else:
        print("skipped")

ts_df = pd.concat(ts_all, ignore_index=True) if ts_all else pd.DataFrame()


# %% [markdown]
# ## 11 · Table 4 — Time-split results

# %%
if not ts_df.empty:
    ts_df.to_csv(f'{OUTPUT_DIR}/Table4_Time_Split_Results.csv', index=False)
    print("TABLE 4 — TIME-SPLIT VALIDATION RESULTS")
    disp = ['Feature_Set','Model','Train_N','Test_N',
            'Train_R2','Val_R2','Test_R2','Test_RMSE']
    if 'Beats_Persistence' in ts_df.columns:
        disp.append('Beats_Persistence')
    print(ts_df[disp].to_string(index=False))


# %% [markdown]
# ## 12 · Table 5 — Incremental value

# %%
def incr(cv_df, model, a, b, label):
    if cv_df.empty:
        return None
    ra = cv_df[(cv_df['Feature_Set'] == a) & (cv_df['Model'] == model)]['R2_mean']
    rb = cv_df[(cv_df['Feature_Set'] == b) & (cv_df['Model'] == model)]['R2_mean']
    rma = cv_df[(cv_df['Feature_Set'] == a) & (cv_df['Model'] == model)]['RMSE_mean']
    rmb = cv_df[(cv_df['Feature_Set'] == b) & (cv_df['Model'] == model)]['RMSE_mean']
    if ra.empty or rb.empty:
        return None
    d_r2 = rb.values[0] - ra.values[0]
    return {'Comparison': label, 'Model': model,
            'R2_A': round(ra.values[0], 4), 'R2_B': round(rb.values[0], 4),
            'Delta_R2': round(d_r2, 4),
            'RMSE_A': round(rma.values[0], 4), 'RMSE_B': round(rmb.values[0], 4),
            'Delta_RMSE': round(rmb.values[0] - rma.values[0], 4),
            'Governance_adds_value': 'Yes' if d_r2 > 0.02 else
                                     'Marginal' if d_r2 > 0 else 'No'}

comparisons = [
    ('M1','M4','M1→M4: market+oil rents+governance vs market baseline'),
    ('M3','M4','M3→M4: does governance add value over market+oil rents? ← KEY'),
    ('M4','M5','M4→M5: do IMF reform + FDI restriction add value over core governance?'),
    ('M5','M6','M5→M6: do lagged features add dynamic value?'),
]

if not cv_df.empty:
    t5_rows = []
    for model in cv_df['Model'].unique():
        for a, b, label in comparisons:
            row = incr(cv_df, model, a, b, label)
            if row:
                t5_rows.append(row)
    table5 = pd.DataFrame(t5_rows)
    table5.to_csv(f'{OUTPUT_DIR}/Table5_Incremental_Value.csv', index=False)
    print("TABLE 5 — INCREMENTAL VALUE")
    print(table5[['Comparison','Model','R2_A','R2_B','Delta_R2',
                  'Governance_adds_value']].to_string(index=False))


# %% [markdown]
# ## 13 · Table 6 — Interpretability (M4 and M5)

# %%
def get_interp(df, features, target):
    sub = df[features + [target]].dropna()
    if len(sub) < 30:
        return None, None

    X  = sub[features].values
    y  = sub[target].values
    Xs = StandardScaler().fit_transform(X)

    # Ridge standardised coefficients
    ridge = Ridge(alpha=1.0).fit(Xs, y)
    enet  = ElasticNet(alpha=0.1, l1_ratio=0.5, max_iter=5000).fit(Xs, y)
    coef  = pd.DataFrame({
        'Feature':            features,
        'Ridge_Std_Coef':     ridge.coef_,
        'ElasticNet_Std_Coef':enet.coef_,
        'Ridge_Abs':          np.abs(ridge.coef_),
    }).sort_values('Ridge_Abs', ascending=False).drop(columns='Ridge_Abs')

    # RF permutation importance
    rf   = RandomForestRegressor(n_estimators=200, min_samples_leaf=5,
                                  random_state=42, n_jobs=-1).fit(X, y)
    perm = permutation_importance(rf, X, y, n_repeats=10, random_state=42, n_jobs=-1)
    imp  = pd.DataFrame({
        'Feature': features,
        'RF_Perm_Importance_Mean': perm.importances_mean,
        'RF_Perm_Importance_Std':  perm.importances_std,
    }).sort_values('RF_Perm_Importance_Mean', ascending=False)

    return coef, imp


for fs in ['M4','M5']:
    feats = FEATURE_SETS.get(fs, [])
    if not feats:
        continue
    print(f"\nINTERPRETABILITY — {fs}  ({DESCRIPTIONS[fs]})")
    coef_df, imp_df = get_interp(df, feats, PRIMARY_TARGET)
    if coef_df is not None:
        coef_df.to_csv(f'{OUTPUT_DIR}/Table6_{fs}_Linear_Coef.csv',        index=False)
        imp_df.to_csv( f'{OUTPUT_DIR}/Table6_{fs}_RF_Perm_Importance.csv', index=False)
        print(f"  Ridge coefficients (top 10):")
        print(coef_df[['Feature','Ridge_Std_Coef','ElasticNet_Std_Coef']].head(10).to_string(index=False))
        print(f"\n  RF permutation importance (top 10):")
        print(imp_df[['Feature','RF_Perm_Importance_Mean','RF_Perm_Importance_Std']].head(10).to_string(index=False))


# %% [markdown]
# ## 14 · EITI focused track

# %%
print("\n" + "="*60)
print("EITI FOCUSED TRACK  (M4 on EITI-reporting countries)")
print("="*60)

if os.path.exists(EITI_FILE):
    eiti = pd.read_csv(EITI_FILE)
    for raw, log in [('GDP_Current_USD','GDP_log'),
                     ('GDP_Per_Capita_USD','GDP_Per_Capita_log'),
                     ('Population','Population_log')]:
        if raw in eiti.columns and log not in eiti.columns:
            eiti[log] = np.log(eiti[raw].where(eiti[raw] > 0))
    if 'FDI_asinh' not in eiti.columns and 'FDI_Flows_Millions_USD' in eiti.columns:
        eiti['FDI_asinh'] = np.arcsinh(eiti['FDI_Flows_Millions_USD'])

    m4_feats_eiti = [c for c in FEATURE_SETS.get('M4', []) if c in eiti.columns]
    print(f"  EITI countries: {eiti[GROUP_COL].nunique()}"
          f"  |  rows: {len(eiti):,}")

    if m4_feats_eiti and PRIMARY_TARGET in eiti.columns:
        n_splits = min(3, eiti[GROUP_COL].nunique() // 2)
        res = run_cv(eiti, m4_feats_eiti, PRIMARY_TARGET, n_splits=max(n_splits, 2))
        if res is not None:
            res.insert(0, 'Feature_Set', 'M4')
            res.insert(0, 'Track', 'EITI_focused')
            res.to_csv(f'{OUTPUT_DIR}/Table7_EITI_Track_CV.csv', index=False)
            print("\n  TABLE 7 — EITI FOCUSED TRACK (M4)")
            print(res[['Model','N_obs','N_countries','R2_mean','RMSE_mean']].to_string(index=False))
        else:
            print("  ⚠ Insufficient EITI data for cross-validation")
    else:
        print("  ⚠ Required features or target missing from EITI file")
else:
    print(f"  ⚠ {EITI_FILE} not found — run build_upgraded_dataset.py first")


# %% [markdown]
# ## 15 · Decision rule

# %%
print("\n" + "="*60)
print("DECISION RULE MATRIX")
print("="*60)

REF_MODEL = 'RandomForest'

def get_r2(fs, model=REF_MODEL):
    if cv_df.empty:
        return np.nan
    r = cv_df[(cv_df['Feature_Set'] == fs) & (cv_df['Model'] == model)]['R2_mean']
    return r.values[0] if not r.empty else np.nan

r2 = {fs: get_r2(fs) for fs in FEATURE_SETS}

print(f"\n  Cross-val R² means  (model: {REF_MODEL})")
for fs, val in r2.items():
    if np.isnan(val):
        print(f"  {fs}  {'N/A':>8}  {DESCRIPTIONS[fs]}")
    else:
        bar = '█' * max(0, int(val * 40))
        print(f"  {fs}  {val:+.4f}  {bar}  {DESCRIPTIONS[fs]}")

delta_gov   = r2.get('M4', np.nan) - r2.get('M3', np.nan)
delta_imf   = r2.get('M5', np.nan) - r2.get('M4', np.nan)
delta_lags  = r2.get('M6', np.nan) - r2.get('M5', np.nan)

RULES = [
    ('Governance improves FDI prediction after GDP + oil-rent controls',
     'Strong empirical anchor for governance thesis',
     'Yes' if delta_gov > 0.02 else 'No'),
    ('Governance works only without GDP controls (M2>M4 or M2>M3)',
     'Market-size confounding — weaker result',
     'Yes' if r2.get('M2', np.nan) > r2.get('M4', np.nan) else 'No'),
    ('Oil rents predict FDI but governance does not add value (M3≈M4)',
     'Resource-pull story — not a governance story',
     'Yes' if abs(delta_gov) <= 0.02 and r2.get('M3', 0) > r2.get('M1', 0) else 'No'),
    ('Nothing beats dummy baseline (M4 R²<0)',
     'Clean null — thesis shifts to decision-support framing',
     'Yes' if r2.get('M4', 0) < 0 else 'No'),
    ('Governance predicts FDI/GDP but not arcsinh FDI',
     'Investment-intensity story — narrower but still publishable',
     'Check Table3b'),
]

print("\n  DECISION MATRIX:")
print(f"  {'Pattern':<60} {'Observed':>10}  Interpretation")
print(f"  {'-'*100}")
for pattern, interp, observed in RULES:
    print(f"  {pattern:<60} {observed:>10}  {interp}")

print(f"\n  KEY DELTAS  (RandomForest):")
print(f"  M3 → M4 (governance increment) : {delta_gov:+.4f}")
print(f"  M4 → M5 (IMF + FDI restriction): {delta_imf:+.4f}")
print(f"  M5 → M6 (lag features)         : {delta_lags:+.4f}")

decision_df = pd.DataFrame([(p, i, o) for p, i, o in RULES],
                            columns=['Pattern','Interpretation','Observed'])
decision_df.to_csv(f'{OUTPUT_DIR}/Decision_Rule_Summary.csv', index=False)

# ── Final summary ─────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("✅ SIGNAL AUDIT COMPLETE")
print(f"   All tables saved to  →  {OUTPUT_DIR}/")
print("="*60)
print("\nFILES:")
for f in sorted(os.listdir(OUTPUT_DIR)):
    print(f"  {f}")
