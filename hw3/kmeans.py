import numpy as np


def kmeans(X, k, n_init=10, max_iter=100, seed=None):
    X = np.asarray(X, dtype=float)
    n, d = X.shape
    if k < 1 or k > n:
        raise ValueError("k must be in [1, n]")

    rng = np.random.default_rng(seed)
    best_inertia = np.inf
    best_labels = None

    for _ in range(n_init):
        # k-means++ style init (simple)
        centers = np.empty((k, d), dtype=float)
        idx = rng.integers(0, n)
        centers[0] = X[idx]
        for i in range(1, k):
            dist_sq = np.min(((X[:, None, :] - centers[None, :i, :]) ** 2).sum(axis=2), axis=1)
            probs = dist_sq / np.sum(dist_sq)
            centers[i] = X[rng.choice(n, p=probs)]

        labels = np.zeros(n, dtype=int)
        for _ in range(max_iter):
            # Assign
            dists = ((X[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
            new_labels = np.argmin(dists, axis=1)
            if np.array_equal(new_labels, labels):
                break
            labels = new_labels

            # Update
            for j in range(k):
                mask = labels == j
                if np.any(mask):
                    centers[j] = X[mask].mean(axis=0)
                else:
                    centers[j] = X[rng.integers(0, n)]

        inertia = np.sum((X - centers[labels]) ** 2)
        if inertia < best_inertia:
            best_inertia = inertia
            best_labels = labels.copy()

    return best_labels


__all__ = ["kmeans"]
