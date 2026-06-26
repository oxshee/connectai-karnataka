"""
ConnectAI Karnataka — Connectivity Engine (GNN + Graph Analysis)

Implements:
  1. Graph construction from habitat patches
  2. Least-Cost Path analysis (Dijkstra on resistance surface)
  3. Graph Neural Network node embedding (PyTorch — prototype architecture)
  4. Corridor ranking and bottleneck detection
  5. Connectivity metrics

Architecture:
  - Habitat patches → graph NODES (features: suitability, area, NDVI, …)
  - Movement probability between patches → graph EDGES (weight = resistance)
  - GNN encodes each node using neighbourhood aggregation
  - Dijkstra finds the minimum-resistance wildlife movement paths
  - Betweenness centrality identifies bottleneck patches

Reference:
  Cushman et al. (2009) "Gene flow in complex landscapes."
  Mcrae & Beier (2007) "Circuit theory predicts gene flow in plant and animal populations."
"""
from __future__ import annotations
import math
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import networkx as nx

logger = logging.getLogger(__name__)


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class HabitatNode:
    id: int
    lat: float
    lon: float
    suitability: float        # 0–1
    area_ha: float
    ndvi: float
    forest_density: float
    dist_to_road_m: float
    name: str = ""

    @property
    def feature_vector(self) -> list[float]:
        return [
            self.suitability,
            min(self.area_ha / 1000, 1.0),   # normalised area
            max(self.ndvi, 0),
            self.forest_density,
            min(self.dist_to_road_m / 5000, 1.0),
        ]


@dataclass
class CorridorPath:
    nodes: list[int]           # patch IDs in order
    total_resistance: float
    bottleneck_resistance: float
    bottleneck_node_id: int
    length_approx_km: float
    permeability: float        # 0–1  (inverse of normalised resistance)


@dataclass
class ConnectivityResult:
    corridor_id: int
    graph_nodes: int
    graph_edges: int
    least_cost_paths: list[CorridorPath]
    bottleneck_zones: list[dict[str, Any]]
    connectivity_score: float   # 0–100
    node_centrality: dict[int, float]
    computation_time_s: float
    explanation: str


# ── Geometry helpers ─────────────────────────────────────────────────────────

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two WGS84 points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def movement_probability(
    node_a: HabitatNode,
    node_b: HabitatNode,
    max_dispersal_km: float = 25.0,
) -> float:
    """
    Probability that an animal moves between two patches.
    Falls off with distance and is modulated by suitability of both patches.
    """
    dist = haversine_km(node_a.lat, node_a.lon, node_b.lat, node_b.lon)
    if dist > max_dispersal_km:
        return 0.0
    # Exponential distance decay (alpha = mean dispersal distance)
    alpha = max_dispersal_km / 3.0
    p_dist = math.exp(-dist / alpha)
    # Geometric mean suitability of both patches
    p_suit = math.sqrt(node_a.suitability * node_b.suitability)
    return round(p_dist * p_suit, 6)


def resistance(prob: float) -> float:
    """Movement probability → resistance cost (for shortest-path)."""
    if prob <= 0:
        return 1e9
    return round(1.0 / prob, 4)


# ── Graph construction ───────────────────────────────────────────────────────

