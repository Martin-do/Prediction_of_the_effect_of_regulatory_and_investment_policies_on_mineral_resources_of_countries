# Manuscript Edits for V0.4.3 Alignment — Revised Complete Checklist

This checklist aligns `MS2_Full_Manuscript_DSS_v8.docx` with the current V0.4.3 manuscript-facing outputs in the repository.

It supersedes the earlier `manuscript_edits.md`.

---

## 1. Abstract

### Oil-rents setup summary

**Find:**

`Oil rents produced two material, three marginal and five setup-dependent setup verdicts;`

**Replace with:**

`Oil rents produced one material, four marginal and five setup-dependent setup verdicts;`

**Reason:** The final V0.4.3 cross-setup synthesis for oil rents is 1 material, 4 marginal and 5 setup-dependent setups.

---

## 2. Table 1 — Panel B

### Regulatory Quality scale

**Find:**

`WGI governance estimate; 0–100 score not used`

**Replace with:**

`WGI governance estimate; alternative 0-100 score checked post hoc`

**Reason:** V0.4.3 includes an isolated post hoc two-scale implementation check. The estimate remains the frozen primary scale, while the alternative 0–100 score was checked without changing any unit, setup or overall verdict.

---

## 3. Table 3 — Benchmark Competitiveness and Matched Incremental Evidence

Make all of the following corrections.

### 3.1 Oil rents, >=1%, primary outcome

**Find — Unit verdicts P/N:**

`11/4/3/0/0 / 11/4/3/0/0`

**Replace with:**

`10/5/3/0/0 / 11/4/3/0/0`

**Find — Setup verdict P/N:**

`Material / Material`

**Replace with:**

`Marginal / Material`

**Reason:** The primary >=1% oil-rents setup now has 10 material, 5 marginal and 3 setup-dependent units. Since 10/18 = 55.6%, it no longer meets the 60% material-unit rule, but 15/18 are material-or-marginal with no unsupported units, so the setup is Marginal. The normalized setup remains Material.

### 3.2 Oil rents, >=5%, normalized model-minus-benchmark median

**Find:** `0.15840 / 0.18636`

**Replace with:** `0.15840 / 0.18630`

### 3.3 Regulatory Quality, All, normalized model-minus-benchmark median

**Find:** `0.25826 / 0.22293`

**Replace with:** `0.25826 / 0.22433`

### 3.4 Regulatory Quality, All, normalized unit verdicts

**Find:** `0/14/2/2/0 / 4/10/1/3/0`

**Replace with:** `0/14/2/2/0 / 4/10/2/2/0`

### 3.5 Regulatory Quality, >=1%, normalized signal increment

**Find:** `0.00005 / 0.00063`

**Replace with:** `0.00005 / 0.00081`

### 3.6 Regulatory Quality, >=5%, normalized model-minus-benchmark median

**Find:** `0.14118 / 0.18177`

**Replace with:** `0.14118 / 0.18196`

---

## 4. Section 4.3 — Matched Incremental Value of Oil Rents and Regulatory Quality

### Paragraph beginning “Oil rents produced the more favourable...”

**Find:**

`...and 11 of 18 units in each setup were classified as material. These were the only two setups classified as supported and practically material.`

**Replace with:**

`...and 10 and 11 of 18 units were classified as material respectively. Only the normalized setup was classified as supported and practically material; the primary setup was classified as directionally positive but marginal.`

### Cross-setup count sentence

**Find:**

`Across all ten decision-bearing setups, oil rents therefore produced two material, three marginal and five setup-dependent verdicts.`

**Replace with:**

`Across all ten decision-bearing setups, oil rents therefore produced one material, four marginal and five setup-dependent verdicts.`

### Base-model benchmark comparison paragraph

**Find:**

`The median base-model margins were 0.1759 and 0.1793 respectively, whereas the median matched increments from adding the signal under test were 0.00506 and 0.00067.`

**Replace with:**

`The median base-model margins were 0.1759 and 0.1790 respectively, whereas the median matched increments from adding the signal under test were 0.00506 and 0.00075.`

---

## 5. Section 4.4 — Uncertainty Diagnostics and Sensitivity of the Verdicts

The current paragraph referring to **two material oil-rents setups** is no longer valid and should be replaced as a whole.

### Find paragraph beginning:

`The two material oil-rents setups both occurred in the 1% country universe...`

### Replace the full paragraph with:

`The single material oil-rents setup occurred in the 1% country universe under the normalized outcome specification. Its lower uncertainty bound was close to zero, and the interval was conditional on frozen predictions rather than repeated model refitting. The result is therefore supportive but should not control the cross-setup conclusion. The corresponding primary-outcome setup in the same 1% universe was directionally positive but marginal rather than material.`

