import argparse
import json
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from hierarchical import my_hierarchical
from kmeans import kmeans
from spectral import my_spectral

try:
    from sklearn.metrics import silhouette_score, adjusted_rand_score
except Exception as e:
    raise RuntimeError("scikit-learn is required for metrics (silhouette, ARI).") from e

try:
    from sklearn.decomposition import PCA
except Exception:
    PCA = None

try:
    from scipy.cluster.hierarchy import dendrogram
except Exception:
    dendrogram = None


DATASETS = {
    # Update paths/format to match the datasets you place in ./datasets
    "iris": {"path": "datasets/iris.csv", "label_col": -1, "delimiter": ",", "header": "infer"},
    "wine": {"path": "datasets/wine.csv", "label_col": -1, "delimiter": ",", "header": "infer"},
    "optdigits": {"path": "datasets/optdigits.csv", "label_col": -1, "delimiter": ",", "header": "infer"},
}


def standardize(X):
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std[std == 0] = 1.0
    return (X - mean) / std


def load_dataset(path, label_col=None, delimiter=",", header="infer"):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    header_arg = 0 if header == "infer" else None
    df = pd.read_csv(path, delimiter=delimiter, header=header_arg)
    if label_col is None:
        X = df.values
        y = None
    else:
        y = df.iloc[:, label_col].to_numpy()
        X = df.drop(df.columns[label_col], axis=1).to_numpy()
    return X, y


def eval_metrics(X, labels, y_true=None):
    sil = silhouette_score(X, labels) if X.shape[0] > 1 else np.nan
    ari = adjusted_rand_score(y_true, labels) if y_true is not None else np.nan
    return sil, ari


def run_hierarchical(X, y, k, linkage):
    t0 = time.perf_counter()
    labels, linkage_matrix = my_hierarchical(X, k=k, linkage=linkage)
    t1 = time.perf_counter()
    sil, ari = eval_metrics(X, labels, y)
    return labels, linkage_matrix, sil, ari, t1 - t0


def run_spectral(X, y, k, sigmas, runs, seed):
    results = []
    for sigma in sigmas:
        sils = []
        aris = []
        times = []
        for r in range(runs):
            t0 = time.perf_counter()
            labels = my_spectral(X, k=k, sigma=sigma, n_init=5, seed=None if seed is None else seed + r)
            t1 = time.perf_counter()
            sil, ari = eval_metrics(X, labels, y)
            sils.append(sil)
            aris.append(ari)
            times.append(t1 - t0)
        results.append(
            {
                "sigma": sigma,
                "sil_mean": float(np.mean(sils)),
                "sil_std": float(np.std(sils)),
                "ari_mean": float(np.mean(aris)),
                "ari_std": float(np.std(aris)),
                "time_mean": float(np.mean(times)),
                "time_std": float(np.std(times)),
            }
        )
    return results


def run_kmeans(X, y, k, seed):
    t0 = time.perf_counter()
    labels = kmeans(X, k, n_init=10, max_iter=100, seed=seed)
    t1 = time.perf_counter()
    sil, ari = eval_metrics(X, labels, y)
    return labels, sil, ari, t1 - t0


