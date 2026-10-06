"""Network topology generators for coupled contagion project."""
from __future__ import annotations

import networkx as nx
import numpy as np


def make_er(n: int = 1000, p: float | None = None, seed: int = 0,
           target_k: float = 6.0) -> nx.Graph:
    """ER with mean degree matched to WS/BA (k~6) by default.

    Pilot artifact fix: fixed p=0.006 gives k~1.8 at N=300 vs k~6 for WS/BA.
    Now p defaults to target_k/(n-1) so density is comparable across N.
    Explicit p still respected.
    """
    if p is None:
        p = target_k / max(1, n - 1)
    return nx.erdos_renyi_graph(n, p, seed=seed)


def make_ws(n: int = 1000, k: int = 6, p: float = 0.1, seed: int = 0) -> nx.Graph:
    """WS small-world graph; clamps k for tiny n (networkx needs k <= n)."""
    if n < 1:
        raise ValueError(f"WS needs n>=1 nodes, got n={n}")
    if k > n:
        # largest valid even k keeps the ring-lattice meaning for n >= 2
        k = n if n % 2 == 0 else n - 1
    return nx.watts_strogatz_graph(n, k, p, seed=seed)


def make_ba(n: int = 1000, m: int = 3, seed: int = 0) -> nx.Graph:
    return nx.barabasi_albert_graph(n, m, seed=seed)


def make_graph(topology: str, n: int = 1000, seed: int = 0, **kwargs) -> nx.Graph:
    topo = topology.lower()
    if topo == "er":
        # pass explicit p if given, else degree-matched default
        return make_er(n=n, p=kwargs.get("p", None), seed=seed)
    if topo == "ws":
        return make_ws(n=n, k=kwargs.get("k", 6), p=kwargs.get("p", 0.1), seed=seed)
    if topo == "ba":
        return make_ba(n=n, m=kwargs.get("m", 3), seed=seed)
    raise ValueError(f"Unknown topology '{topology}'. Use er/ws/ba.")


def to_arrays(G: nx.Graph):
    """Convert graph to dense adjacency + degree arrays.

    Returns (A, degree, nodes) where A is float32 (N,N) adjacency,
    degree is (N,) float, and nodes lists node labels in index order.
    """
    nodes = list(G.nodes())
    index = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)
    A = np.zeros((n, n), dtype=np.float32)
    for u, v in G.edges():
        i, j = index[u], index[v]
        A[i, j] = 1.0
        A[j, i] = 1.0
    degree = A.sum(axis=1)
    return A, degree, nodes
