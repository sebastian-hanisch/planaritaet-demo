"""Szenario: Graphen, an denen Planarität geprüft wird (Karte, Raster, Zufallsverbindungen, Lehrbuch-Graphen, Toronto-Karte).

Ein Graph ist eine Kantenliste über den Knoten 0 bis n − 1 (ungerichtet, einfach, jede Kante als (u, v) mit u < v) und eine Lage der Knoten
für die Zeichnung. Die Lage ist **nur ein Layout**: Planarität ist eine Eigenschaft des Graphen, nicht seiner Zeichnung."""

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import plt_constants as C

DATA = Path(__file__).resolve().parent / "data"


@dataclass(frozen=True)
class Instance:
    """n Knoten, Kanten (sortierte Paare), Lage der Knoten (x, y) und ein Name für die Anzeige."""

    n: int
    edges: tuple[tuple[int, int], ...]
    pos: tuple[tuple[float, float], ...]
    name: str = ""

    @property
    def m(self) -> int:
        return len(self.edges)


def normalize_edges(edges) -> tuple[tuple[int, int], ...]:
    """Sortierte, doppelfreie Kantenliste ohne Schlingen."""
    return tuple(sorted({(min(u, v), max(u, v)) for u, v in edges if u != v}))


def euler_bound(n: int, bipartite: bool = False) -> int:
    """Höchste Kantenzahl eines planaren einfachen Graphen mit n Knoten: 3n − 6 (2n − 4 ohne Dreiecke); ab n = 3 gültig, darunter alle Paare."""
    if n < 3:
        return n * (n - 1) // 2
    return 2 * n - 4 if bipartite else 3 * n - 6


def target_edge_count(n: int, density: int) -> int:
    """Kantenzahl, die ein Netz bei dieser Dichte (Prozent von 3n − 6) haben soll."""
    return max(0, round(density / 100 * euler_bound(n)))


def circle_layout(n: int) -> tuple[tuple[float, float], ...]:
    return tuple((round(math.cos(2 * math.pi * i / n), 4), round(math.sin(2 * math.pi * i / n), 4)) for i in range(n))


def _delaunay_edges(points: np.ndarray) -> list[tuple[int, int]]:
    """Kanten der Delaunay-Triangulierung (scipy/Qhull, nur hier gebraucht)."""
    from scipy.spatial import Delaunay

    tri = Delaunay(points)
    found = set()
    for simplex in tri.simplices:
        a, b, c = (int(x) for x in simplex)
        found.update({(min(a, b), max(a, b)), (min(b, c), max(b, c)), (min(a, c), max(a, c))})
    return sorted(found)


def _pick(rng, candidates: list, count: int) -> list:
    """`count` Elemente zufällig (ohne Zurücklegen), die Reihenfolge der Kandidaten entscheidet nicht."""
    count = min(count, len(candidates))
    if count <= 0:
        return []
    chosen = rng.choice(len(candidates), size=count, replace=False)
    return [candidates[int(i)] for i in sorted(chosen)]


def make_delaunay(n: int, density: int, seed: int) -> Instance:
    """Zufällige Standorte im Einheitsquadrat, Kanten aus ihrer Delaunay-Triangulierung (verdünnt auf die Dichte)."""
    rng = np.random.default_rng(seed)
    points = rng.random((n, 2))
    all_edges = _delaunay_edges(points)
    kept = _pick(rng, all_edges, target_edge_count(n, density))
    pos = tuple((round(float(x), 4), round(float(y), 4)) for x, y in points)
    return Instance(n, normalize_edges(kept), pos, "Karte")


def grid_dimensions(n: int) -> tuple[int, int]:
    """Spalten und Zeilen eines Rasters mit n Knoten (Zeile für Zeile gefüllt, die letzte Zeile darf unvollständig sein)."""
    width = max(2, math.ceil(math.sqrt(n)))
    return width, math.ceil(n / width)