**Reason:** Only the normalized >=1% oil-rents setup remains Material. The previous interpretation based on two correlated material setups is no longer applicable.

---

## 6. Figure 2 — Panel (a)

Figure 2a must be regenerated/replaced because the manuscript image still displays the old two-material-setup pattern.

### Required oil-rents setup pattern

For **Annual FDI net flow**:

- All → `G` / Marginal
- >=1% → `G` / Marginal
- >=5% → `S` / Setup-dependent
- >=10% → `S` / Setup-dependent
- >=15% → `S` / Setup-dependent

For **FDI net flow / GDP**:

- All → `G` / Marginal
- >=1% → `M` / Material
- >=5% → `G` / Marginal
- >=10% → `S` / Setup-dependent
- >=15% → `S` / Setup-dependent

Regulatory Quality remains `S` / Setup-dependent in all ten cells.

### Figure 2b

No manuscript edit is required solely because of the 1/4/5 setup-count correction, provided the archived threshold curve and the displayed `44/180 (24.4%)` and `14/180 (7.8%)` values remain generated from the current V0.4.3 unit-level probabilities.

---

## 7. Section 4.5 — Final Signal-Admissibility Roles

**Find:**

`Oil rents was the more favourable signal at the setup level, with two material and three marginal setups...`

**Replace with:**

`Oil rents was the more favourable signal at the setup level, with one material and four marginal setups...`

---

## 8. Table 4 — Final Cross-Setup Signal-Admissibility Synthesis

### Oil-rents row

**Find:**

`Oil rents (t−1) | 10 | 2 | 3 | 5 | 0 | 0 | Setup-dependent`

**Replace with:**

`Oil rents (t−1) | 10 | 1 | 4 | 5 | 0 | 0 | Setup-dependent`

The locked decision role remains `Candidate pre-weighting signal`.

### Table 4 note

**Find:**

`The two oil-rent material setups are supportive rather than standalone confirmatory because they arise from correlated analytical environments — the same 1% country universe under two closely related outcome specifications — have lower uncertainty bounds close to zero and use fixed-prediction bootstrap intervals that exclude model-refitting variability.`

**Replace with:**

`The single oil-rent material setup occurred in the 1% country universe under the normalized outcome specification. Its lower uncertainty bound was close to zero, and the fixed-prediction bootstrap interval excludes model-refitting variability; it is therefore supportive rather than standalone confirmatory evidence.`

---

## 9. Section 5.1 — Predictive Usefulness Is Not Signal Admissibility

The corrected base-model headline values occur a second time in the Discussion and must also be updated.

**Find:**

`The median base-model margins were 0.1759 and 0.1793 respectively, whereas the median matched increments from adding the signal under test were 0.00506 and 0.00067.`

**Replace with:**

`The median base-model margins were 0.1759 and 0.1790 respectively, whereas the median matched increments from adding the signal under test were 0.00506 and 0.00075.`

---

## 10. Section 5.3 — Interpreting the Two Candidate Signals

### Find:

`Oil rents produced the more favourable evidence profile, but that profile remained conditional. Its two material setups occurred at the 1% resource-intensity threshold, with three further marginal setups, and evidence weakened as the threshold became more restrictive while matched sample sizes also declined.`

### Replace with:

`Oil rents produced the more favourable evidence profile, but that profile remained conditional. Its single material setup occurred at the 1% resource-intensity threshold under the normalized outcome specification, with four further marginal setups, and evidence weakened as the threshold became more restrictive while matched sample sizes also declined.`

### Find:

`The two material setups are not independent confirmation, because they use closely related outcome definitions within the same 1% country universe, and their role is supportive rather than decisive.`

### Replace with:

`The single material setup should be interpreted as supportive rather than decisive because its lower uncertainty bound was close to zero and the bootstrap interval was conditional on frozen predictions rather than repeated model refitting.`

---

## 11. Conclusion

**Find:**

`Oil rents produced two material, three marginal and five setup-dependent verdicts, while Regulatory Quality was setup-dependent in all ten setups.`

**Replace with:**

`Oil rents produced one material, four marginal and five setup-dependent verdicts, while Regulatory Quality was setup-dependent in all ten setups.`

The remainder of the conclusion — including the overall setup-dependent classification and candidate pre-weighting role for both signals — remains valid.

---

## 12. Items Already Consistent and Not Requiring Manuscript Changes

The following remain aligned with the current analytical interpretation unless a later repository regeneration changes them:

