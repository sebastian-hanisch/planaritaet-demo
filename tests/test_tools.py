"""Das Werkzeug, das den schweren Toronto-Teil vorrechnet: `ddmin` liefert auf kleinen Graphen kantenminimale nichtplanare Teilgraphen."""

import importlib.util
import random
from pathlib import Path

import plt_algorithm as A

ROOT = Path(__file__).resolve().parent.parent


def _tool():
    spec = importlib.util.spec_from_file_location("toronto_befund", ROOT / "tools" / "toronto_befund.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ddmin_finds_a_minimal_nonplanar_subgraph_like_the_edge_deletion():
    tool = _tool()
    rng = random.Random(13)
    for _ in range(25):
        n = rng.randint(7, 12)
        pairs = [(u, v) for u in range(n) for v in range(u + 1, n)]
        edges = sorted(rng.sample(pairs, min(len(pairs), 2 * n)))
        if A.is_planar_edges(edges):
            continue
        reduced, tests = tool.ddmin(edges, lambda es: not A.is_planar_edges(es))
        assert tests > 0 and not A.is_planar_edges(reduced)
        for e in reduced:
            assert A.is_planar_edges([x for x in reduced if x != e])       # 1-minimal
        w = A.classify_witness(reduced, tests)
        assert w.kind in ("K5", "K3,3") and A.verify_witness(edges, w) == []


def test_the_stored_toronto_witness_is_minimal():
    import json

    import plt_scenario as S

    fixed = json.loads((S.DATA / "toronto_befund.json").read_text(encoding="utf-8"))
    edges = [tuple(e) for e in fixed["witness_edges"]]
    assert not A.is_planar_edges(edges)
    for e in edges:
        assert A.is_planar_edges([x for x in edges if x != e])