def build_habitat_graph(
    patches: list[dict],
    species: str = "all",
    max_dispersal_km: float = 25.0,
) -> tuple[nx.Graph, dict[int, HabitatNode]]:
    """
    Build a weighted undirected graph where:
      nodes = habitat patches
      edges = movement probability > 0 between patches

    Returns the graph and a node_id → HabitatNode mapping.
    """
    # Dispersal distance varies by species
    dispersal = {
        "elephant": 40.0, "tiger": 50.0, "leopard": 30.0, "all": 25.0,
    }.get(species, max_dispersal_km)

    nodes: dict[int, HabitatNode] = {}
    for p in patches:
        nodes[p["id"]] = HabitatNode(
            id=p["id"],
            lat=p["centroid_lat"],
            lon=p["centroid_lon"],
            suitability=p.get("suitability_score", 0.5),
            area_ha=p.get("area_ha", 100),
            ndvi=p.get("ndvi", 0.4),
            forest_density=p.get("forest_density", 0.5),
            dist_to_road_m=p.get("dist_to_road_m", 1000),
            name=p.get("name", f"Patch-{p['id']}"),
        )

    G = nx.Graph()
    for nid, node in nodes.items():
        G.add_node(nid, **{
            "lat": node.lat, "lon": node.lon,
            "suitability": node.suitability,
            "area_ha": node.area_ha,
            "name": node.name,
        })

    ids = list(nodes.keys())
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = nodes[ids[i]], nodes[ids[j]]
            prob = movement_probability(a, b, dispersal)
            if prob > 0.001:  # only add meaningful edges
                r = resistance(prob)
                G.add_edge(ids[i], ids[j], weight=r, probability=prob,
                           distance_km=haversine_km(a.lat, a.lon, b.lat, b.lon))

    logger.info(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G, nodes


# ── Least-cost path analysis ─────────────────────────────────────────────────

def find_least_cost_paths(
    G: nx.Graph,
    nodes: dict[int, HabitatNode],
    source_ids: list[int],
    target_ids: list[int],
    top_k: int = 3,
) -> list[CorridorPath]:
    """
    Find the top-k least-cost paths between source and target node sets.
    Uses Dijkstra on the resistance-weighted graph.
    """
    paths: list[CorridorPath] = []

    for src in source_ids:
        for tgt in target_ids:
            if src == tgt or src not in G or tgt not in G:
                continue
            try:
                path_nodes = nx.dijkstra_path(G, src, tgt, weight="weight")
                cost = nx.dijkstra_path_length(G, src, tgt, weight="weight")

                # Compute path metrics
                edge_costs = []
                total_km = 0.0
                for k in range(len(path_nodes) - 1):
                    u, v = path_nodes[k], path_nodes[k + 1]
                    edge_data = G[u][v]
                    edge_costs.append((u, v, edge_data["weight"]))
                    total_km += edge_data.get("distance_km", 0)

                # Bottleneck = highest-resistance edge
                if edge_costs:
                    bn_u, bn_v, bn_cost = max(edge_costs, key=lambda x: x[2])
                    bn_node = bn_u  # the upstream node of the bottleneck edge
                else:
                    bn_cost, bn_node = cost, path_nodes[0]

                # Normalise resistance to permeability 0–1
                max_r = 1000.0
                permeability = round(max(0, 1.0 - (cost / (len(path_nodes) * max_r))), 3)

                paths.append(CorridorPath(
                    nodes=path_nodes,
                    total_resistance=round(cost, 2),
                    bottleneck_resistance=round(bn_cost, 2),
                    bottleneck_node_id=bn_node,
                    length_approx_km=round(total_km, 1),
                    permeability=permeability,
                ))
            except nx.NetworkXNoPath:
                logger.debug(f"No path from {src} to {tgt}")
            except Exception as e:
                logger.warning(f"Path error {src}→{tgt}: {e}")

    # Sort by total resistance (ascending = best paths first)
    paths.sort(key=lambda p: p.total_resistance)
    return paths[:top_k]


# ── Bottleneck detection ─────────────────────────────────────────────────────

def detect_bottlenecks(
    G: nx.Graph,
    nodes: dict[int, HabitatNode],
    top_n: int = 5,
) -> list[dict[str, Any]]:
    """
    Identify bottleneck habitat patches using:
      - Betweenness centrality (how often a node lies on shortest paths)
      - Low local suitability (the node is both critical AND poor quality)
    """
    if not G.nodes:
        return []

    # Betweenness centrality on resistance-weighted graph
    try:
        bc = nx.betweenness_centrality(G, weight="weight", normalized=True)
    except Exception:
        bc = {n: 0.0 for n in G.nodes}

    # Combine: bottleneck score = centrality × (1 – suitability)
    bottleneck_scores = {}
    for nid in G.nodes:
        suit = nodes.get(nid, HabitatNode(nid, 0, 0, 0, 0, 0, 0, 0)).suitability
        bottleneck_scores[nid] = bc.get(nid, 0) * (1.0 - suit)

    top_nodes = sorted(bottleneck_scores, key=bottleneck_scores.get, reverse=True)[:top_n]

    results = []
    for nid in top_nodes:
        node = nodes.get(nid)
        if node:
            results.append({
                "patch_id": nid,
                "name": node.name,
                "lat": node.lat,
                "lon": node.lon,
                "suitability": node.suitability,
                "centrality": round(bc.get(nid, 0), 4),
                "bottleneck_score": round(bottleneck_scores[nid], 4),
                "intervention": _bottleneck_intervention(node),
            })
    return results


def _bottleneck_intervention(node: HabitatNode) -> str:
    if node.dist_to_road_m < 500:
        return "Wildlife crossing or road mitigation required"
    if node.suitability < 0.4:
        return "Habitat restoration / reforestation priority"
    if node.forest_density < 0.4:
        return "Tree planting to increase canopy connectivity"
    return "Buffer zone protection"


# ── Connectivity score ───────────────────────────────────────────────────────

def compute_connectivity_score(
    G: nx.Graph,
    paths: list[CorridorPath],
    nodes: dict[int, HabitatNode],
) -> float:
    """
    Composite 0–100 connectivity score combining:
      - Graph density (edges / possible edges)
      - Mean patch suitability
      - Best path permeability
      - Component connectivity
    """
    if not G.nodes:
        return 0.0

    n = G.number_of_nodes()
    e = G.number_of_edges()
    max_edges = n * (n - 1) / 2 if n > 1 else 1
    density = e / max_edges

    mean_suit = np.mean([d["suitability"] for _, d in G.nodes(data=True)])

    best_perm = max((p.permeability for p in paths), default=0.0)

    # Largest connected component as fraction of total nodes
    cc = max(nx.connected_components(G), key=len)
    cc_ratio = len(cc) / n

    score = (
        0.25 * density * 100 +
        0.30 * mean_suit * 100 +
        0.30 * best_perm * 100 +
        0.15 * cc_ratio * 100
    )
    return round(min(score, 100.0), 1)


# ── GNN prototype (PyTorch) ──────────────────────────────────────────────────

def build_gnn_embeddings(
    patches: list[dict],
    graph: nx.Graph,
) -> dict[int, list[float]]:
    """
    Prototype Graph Neural Network that computes node embeddings via
    mean neighbourhood aggregation (1-layer GraphSAGE-style).

    In production this would use torch_geometric with trained weights.
    Here we produce meaningful embeddings without GPU dependency.
    """
    try:
        import torch
        import torch.nn.functional as F

        # Build feature matrix
        patch_map = {p["id"]: p for p in patches}
        node_ids = list(graph.nodes)
        n = len(node_ids)
        idx_map = {nid: i for i, nid in enumerate(node_ids)}

        X = torch.zeros(n, 5)
        for i, nid in enumerate(node_ids):
            p = patch_map.get(nid, {})
            X[i] = torch.tensor([
                p.get("suitability_score", 0.5),
                min(p.get("area_ha", 100) / 1000, 1.0),
                max(p.get("ndvi", 0.4), 0),
                p.get("forest_density", 0.5),
                min(p.get("dist_to_road_m", 1000) / 5000, 1.0),
            ])

        # Simple 1-layer mean aggregation: h_v = ReLU(W · mean(h_neighbours))
        W = torch.tensor([
            [0.4, 0.2, 0.2, 0.1, 0.1],
            [0.1, 0.3, 0.2, 0.2, 0.2],
            [0.2, 0.1, 0.4, 0.2, 0.1],
            [0.3, 0.2, 0.1, 0.3, 0.1],
        ])  # 4-dim embedding

        H = torch.zeros(n, 4)
        for i, nid in enumerate(node_ids):
            neighbours = list(graph.neighbors(nid))
            if neighbours:
                nbr_idx = [idx_map[nb] for nb in neighbours if nb in idx_map]
                nbr_feats = X[nbr_idx].mean(dim=0)
            else:
                nbr_feats = X[i]
            agg = (X[i] + nbr_feats) / 2.0
            H[i] = F.relu(W @ agg)

        # Normalise embeddings
        H = F.normalize(H, dim=1)

        return {nid: H[i].tolist() for i, nid in enumerate(node_ids)}

    except Exception as e:
        logger.warning(f"GNN embedding failed: {e}. Using feature vectors.")
        patch_map = {p["id"]: p for p in patches}
        return {
            nid: [
                patch_map.get(nid, {}).get("suitability_score", 0.5),
                min(patch_map.get(nid, {}).get("area_ha", 100) / 1000, 1.0),
                max(patch_map.get(nid, {}).get("ndvi", 0.4), 0.0),
                patch_map.get(nid, {}).get("forest_density", 0.5),
            ]
            for nid in graph.nodes
        }


# ── Main analysis entry point ────────────────────────────────────────────────

def analyse_corridor_connectivity(
    corridor_id: int,
    patches: list[dict],
    species: str = "all",
) -> ConnectivityResult:
    """
    Full connectivity analysis pipeline:
      1. Score habitat patches
      2. Build resistance graph
      3. Find least-cost paths
      4. Detect bottlenecks
      5. Compute GNN embeddings
      6. Return connectivity score + explanation
    """
    t0 = time.time()

    if not patches:
        return ConnectivityResult(
            corridor_id=corridor_id, graph_nodes=0, graph_edges=0,
            least_cost_paths=[], bottleneck_zones=[],
            connectivity_score=0, node_centrality={},
            computation_time_s=0, explanation="No habitat patches found.",
        )

    # Score patches with habitat model
    from app.ml.habitat_model import score_habitat_patches
    scored = score_habitat_patches(patches, species)

    # Build graph
    G, node_map = build_habitat_graph(scored, species)

    # Identify source (first corridor end) and target (last) nodes
    sorted_by_id = sorted(node_map.keys())
    n = len(sorted_by_id)
    sources = sorted_by_id[:max(1, n // 3)]
    targets = sorted_by_id[max(1, 2 * n // 3):]

    # Least-cost paths
    paths = find_least_cost_paths(G, node_map, sources, targets)

    # Bottlenecks
    bottlenecks = detect_bottlenecks(G, node_map)

    # Connectivity score
    score = compute_connectivity_score(G, paths, node_map)

    # GNN embeddings (stored, not returned directly)
    embeddings = build_gnn_embeddings(scored, G)

    # Centrality
    try:
        centrality = nx.betweenness_centrality(G, weight="weight", normalized=True)
        centrality = {k: round(v, 4) for k, v in centrality.items()}
    except Exception:
        centrality = {}

    elapsed = round(time.time() - t0, 3)

    # Build explanation
    best_path = paths[0] if paths else None
    explanation = (
        f"Connectivity analysis for corridor {corridor_id} | species: {species}. "
        f"Graph: {G.number_of_nodes()} habitat patches, {G.number_of_edges()} movement edges. "
        f"Connectivity score: {score}/100. "
    )
    if best_path:
        bn_name = node_map.get(best_path.bottleneck_node_id, HabitatNode(0,0,0,0,0,0,0,0)).name
        explanation += (
            f"Best path: {len(best_path.nodes)} patches, "
            f"~{best_path.length_approx_km} km, "
            f"permeability {best_path.permeability:.2f}. "
            f"Key bottleneck: {bn_name}. "
        )
    if bottlenecks:
        explanation += f"Top intervention needed: {bottlenecks[0]['intervention']}."

    return ConnectivityResult(
        corridor_id=corridor_id,
        graph_nodes=G.number_of_nodes(),
        graph_edges=G.number_of_edges(),
        least_cost_paths=paths,
        bottleneck_zones=bottlenecks,
        connectivity_score=score,
        node_centrality=centrality,
        computation_time_s=elapsed,
        explanation=explanation,
    )
