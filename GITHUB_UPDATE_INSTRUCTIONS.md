# GitHub update instructions

This ZIP is prepared to replace the working tree of:

`https://github.com/igeoo/Prediction_of_the_effect_of_regulatory_and_investment_policies_on_mineral_resources_of_countries`

## Recommended update method

1. Download and unzip this package locally.
2. Clone the existing GitHub repository.
3. Preserve the clone's hidden `.git` directory.
4. Remove the old tracked working-tree files, but do not remove `.git`.
5. Copy all files and folders from this package's repository folder into the clone.
6. Run the validation commands below.
7. Commit and push.

Example commands:

```bash
git clone https://github.com/igeoo/Prediction_of_the_effect_of_regulatory_and_investment_policies_on_mineral_resources_of_countries.git
cd Prediction_of_the_effect_of_regulatory_and_investment_policies_on_mineral_resources_of_countries

git rm -r .
# Copy the contents of the unzipped update folder here.

git add .
git commit -m "Cut Before-the-Weights reproducibility release V0.4.3"
git push origin main
```

## Environment and validation

Create a clean environment using the exact versions in `09_environment/requirements-lock.txt`, then run:

```bash
python run_pipeline.py
```

Expected result:

- complete rebuild from the included official raw workbooks;
- fixed panel, folds and matched samples;
- paired country-cluster bootstrap with seed `20260714` and 2,000 replicates per unit;
- null-signal test with seed `20260715`, 20 permutations and 500 replicates;
- 203/203 byte-identical analytical files (202 inherited V0.4.2 files plus one new unit-level base-margin output) and 6/6 reproducible reporting-only outputs.

## Repository settings recommended on GitHub

- Description: `Reproducible pre-weighting signal-admissibility audit for AI–MCDM decision support in resource-rich economies.`
- Topics: `decision-support`, `mcdm`, `reproducibility`, `bootstrap`, `fdi`, `resource-economics`, `machine-learning`
- Release tag: `v0.4.3`
- Release title: `Manuscript-aligned reporting release V0.4.3`

## Important scope statement

The outcome is aggregate national inward FDI. It is not petroleum-sector, mining-sector or project-level investment.

## Permanent DOI archive

After the GitHub tree is updated, create a permanent V0.4.3 archive. The preferred sequence is to reserve a DOI in a Zenodo draft, insert that DOI into `README.md`, `CITATION.cff`, and the manuscript data-availability statement, regenerate the package manifest, upload the final archive, and publish the record. Do not invent or prefill a DOI.

The repository-level technical record to accompany the DOI deposit is `00_protocol/TECHNICAL_AUDIT_TRAIL_V0_4_3.md`.


## Licensing before deposit

GitHub should detect the root `LICENSE` as MIT. The complete mixed-licensing position is recorded in `LICENSING.md`: code is MIT; author-created documentation and generated outputs are CC BY 4.0; third-party source workbooks retain their original terms. For the Zenodo software record, use MIT as the primary software licence and reproduce the mixed-licensing statement in the record description. Insert the reserved DOI into `README.md` and `CITATION.cff` before publishing the archive.
