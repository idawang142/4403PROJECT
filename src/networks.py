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
        p = min(1.0, target_k / max(1, n - 1))
    return nx.erdos_renyi_graph(n, p, seed=seed)


def make_ws(n: int = 1000, k: int = 6, p: float = 0.1, seed: int = 0) -> nx.Graph:
    k = min(k, n - 1)
    k -= k % 2
    return nx.watts_strogatz_graph(n, k, p, seed=seed)


def make_ba(n: int = 1000, m: int = 3, seed: int = 0) -> nx.Graph:
    if n == 1:
        return nx.empty_graph(1)
    return nx.barabasi_albert_graph(n, min(m, n - 1), seed=seed)


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
    """Convert graph to sparse CSR adjacency and a one-dimensional degree array.

    Returns (A, degree, nodes); A is float32 CSR and degree is (N,) float.
    Nodes are ordered by G.nodes() order; caller must keep the mapping.
    """
    nodes = list(G.nodes())
    A = nx.to_scipy_sparse_array(G, nodelist=nodes, dtype=np.float32, format="csr")
    degree = np.asarray(A.sum(axis=1)).ravel()
    return A, degree, nodes
