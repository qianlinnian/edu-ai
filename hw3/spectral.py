import numpy as np

from kmeans import kmeans


def rbf_affinity(X: np.ndarray, sigma: float) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    diff = X[:, None, :] - X[None, :, :]
    dist_sq = np.sum(diff * diff, axis=2)
    W = np.exp(-dist_sq / (2.0 * sigma * sigma))
    np.fill_diagonal(W, 0.0)
    return W


def my_spectral(X: np.ndarray, k: int, sigma: float = 1.0, n_init: int = 10, max_iter: int = 100, seed=None):
    """
    Spectral clustering with fully connected RBF affinity and k-means on normalized eigenvectors.
    Returns:
      labels: cluster labels (0..k-1) for each point
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    if sigma <= 0:
        raise ValueError("sigma must be > 0")

    X = np.asarray(X, dtype=float)
    n = X.shape[0]
    if k > n:
        raise ValueError("k must be <= number of samples")

    W = rbf_affinity(X, sigma=sigma)
    D = np.diag(W.sum(axis=1))

    # Normalized symmetric Laplacian: Lsym = I - D^{-1/2} W D^{-1/2}
    with np.errstate(divide="ignore"):
        d_inv_sqrt = np.diag(1.0 / np.sqrt(np.maximum(np.diag(D), 1e-12)))
    Lsym = np.eye(n) - d_inv_sqrt @ W @ d_inv_sqrt

    # Eigen-decomposition (symmetric)
    eigvals, eigvecs = np.linalg.eigh(Lsym)
    idx = np.argsort(eigvals)[:k]
    U = eigvecs[:, idx]

    # Row normalization
    norms = np.linalg.norm(U, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    U_norm = U / norms

    labels = kmeans(U_norm, k, n_init=n_init, max_iter=max_iter, seed=seed)
    return labels


__all__ = ["my_spectral"]
