"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): kleinste Graphen, Entartungen, Gleichstände, inklusive Grenzen."""

import pytest

import plt_algorithm as A
import plt_constants as C
import plt_evaluation as ev
import plt_scenario as S


def test_empty_graph_and_single_vertex():
    e = A.embed(0, [])
    assert e.planar and e.blocks == () and e.components == 0
    e = A.embed(1, [])
    assert e.planar and e.components == 1 and e.faces == 1 and e.steps == 0


def test_exactly_two_vertices_and_one_edge():
    """n = 2: der kleinste Fall mit einer Kante, ein Block aus einer Brücke; die Fläche ist die eine Ebene (m − n + 1 + c = 1)."""
    e = A.embed(2, [(0, 1)])
    assert e.planar and len(e.blocks) == 1 and e.blocks[0].faces == () and e.faces == 1


def test_triangle_is_the_smallest_embedding_with_two_faces():
    e = A.embed(3, [(0, 1), (1, 2), (0, 2)])
    assert e.planar and e.faces == 2 and len(e.blocks[0].faces) == 2 and [ev_.kind for ev_ in e.blocks[0].events] == ["cycle"]


def test_duplicate_edges_and_reversed_pairs_count_once():
    e = A.embed(3, [(0, 1), (1, 0), (1, 2), (0, 2), (2, 0)])
    assert e.m == 3 and e.planar


def test_isolated_vertices_and_components_do_not_disturb():
    edges = [(u, v) for u in range(5) for v in range(u + 1, 5)]       # K5 auf 0..4
    e = A.embed(9, edges)                                             # dazu 4 isolierte Knoten
    assert not e.planar and e.components == 5


def test_star_and_path_are_planar_forests_without_embedding_steps():
    assert A.embed(6, [(0, k) for k in range(1, 6)]).steps == 0
    e = A.embed(5, [(k, k + 1) for k in range(4)])
    assert e.planar and e.faces == 1 and all(not b.faces for b in e.blocks)


def test_the_bound_is_inclusive_at_exactly_3n_minus_6():
    """Ein maximal planarer Graph (Oktaeder: n = 6, m = 12 = 3n − 6) ist planar; mit einer weiteren Kante (13) nicht mehr."""
    g = S.hand_graph("Oktaeder")
    assert g.m == S.euler_bound(g.n) and A.embed(g.n, g.edges).planar
    missing = [(u, v) for u in range(6) for v in range(u + 1, 6) if (u, v) not in set(g.edges)]
    assert not A.embed(g.n, list(g.edges) + [missing[0]]).planar


def test_k5_minus_an_edge_is_planar_but_k5_is_not():
    assert A.embed(5, S.hand_graph("K5 minus eine Kante").edges).planar and not A.embed(5, S.hand_graph("K5").edges).planar


def test_the_witness_of_a_block_that_is_exactly_k33_is_the_whole_block():
    g = S.hand_graph("K3,3")
    w = A.witness_for(A.embed(g.n, g.edges))
    assert w.edges == g.edges and w.kind == "K3,3" and w.tests == g.m


def test_no_witness_for_planar_graphs_and_none_for_oversized_blocks():
    assert A.witness_for(A.embed(4, S.hand_graph("K4").edges)) is None
    g = S.hand_graph("K5")
    assert A.witness_for(A.embed(g.n, g.edges), max_edges=g.m - 1) is None and A.witness_for(A.embed(g.n, g.edges), max_edges=g.m) is not None


def test_ties_are_broken_by_the_smaller_vertex_number_and_results_repeat():
    inst = S.make_instance("gnc", 20, 50, 0, 1)
    first, second = A.embed(inst.n, inst.edges), A.embed(inst.n, inst.edges)
    assert first == second
    assert A.witness_for(first) == A.witness_for(second)


@pytest.mark.parametrize("net", list(C.NET_TYPES))
@pytest.mark.parametrize("n", [C.N_MIN, C.N_MAX])
@pytest.mark.parametrize("density", [C.DENSITY_MIN, C.DENSITY_MAX])
@pytest.mark.parametrize("extra", [C.EXTRA_MIN, C.EXTRA_MAX])
def test_every_corner_of_the_controls_gives_a_consistent_analysis(net, n, density, extra):
    a = ev.analyse(ev.Settings(net, n, density, extra, 7))
    assert a.inst.n == n and a.emb.planar == (a.witness is None)
    kind, text = ev.verdict_planarity(a)
    assert kind in ("success", "error") and text


def test_fully_connected_extra_edges_cannot_exceed_the_free_pairs():
    """Mehr Zusatzkanten als freie Paare: es kommen nur die freien dazu."""
    inst = S.Instance(4, S.normalize_edges([(0, 1), (0, 2), (0, 3), (1, 2), (1, 3)]), S.circle_layout(4), "x")
    assert S.add_extra_edges(inst, 5, 1).m == 6
    assert S.add_extra_edges(inst, 0, 1) == inst