- 217 economies and the 1990–2024 panel period.
- 7,595 country-year rows.
- 6,635 observed annual FDI-flow rows.
- 504 preserved negative-flow years.
- 6,538 observed normalized FDI-flow rows.
- 6,054 oil-rents observations.
- 5,143 Regulatory Quality observations.
- Restoration of 31 previously omitted oil-rent-intensive economies.
- 30 restored economies entering at least one complete M3 observation.
- Nigeria contributing 35 annual FDI-flow observations.
- Three algorithms: Ridge, Elastic Net and Random Forest.
- Five country-grouped folds and five future-period cutoffs.
- 18 algorithm-validation units per setup.
- 10 decision-bearing setups per signal.
- 2,000-replicate paired country-cluster bootstrap.
- Overall classification of both oil rents and Regulatory Quality as `Setup-dependent`.
- Locked decision role of both signals as `Candidate pre-weighting signal`.
- The persistence headline comparison in Table 2.
- The post hoc Regulatory Quality two-scale result: no unit or setup verdict changes and no change to the overall classification.

---

## 13. Repository-Side Consistency Fixes / Re-verification Targets

These are not Word-manuscript edits. They were identified during the alignment audit and must be correct before V0.4.3 is treated as fully internally synchronized. Items corrected on `main` are retained here as explicit re-verification targets.

### `04_pipeline/07_integrate_bootstrap_verdicts.py`

**Stale form:** `the two ge1pct material cells`

**Required/current interpretation:** only the normalized >=1% oil-rents setup is material; the primary >=1% setup is marginal. The generator should describe a **single ge1pct material setup** and should not refer to two correlated material cells.

Because this generator writes annotation fields into multiple outputs, rerunning this stage should refresh at least:

- `07_outputs/Central_Verdict_Sensitivity_Table.csv`
- `07_outputs/Oil_Rent_Threshold_Sensitivity_Table.csv`
- `07_outputs/Material_Setup_Caveats.csv`

`Material_Setup_Caveats.csv` has been synchronized directly; the two larger sensitivity tables should be checked after pipeline regeneration to confirm the stale generated annotation has disappeared there too.

### `RELEASE_NOTES_V0_4_3.md`

**Stale Regulatory Quality headline values:**

- median base margin `0.1793236`
- median signal increment `0.0006654`

**Required/current values:**

- median base margin `0.1790498`
- median signal increment `0.0007481`

### `00_protocol/TECHNICAL_AUDIT_TRAIL_V0_4_3.md`

**Stale values:**

- `0.1793236413`
- `0.0006654433`

**Required/current values:**

- `0.1790498327`
- `0.0007481264`

### `00_protocol/BOOTSTRAP_METHOD_AND_GUARDRAILS.md`

**Stale form:** `The two ge1pct setups that meet the materiality rule...`

**Required/current interpretation:** one >=1% oil-rents setup meets the materiality rule — the normalized outcome specification. The corresponding primary-outcome >=1% setup is marginal. The remaining caveat is that the material result has a lower uncertainty bound close to zero and comes from a fixed-prediction bootstrap that excludes model-refitting variability.

### `08_validation/Reproducibility_Report.md`

**Stale form:** `Two oil-rent setups in the pre-2016 >=1% universe meet the prespecified materiality rule.`

**Required/current interpretation:** one setup meets the materiality rule — the normalized >=1% oil-rents setup — while the primary >=1% setup is marginal.

---

## Final Alignment Check

After applying the manuscript edits and regenerating the reporting layer where required:

- Search the manuscript for `two material` and confirm no remaining passage describes two material oil-rents setups.
- Search the manuscript for `0.1793` and confirm no stale base-margin headline remains.
- Search the manuscript for `0.00067` and confirm no stale Regulatory Quality headline increment remains.
- Confirm Table 3 matches `07_outputs/Manuscript_Table3_Setup_Evidence_Compact.csv`.
- Confirm Table 4 matches `07_outputs/Manuscript_Table4_Final_Synthesis.csv`.
- Confirm Figure 2a shows the corrected oil-rents pattern with only the normalized >=1% cell marked Material.
- Confirm the Abstract, Results, Discussion and Conclusion all report **1 material, 4 marginal, 5 setup-dependent** for oil rents.
- Search live repository documentation for stale claims that **two** >=1% oil-rents setups are material.
- Search live repository documentation for stale Regulatory Quality headline values `0.1793236`, `0.1793236413`, `0.0006654`, or `0.0006654433`.
- After rerunning `07_integrate_bootstrap_verdicts.py`, confirm `Central_Verdict_Sensitivity_Table.csv`, `Oil_Rent_Threshold_Sensitivity_Table.csv`, and `Material_Setup_Caveats.csv` all use the single-material-setup interpretation.

Once those checks pass, the manuscript narrative, documentation and generated reporting annotations are aligned with the current V0.4.3 outputs.
