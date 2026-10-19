"""Szenario: Generatoren (Eigenschaften, Determinismus), Lehrbuch-Graphen und die Toronto-Daten."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import plt_algorithm as A
import plt_constants as C
import plt_scenario as S

ROOT = Path(__file__).resolve().parent.parent


def test_target_edge_count_is_a_percentage_of_the_bound():
    assert S.target_edge_count(14, 100) == 36 and S.target_edge_count(14, 50) == 18 and S.target_edge_count(14, 5) == 2


def test_same_inputs_give_the_same_instance_and_other_seeds_differ():
    for net in C.NET_TYPES:
        a = S.make_instance(net, 20, 60, 1, 4)
        assert a == S.make_instance(net, 20, 60, 1, 4)
        assert a != S.make_instance(net, 20, 60, 1, 5)


def test_edges_are_sorted_simple_pairs_inside_the_vertex_range():
    for net in C.NET_TYPES:
        inst = S.make_instance(net, 25, 80, 3, 2)
        assert list(inst.edges) == sorted(set(inst.edges)) and all(0 <= u < v < inst.n for u, v in inst.edges)
        assert len(inst.pos) == inst.n


@pytest.mark.parametrize("n", [6, 7, 12, 25, 60])
@pytest.mark.parametrize("density", [5, 50, 100])
def test_maps_and_grids_without_extra_edges_are_planar_and_below_the_bound(n, density):
    for net in ("delaunay", "grid"):
        inst = S.make_instance(net, n, density, 0, 3)
        assert A.embed(inst.n, inst.edges).planar and inst.m <= S.euler_bound(n), (net, n, density)


def test_the_map_with_full_density_has_all_triangulation_edges():
    inst = S.make_instance("delaunay", 30, 100, 0, 3)
    assert inst.m <= 3 * 30 - 6 and inst.m >= 30 - 1
    assert A.embed(inst.n, inst.edges).faces == inst.m - inst.n + 2        # zusammenhängend: Euler


def test_grid_dimensions_and_edge_counts():
    assert S.grid_dimensions(25) == (5, 5) and S.grid_dimensions(7) == (3, 3) and S.grid_dimensions(6) == (3, 2)
    full = S.make_instance("grid", 25, 58, 0, 1)                           # 58 % von 69 = 40 Kanten = alle Gitterkanten eines 5 × 5-Gitters
    assert full.m == 40
    assert sorted({(round(x), round(y)) for x, y in full.pos}) == sorted((c, -r) for r in range(5) for c in range(5))
    assert S.make_instance("grid", 25, 100, 0, 1).m == 40 + 16             # dazu alle 16 Diagonalen: 3 · 25 − 6 = 69 wäre mehr, das Raster hat nur 56


def test_a_grid_with_a_partial_last_row_keeps_all_nodes():
    inst = S.make_instance("grid", 7, 100, 0, 1)
    assert inst.n == 7 and all(0 <= u < v < 7 for u, v in inst.edges) and A.embed(7, inst.edges).planar


def test_random_pairs_have_exactly_the_requested_number_of_edges():
    for density in (5, 40, 100):
        assert S.make_instance("gnc", 20, density, 0, 2).m == S.target_edge_count(20, density)


def test_extra_edges_add_exactly_k_new_pairs():
    base = S.make_instance("delaunay", 20, 60, 0, 6)
    more = S.make_instance("delaunay", 20, 60, 4, 6)
    assert more.m == base.m + 4 and set(base.edges) <= set(more.edges)


def test_the_instance_does_not_depend_on_the_hash_seed():
    code = (
        "import sys; sys.path.insert(0, %r); import plt_scenario as S, plt_evaluation as ev; "
        "a = ev.analyse(ev.Settings('gnc', 20, 50, 1, 7)); print(a.inst.edges, a.emb.steps, a.witness.edges)" % str(ROOT)
    )
    outputs = []
    for hash_seed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONIOENCODING="utf-8")
        out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True).stdout
        outputs.append(out)
    assert outputs[0] == outputs[1] and outputs[0].strip()


EXPECTED = {
    "K4": (4, 6, True), "Würfel": (8, 12, True), "Oktaeder": (6, 12, True), "K5 minus eine Kante": (5, 9, True),
    "K5": (5, 10, False), "K3,3": (6, 9, False), "Petersen-Graph": (10, 15, False), "Wagner-Graph": (8, 12, False), "K3,3 mit Unterteilungen": (8, 11, False),
}


def test_the_textbook_graphs_have_the_documented_size_and_planarity():
    assert set(EXPECTED) == set(C.HAND_GRAPHS)
    for name, (n, m, planar) in EXPECTED.items():
        g = S.hand_graph(name)
        assert (g.n, g.m) == (n, m), name
        assert A.embed(g.n, g.edges).planar is planar, name


def test_petersen_and_wagner_are_cubic():
    for name in ("Petersen-Graph", "Wagner-Graph", "K3,3", "Würfel"):
        g = S.hand_graph(name)
        assert {len(a) for a in A.adjacency(g.n, g.edges)} == {3}, name


def test_unknown_textbook_graph_is_rejected():
    with pytest.raises(ValueError):
        S.hand_graph("Banane")


def test_toronto_data_and_license():
    inst, length = S.load_toronto()
    assert (inst.n, inst.m) == (5072, 7621) and set(length) == set(inst.edges)
    assert all(w > 0 for w in length.values())
    assert (S.DATA / "LICENSE-ODbL.md").exists()
    fixed = json.loads((S.DATA / "toronto_befund.json").read_text(encoding="utf-8"))
    assert set(fixed) >= {"witness_edges", "cover_edges", "planar_after_cover", "block_nodes", "block_edges", "witness_tests"}