def plot_dendrogram(linkage_matrix, out_path):
    if dendrogram is None:
        print("scipy not available; skipping dendrogram plot.")
        return
    plt.figure(figsize=(10, 6))
    dendrogram(linkage_matrix)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def to_2d(X):
    if X.shape[1] == 2:
        return X
    if PCA is not None:
        return PCA(n_components=2).fit_transform(X)
    # Simple SVD-based PCA fallback
    Xc = X - X.mean(axis=0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    return U[:, :2] * S[:2]


def plot_scatter(X, labels, title, out_path):
    X2 = to_2d(X)
    plt.figure(figsize=(6, 5))
    plt.scatter(X2[:, 0], X2[:, 1], c=labels, s=10, cmap="tab10")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def scalability_experiment(X, k, algorithm, sigmas, sizes, dims, seed, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if algorithm == "spectral":
        best_sigma = sigmas[0]
        algo = lambda data: my_spectral(data, k=k, sigma=best_sigma, n_init=3, seed=seed)
    elif algorithm == "hierarchical":
        algo = lambda data: my_hierarchical(data, k=k, linkage="complete")[0]
    else:
        algo = lambda data: kmeans(data, k, n_init=5, seed=seed)

    # Vary sample size
    size_times = []
    rng = np.random.default_rng(seed)
    for n in sizes:
        idx = rng.choice(X.shape[0], size=min(n, X.shape[0]), replace=False)
        Xn = X[idx]
        t0 = time.perf_counter()
        _ = algo(Xn)
        t1 = time.perf_counter()
        size_times.append({"n": int(Xn.shape[0]), "time": t1 - t0})

    # Vary dimensions
    dim_times = []
    max_dim = X.shape[1]
    for d in dims:
        d = min(d, max_dim)
        Xd = X[:, :d]
        t0 = time.perf_counter()
        _ = algo(Xd)
        t1 = time.perf_counter()
        dim_times.append({"d": int(d), "time": t1 - t0})

    # Save plots
    plt.figure(figsize=(6, 4))
    plt.plot([x["n"] for x in size_times], [x["time"] for x in size_times], marker="o")
    plt.xlabel("Samples")
    plt.ylabel("Runtime (s)")
    plt.title(f"Scalability vs Samples ({algorithm})")
    plt.tight_layout()
    plt.savefig(out_dir / "scalability_samples.png", dpi=150)
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.plot([x["d"] for x in dim_times], [x["time"] for x in dim_times], marker="o")
    plt.xlabel("Dimensions")
    plt.ylabel("Runtime (s)")
    plt.title(f"Scalability vs Dimensions ({algorithm})")
    plt.tight_layout()
    plt.savefig(out_dir / "scalability_dims.png", dpi=150)
    plt.close()

    return size_times, dim_times


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="*", default=list(DATASETS.keys()))
    parser.add_argument("--sigmas", nargs="*", type=float, default=[0.1, 0.5, 1, 2, 5])
    parser.add_argument("--spectral-runs", type=int, default=5)
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--dendrogram-dataset", default="iris")
    parser.add_argument("--scatter-dataset", default=None)
    parser.add_argument("--scalability-dataset", default=None)
    parser.add_argument("--scalability-algorithm", default="spectral", choices=["spectral", "hierarchical", "kmeans"])
    parser.add_argument("--scalability-sizes", nargs="*", type=int, default=[100, 500, 1000, 2000])
    parser.add_argument("--scalability-dims", nargs="*", type=int, default=[2, 4, 8, 16, 32])
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    all_results = {}

    for name in args.datasets:
        if name not in DATASETS:
            raise ValueError(f"Unknown dataset: {name}")
        cfg = DATASETS[name]
        X, y = load_dataset(cfg["path"], cfg["label_col"], cfg["delimiter"], cfg["header"])
        X = standardize(X)
        k = len(np.unique(y)) if y is not None else 3

        # Hierarchical
        labels_s, link_s, sil_s, ari_s, time_s = run_hierarchical(X, y, k, linkage="single")
        labels_c, link_c, sil_c, ari_c, time_c = run_hierarchical(X, y, k, linkage="complete")

        # Spectral
        spectral_results = run_spectral(X, y, k, args.sigmas, args.spectral_runs, args.seed)
        if y is not None:
            best = max(spectral_results, key=lambda r: r["ari_mean"])
        else:
            best = max(spectral_results, key=lambda r: r["sil_mean"])

        # K-means baseline
        labels_km, sil_km, ari_km, time_km = run_kmeans(X, y, k, seed=args.seed)

        all_results[name] = {
            "hierarchical_single": {"sil": sil_s, "ari": ari_s, "time": time_s},
            "hierarchical_complete": {"sil": sil_c, "ari": ari_c, "time": time_c},
            "spectral": spectral_results,
            "spectral_best": best,
            "kmeans": {"sil": sil_km, "ari": ari_km, "time": time_km},
        }

        # Dendrogram
        if name == args.dendrogram_dataset:
            plot_dendrogram(link_c, results_dir / f"{name}_dendrogram.png")

        # Scatter plots (optional)
        if args.scatter_dataset is not None and name == args.scatter_dataset:
            plot_scatter(X, labels_km, f"{name} - KMeans", results_dir / f"{name}_kmeans.png")
            plot_scatter(X, labels_s, f"{name} - HAC Single", results_dir / f"{name}_hac_single.png")
            plot_scatter(X, labels_c, f"{name} - HAC Complete", results_dir / f"{name}_hac_complete.png")
            # Use best spectral sigma
            labels_sp = my_spectral(X, k=k, sigma=best["sigma"], n_init=5, seed=args.seed)
            plot_scatter(X, labels_sp, f"{name} - Spectral", results_dir / f"{name}_spectral.png")

    # Scalability
    if args.scalability_dataset is None:
        args.scalability_dataset = args.datasets[0]
    cfg = DATASETS[args.scalability_dataset]
    X, y = load_dataset(cfg["path"], cfg["label_col"], cfg["delimiter"], cfg["header"])
    X = standardize(X)
    k = len(np.unique(y)) if y is not None else 3
    size_times, dim_times = scalability_experiment(
        X,
        k=k,
        algorithm=args.scalability_algorithm,
        sigmas=args.sigmas,
        sizes=args.scalability_sizes,
        dims=args.scalability_dims,
        seed=args.seed,
        out_dir=results_dir,
    )

    all_results["scalability"] = {
        "dataset": args.scalability_dataset,
        "algorithm": args.scalability_algorithm,
        "sizes": size_times,
        "dims": dim_times,
    }

    with open(results_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print(f"Saved results to {results_dir}")


if __name__ == "__main__":
    main()
