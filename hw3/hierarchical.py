import numpy as np


def pairwise_distances(X: np.ndarray) -> np.ndarray:
    diff = X[:, None, :] - X[None, :, :]
    dist = np.sqrt(np.sum(diff * diff, axis=2))
    return dist


def _assign_labels(active_clusters, clusters, n_points):
    labels = np.empty(n_points, dtype=int)
    for label, cid in enumerate(active_clusters):
        for idx in clusters[cid]:
            labels[idx] = label
    return labels


def my_hierarchical(X: np.ndarray, k: int, linkage: str = "single"):
    """
    Hierarchical Agglomerative Clustering.
    Returns:
      labels: cluster labels (0..k-1) for each point
      linkage_matrix: (n-1, 4) array for dendrogram plotting
    """
    if linkage not in {"single", "complete"}:
        raise ValueError("linkage must be 'single' or 'complete'")
    if k < 1:
        raise ValueError("k must be >= 1")

    X = np.asarray(X, dtype=float)
    n = X.shape[0]
    if k > n:
        raise ValueError("k must be <= number of samples")

    dist = pairwise_distances(X)
    np.fill_diagonal(dist, np.inf)

    max_clusters = 2 * n - 1
    cluster_dist = np.full((max_clusters, max_clusters), np.inf, dtype=float)
    cluster_dist[:n, :n] = dist

    clusters = {i: [i] for i in range(n)}
    cluster_sizes = {i: 1 for i in range(n)}
    active = list(range(n))

    linkage_matrix = np.zeros((n - 1, 4), dtype=float)
    next_id = n
    labels_at_k = None

    step = 0
    while len(active) > 1:
        # Find closest pair among active clusters
        min_d = np.inf
        pair = None
        for i in range(len(active)):
            ci = active[i]
            for j in range(i + 1, len(active)):
                cj = active[j]
                d = cluster_dist[ci, cj]
                if d < min_d:
                    min_d = d
                    pair = (ci, cj)

        if pair is None:
            break

        a, b = pair
        # Record linkage
        size = cluster_sizes[a] + cluster_sizes[b]
        linkage_matrix[step] = [a, b, min_d, size]
        step += 1

        # Merge clusters
        clusters[next_id] = clusters[a] + clusters[b]
        cluster_sizes[next_id] = size

        # Update distances to new cluster
        for c in active:
            if c in (a, b):
                continue
            if linkage == "single":
                new_d = min(cluster_dist[a, c], cluster_dist[b, c])
            else:
                new_d = max(cluster_dist[a, c], cluster_dist[b, c])
            cluster_dist[next_id, c] = new_d
            cluster_dist[c, next_id] = new_d

        # Update active list
        active = [c for c in active if c not in (a, b)]
        active.append(next_id)
        next_id += 1

        if labels_at_k is None and len(active) == k:
            labels_at_k = _assign_labels(active, clusters, n)

    if labels_at_k is None:
        # k == 1 or not captured
        labels_at_k = np.zeros(n, dtype=int)

    return labels_at_k, linkage_matrix


__all__ = ["my_hierarchical"]
