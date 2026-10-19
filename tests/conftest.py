"""Gemeinsame Fixtures: Mini-Graphen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def complete(n):
    return [(u, v) for u in range(n) for v in range(u + 1, n)]


def complete_bipartite(a, b):
    return [(u, a + v) for u in range(a) for v in range(b)]


@pytest.fixture
def k4():
    """K4: planar, 4 Knoten, 6 Kanten, genau 4 Flächen (Euler: 4 − 6 + 4 = 2)."""
    return 4, complete(4)


@pytest.fixture
def k5():
    return 5, complete(5)


@pytest.fixture
def k33():
    return 6, complete_bipartite(3, 3)


@pytest.fixture
def house():
    """Haus: Quadrat 0-1-2-3 mit Dach 4 über der Kante 0-1 (Knoten 4 mit 0 und 1 verbunden): Block mit 5 Knoten, 6 Kanten, planar, 3 Flächen."""
    return 5, [(0, 1), (1, 2), (2, 3), (0, 3), (0, 4), (1, 4)]