def make_grid(n: int, density: int, seed: int) -> Instance:
    """Raster: zuerst Gitterkanten, dann eine Diagonale je Zelle; zufällig verdünnt auf die Dichte."""
    rng = np.random.default_rng(seed)
    width, _ = grid_dimensions(n)

    def node(r, c):
        i = r * width + c
        return i if c < width and i < n else None

    lattice, diagonal = [], []
    for i in range(n):
        r, c = divmod(i, width)
        right, below, diag = node(r, c + 1), node(r + 1, c), node(r + 1, c + 1)
        if right is not None and c + 1 < width:
            lattice.append((i, right))
        if below is not None:
            lattice.append((i, below))
        if diag is not None and c + 1 < width and right is not None and below is not None:
            diagonal.append((i, diag))
    want = target_edge_count(n, density)
    if want <= len(lattice):
        kept = _pick(rng, lattice, want)
    else:
        kept = lattice + _pick(rng, diagonal, want - len(lattice))
    pos = tuple((float(i % width), float(-(i // width))) for i in range(n))
    return Instance(n, normalize_edges(kept), pos, "Raster")


def make_random_pairs(n: int, density: int, seed: int) -> Instance:
    """m zufällig gewählte Paare, Knoten auf einem Kreis angeordnet (das Layout sagt nichts über Planarität)."""
    rng = np.random.default_rng(seed)
    pairs = [(u, v) for u in range(n) for v in range(u + 1, n)]
    kept = _pick(rng, pairs, target_edge_count(n, density))
    return Instance(n, normalize_edges(kept), circle_layout(n), "Zufallsverbindungen")


def add_extra_edges(inst: Instance, k: int, seed: int) -> Instance:
    """k zusätzliche Kanten zwischen zufälligen, bisher nicht verbundenen Paaren (weniger, falls es nicht so viele Paare gibt)."""
    if k <= 0:
        return inst
    rng = np.random.default_rng(seed + 7919)
    present = set(inst.edges)
    free = [(u, v) for u in range(inst.n) for v in range(u + 1, inst.n) if (u, v) not in present]
    extra = _pick(rng, free, k)
    return Instance(inst.n, normalize_edges(list(inst.edges) + extra), inst.pos, inst.name)


def make_instance(net: str, n: int, density: int, extra: int, seed: int) -> Instance:
    """Deterministisch aus den fünf Reglern: gleiche Eingabe, gleiche Instanz."""
    base = {"delaunay": make_delaunay, "grid": make_grid, "gnc": make_random_pairs}[net](n, density, seed)
    return add_extra_edges(base, extra, seed)


# --- Lehrbuch-Graphen -----------------------------------------------------------------------------------------------------------------------


def _pentagon(radius: float, phase: float = 90.0) -> list[tuple[float, float]]:
    return [(round(radius * math.cos(math.radians(phase + 72 * i)), 4), round(radius * math.sin(math.radians(phase + 72 * i)), 4)) for i in range(5)]


def _hexagon_bipartite() -> tuple[tuple[float, float], ...]:
    """Die Knoten 0, 1, 2 und 3, 4, 5 abwechselnd auf einem Sechseck (die übliche Zeichnung von K3,3 mit drei Kreuzungen)."""
    angles = {0: 90, 3: 150, 1: 210, 4: 270, 2: 330, 5: 30}
    return tuple((round(math.cos(math.radians(angles[i])), 4), round(math.sin(math.radians(angles[i])), 4)) for i in range(6))


def _midpoint(a, b) -> tuple[float, float]:
    return (round((a[0] + b[0]) / 2, 4), round((a[1] + b[1]) / 2, 4))


def hand_graph(name: str) -> Instance:
    """Die neun Lehrbuch-Graphen; die planaren sind kreuzungsfrei gezeichnet, die übrigen in einer üblichen Lage."""
    if name == "K4":
        pos = ((0.0, 1.3), (-1.2, -0.8), (1.2, -0.8), (0.0, 0.0))
        edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    elif name == "Würfel":
        pos = ((-1.2, 1.2), (1.2, 1.2), (1.2, -1.2), (-1.2, -1.2), (-0.6, 0.6), (0.6, 0.6), (0.6, -0.6), (-0.6, -0.6))
        edges = [(0, 1), (1, 2), (2, 3), (0, 3), (4, 5), (5, 6), (6, 7), (4, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
    elif name == "Oktaeder":
        pos = ((0.0, 1.4), (-1.2, -0.7), (1.2, -0.7), (0.0, -0.35), (0.45, 0.35), (-0.45, 0.35))
        edges = [(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5), (0, 4), (0, 5), (1, 3), (1, 5), (2, 3), (2, 4)]
    elif name == "K5 minus eine Kante":
        # Die Knoten 0 und 1 sind die einzigen nicht benachbarten; 2, 3, 4 bilden das Dreieck dazwischen: 0 liegt oben außen, 4 in der Mitte, 1 darunter
        pos = ((0.0, 1.3), (0.0, -0.45), (-1.2, -0.8), (1.2, -0.8), (0.0, 0.1))
        edges = [(0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]
    elif name == "K5":
        pos = circle_layout(5)
        edges = [(u, v) for u in range(5) for v in range(u + 1, 5)]
    elif name == "K3,3":
        pos = _hexagon_bipartite()
        edges = [(a, b) for a in range(3) for b in range(3, 6)]
    elif name == "Petersen-Graph":
        outer, inner = _pentagon(1.4), _pentagon(0.7)
        pos = tuple(outer + inner)
        edges = [(i, (i + 1) % 5) for i in range(5)] + [(i, i + 5) for i in range(5)] + [(5 + i, 5 + (i + 2) % 5) for i in range(5)]
    elif name == "Wagner-Graph":
        pos = circle_layout(8)
        edges = [(i, (i + 1) % 8) for i in range(8)] + [(i, i + 4) for i in range(4)]
    elif name == "K3,3 mit Unterteilungen":
        # K3,3 (Knoten 0..5), die Kanten 0-3 und 1-4 sind durch die Knoten 6 und 7 unterteilt
        base = _hexagon_bipartite()
        pos = base + (_midpoint(base[0], base[3]), _midpoint(base[1], base[4]))
        edges = [(a, b) for a in range(3) for b in range(3, 6) if (a, b) not in ((0, 3), (1, 4))] + [(0, 6), (6, 3), (1, 7), (7, 4)]
    else:
        raise ValueError(f"unbekannter Lehrbuch-Graph: {name}")
    return Instance(len(pos), normalize_edges(edges), tuple(pos), name)


# --- Toronto-Karte --------------------------------------------------------------------------------------------------------------------------


def load_toronto() -> tuple[Instance, dict]:
    """Straßenkarte aus OpenStreetMap (ODbL, Auszug aus bfs-demo): Kanten ungerichtet vereinigt; dazu die Kantenlängen (Meter) laut Datei."""
    payload = json.loads((DATA / "toronto_campus.json").read_text(encoding="utf-8"))
    pos = tuple((float(x), float(y)) for x, y in payload["nodes_xy_m"])
    length: dict[tuple[int, int], float] = {}
    for u, v, w in payload["arcs"]:
        if u == v:
            continue
        key = (min(u, v), max(u, v))
        length[key] = min(length.get(key, float("inf")), float(w))
    inst = Instance(len(pos), tuple(sorted(length)), pos, "Toronto-Karte")
    return inst, length
