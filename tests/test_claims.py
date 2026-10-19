"""Jede Zahl der README wird hier nachgerechnet (DEMO-PLAYBOOK §4): über dieselben Auswertungsfunktionen wie in der App.

Zufallsabhängige Anteile (100 Graphen je Zelle) mit Band, weil die Bibliotheksversionen der CI die Ziehungen verschieben dürfen; Zahlen aus den Toronto-Daten und
Handrechnungen exakt."""

import json

import pytest

import plt_algorithm as A
import plt_constants as C
import plt_evaluation as ev
import plt_scenario as S

BAND = 0.06


@pytest.fixture(scope="module")
def toronto():
    return ev.toronto_stats()


@pytest.fixture(scope="module")
def share_rows():
    return ev.share_table()


def _share(rows, n, density):
    return next(r["share"] for r in rows if r["n"] == n and r["density"] == density)


def test_share_table(share_rows):
    expected = {(20, 40): 0.90, (20, 50): 0.48, (20, 60): 0.08, (40, 30): 0.96, (40, 40): 0.22, (40, 50): 0.0}
    for (n, d), share in expected.items():
        assert _share(share_rows, n, d) == pytest.approx(share, abs=BAND), (n, d)
    assert ev.tipping_density(share_rows, 20) == 50 and ev.tipping_density(share_rows, 40) == 40
    assert [round(ev.mean_degree(20, 50), 1), round(ev.mean_degree(40, 40), 1)] == [2.7, 2.3]
    assert [round(ev.mean_degree(20, 100), 1), round(ev.mean_degree(40, 100), 1)] == [5.4, 5.7]
    assert C.SHARE_SAMPLES == 100 and C.SHARE_NS == (20, 40)


def test_plus_table():
    rows = ev.plus_table()
    expected = {(30, 0): 0.0, (30, 1): 0.48, (30, 2): 0.81, (30, 3): 0.91, (30, 5): 1.0, (60, 0): 0.0, (60, 1): 0.70, (60, 2): 0.93, (60, 3): 1.0, (60, 5): 1.0}
    for (n, k), share in expected.items():
        assert next(r["nonplanar"] for r in rows if r["n"] == n and r["k"] == k) == pytest.approx(share, abs=BAND), (n, k)
    assert C.PLUS_DENSITY == 60 and C.PLUS_SAMPLES == 100


def test_cost_table():
    rows = ev.cost_table()
    expected = {20: 1873, 40: 11891, 80: 78570, 160: 442477, 320: 2855431}
    for r in rows:
        assert r["steps"] == pytest.approx(expected[r["n"]], rel=0.1), r["n"]
    assert 2.5 <= ev.cost_exponent(rows) <= 2.7
    assert len(C.SWEEP_SEEDS) == 5


def test_euler_bound_is_not_sufficient():
    k33 = S.hand_graph("K3,3")
    assert k33.m == 9 and S.euler_bound(k33.n) == 12 and not A.embed(k33.n, k33.edges).planar
    a = ev.analyse(ev.Settings(**C.PRESETS["Eine Kante zu viel"]))
    assert (a.inst.m, a.bound, a.emb.planar) == (34, 36, False)


def test_toronto_witness_and_block(toronto):
    fixed = toronto["fixed"]
    assert (fixed["block_nodes"], fixed["block_edges"], fixed["witness_tests"]) == (4193, 6720, 1134)
    w = toronto["witness"]
    assert w.kind == "K3,3" and len(w.edges) == 37 and toronto["witness_problems"] == [] and toronto["witness_nonplanar"]
    inst = toronto["inst"]
    assert (inst.n, inst.m) == (5072, 7621)
    emb = A.embed(inst.n, inst.edges)
    assert not emb.planar and len(emb.blocks[emb.failed_block].nodes) == 4193 and len(emb.blocks[emb.failed_block].edges) == 6720


def test_toronto_crossings_and_cover(toronto):
    assert toronto["crossings"] == 125 and toronto["involved_edges"] == 163 and toronto["cover_size"] == 52
    assert round(toronto["cover_size"] / toronto["inst"].m * 100, 1) == 0.7
    inst = toronto["inst"]
    assert sorted(tuple(inst.edges[i]) for i in toronto["cover"]) == sorted(tuple(e) for e in toronto["fixed"]["cover_edges"])
    covered = {i for p in toronto["pairs"] for i in p}
    assert set(toronto["cover"]) <= covered and all(i in set(toronto["cover"]) or j in set(toronto["cover"]) for i, j in toronto["pairs"])


def test_toronto_planar_after_cover(toronto):
    nx = pytest.importorskip("networkx")
    inst = toronto["inst"]
    removed = {tuple(e) for e in toronto["fixed"]["cover_edges"]}
    kept = [e for e in inst.edges if e not in removed]
    assert len(kept) == inst.m - 52 and toronto["fixed"]["planar_after_cover"] is True
    assert nx.check_planarity(nx.Graph(kept))[0] and not nx.check_planarity(nx.Graph(list(inst.edges)))[0]


def test_toronto_curvature(toronto):
    assert (toronto["curved_cross"], toronto["straight_cross"]) == (31, 51)
    assert round(toronto["median_ratio"], 3) == 1.004 and round(toronto["share_curved"] * 100, 1) == 7.4


def test_toronto_has_no_bridge_tags():
    payload = json.loads((S.DATA / "toronto_campus.json").read_text(encoding="utf-8"))
    assert set(payload) == {"source", "center", "dist_m", "network_type", "start", "goal", "nodes_xy_m", "arcs"}
    assert all(len(a) == 3 for a in payload["arcs"])                          # Knoten, Knoten, Länge: nichts über Brücken oder Tunnel


def test_textbook_graphs():
    planar = {name for name in C.HAND_GRAPHS if A.embed(S.hand_graph(name).n, S.hand_graph(name).edges).planar}
    assert planar == {"K4", "Würfel", "Oktaeder", "K5 minus eine Kante"}
    for name in ("K5", "K3,3", "Petersen-Graph", "Wagner-Graph", "K3,3 mit Unterteilungen"):
        g = S.hand_graph(name)
        w = A.witness_for(A.embed(g.n, g.edges))
        assert w is not None and w.kind in ("K5", "K3,3") and A.verify_witness(g.edges, w) == [], name
