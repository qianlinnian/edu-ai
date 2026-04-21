# Homework 03 - Data Analysis and Mining

This folder contains implementations for:

1. `hierarchical.py`: Hierarchical Agglomerative Clustering (single/complete linkage)
2. `spectral.py`: Spectral Clustering (RBF affinity + normalized Laplacian)
3. `experiments.py`: Runs experiments, metrics, and plots

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

## Datasets

Place datasets under `datasets/` and update `DATASETS` in `experiments.py` to match:

- `path`: file path
- `label_col`: index of label column (use `-1` if labels are in the last column)
- `delimiter`: `,` or other separators
- `header`: `infer` if a header row exists, otherwise `none`

Example:

```
datasets/
  iris.csv
  wine.csv
  optdigits.csv
```

## Run Experiments

```bash
python experiments.py --datasets iris wine optdigits --spectral-runs 5
```

Outputs:

- `results/results.json`
- Dendrogram for the configured dataset (default: iris)
- Scatter plots if `--scatter-dataset` is set
- Scalability plots: `scalability_samples.png`, `scalability_dims.png`

## Notes

- No high-level clustering libraries are used for HAC or Spectral clustering.
- Metrics use `scikit-learn` (allowed for evaluation).
