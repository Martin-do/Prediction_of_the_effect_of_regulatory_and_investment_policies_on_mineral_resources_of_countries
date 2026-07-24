from __future__ import annotations

import pandas as pd

from common import LOCKED_DIR, PROCESSED_DIR, load_config, stable_fold


def main() -> None:
    cfg = load_config()
    panel = pd.read_csv(PROCESSED_DIR / "MS2_SIGNAL_ADMISSIBILITY_PANEL_V3.csv", usecols=["ISO3", "Country Name", "Region", "IncomeGroup"])
    countries = panel.drop_duplicates("ISO3").sort_values("ISO3").copy()
    countries["Country_Fold"] = countries["ISO3"].map(
        lambda iso3: stable_fold(str(iso3), int(cfg["country_folds"]), str(cfg["fold_hash_salt"]))
    )
    countries.to_csv(LOCKED_DIR / "Country_Fold_Assignments.csv", index=False)
    counts = countries.groupby("Country_Fold").size().rename("countries").reset_index()
    counts.to_csv(LOCKED_DIR / "Country_Fold_Counts.csv", index=False)
    print(counts.to_string(index=False))


if __name__ == "__main__":
    main()
