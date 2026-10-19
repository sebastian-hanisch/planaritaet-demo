"""Einheiten des Kerns an Mini-Graphen, von Hand gerechnet (DEMO-PLAYBOOK §1b): eine Regel = ein Test."""

import pytest

import plt_algorithm as A
import plt_scenario as S


def _blocks(n, edges):
    return sorted(sorted(b) for b in A.biconnected_blocks(n, A.adjacency(n, edges)))


def test_blocks_of_a_triangle_with_a_tail():
    """Dreieck 0-1-2 mit Schwanz 2-3-4: ein Dreiecksblock und zwei Brücken."""
    edges = [(0, 1), (0, 2), (1, 2), (2, 3), (3, 4)]
    assert _blocks(5, edges) == [[(0, 1), (0, 2), (1, 2)], [(2, 3)], [(3, 4)]]


def test_blocks_of_two_triangles_sharing_a_vertex():
    edges = [(0, 1), (0, 2), (1, 2), (2, 3), (2, 4), (3, 4)]
    assert _blocks(5, edges) == [[(0, 1), (0, 2), (1, 2)], [(2, 3), (2, 4), (3, 4)]]


def test_components_count_isolated_vertices():
    assert A.components(5, A.adjacency(5, [(0, 1), (2, 3)])) == 3


def test_cycle_of_a_square_contains_all_four_vertices():
    adj = {0: {1, 3}, 1: {0, 2}, 2: {1, 3}, 3: {0, 2}}
    assert sorted(A.find_cycle(adj, {0, 1, 2, 3})) == [0, 1, 2, 3]


def test_a_tree_has_no_cycle():
    adj = {0: {1}, 1: {0, 2}, 2: {1}}
    assert A.find_cycle(adj, {0, 1, 2}) is None


def test_fragments_of_the_house_after_the_square():
    """Haus: Quadrat 0-1-2-3 ist eingebettet; der Dachknoten 4 hängt über 0 und 1: genau ein Fragment, zwei Nachbarbesuche."""
    edges = [(0, 1), (1, 2), (2, 3), (0, 3), (0, 4), (1, 4)]
    adj = A.adjacency(5, edges)
    frags, steps = A.fragments(adj, set(range(5)), {0, 1, 2, 3}, {(0, 1), (1, 2), (2, 3), (0, 3)})
    assert frags == [A.Fragment((0, 1), (4,))] and steps == 2


def test_fragments_report_a_single_edge_between_embedded_vertices():
    """Quadrat mit Diagonale 0-2: die Diagonale ist ein Fragment ohne inneren Knoten."""
    edges = [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2)]
    adj = A.adjacency(4, edges)
    frags, steps = A.fragments(adj, set(range(4)), {0, 1, 2, 3}, {(0, 1), (1, 2), (2, 3), (0, 3)})
    assert frags == [A.Fragment((0, 2), ())] and steps == 0


def test_admissible_faces_need_all_attachments_on_the_boundary():
    faces = [{0, 1, 2, 3}, {0, 1, 4}]
    assert A.admissible_faces(A.Fragment((0, 1), (9,)), faces) == [0, 1]
    assert A.admissible_faces(A.Fragment((2, 4), (9,)), faces) == []
    assert A.admissible_faces(A.Fragment((0, 2), ()), faces) == [0]


def test_the_fragment_with_the_fewest_admissible_faces_goes_first_and_ties_take_the_first():
    f = A.Fragment((0, 1), ())
    assert A.choose_fragment([(f, [0, 1]), (f, [1])]) == 1
    assert A.choose_fragment([(f, [0, 1]), (f, [1, 2])]) == 0
    assert A.choose_fragment([(f, [0]), (f, [1])]) == 0


def test_path_through_a_fragment_and_a_single_edge():
    edges = [(0, 1), (1, 2), (2, 3), (0, 3), (0, 4), (1, 4)]
    adj = A.adjacency(5, edges)
    assert A.path_in_fragment(adj, set(range(5)), A.Fragment((0, 1), (4,))) == [0, 4, 1]
    assert A.path_in_fragment(adj, set(range(5)), A.Fragment((0, 3), ())) == [0, 3]


def test_split_face_by_a_path_makes_a_triangle_and_a_pentagon():
    """Quadrat [0,1,2,3] und Weg 0-4-1: Dreieck [0,1,4] und Fünfeck [1,2,3,0,4] (Summe der Randlängen = 2 · 6 Kanten)."""
    first, second = A.split_face([0, 1, 2, 3], [0, 4, 1])
    assert first == [0, 1, 4] and second == [1, 2, 3, 0, 4]


def test_split_face_by_a_chord_keeps_both_halves_closed():
    first, second = A.split_face([0, 1, 2, 3], [0, 2])
    assert first == [0, 1, 2] and second == [2, 3, 0]


def test_house_is_embedded_with_three_faces():
    n, edges = 5, [(0, 1), (1, 2), (2, 3), (0, 3), (0, 4), (1, 4)]
    r = A.embed_block(edges)
    assert r.planar and len(r.faces) == 3 and sorted(len(f) for f in r.faces) == [3, 4, 5]
    assert A.euler_ok(r)
    assert [e.kind for e in r.events] == ["cycle", "path"]


def test_k4_has_four_triangular_faces(k4):
    n, edges = k4
    r = A.embed_block(edges)
    assert r.planar and sorted(len(f) for f in r.faces) == [3, 3, 3, 3] and A.euler_ok(r)


@pytest.mark.parametrize("fixture", ["k5", "k33"])
def test_the_two_kuratowski_graphs_fail_with_a_fragment_without_admissible_face(fixture, request):
    n, edges = request.getfixturevalue(fixture)
    r = A.embed_block(edges)
    assert not r.planar and r.faces == () and r.events[-1].kind == "fail"
    assert r.events[-1].fragment is not None and len(r.events[-1].fragment.attach) >= 2


def test_embed_of_a_disconnected_graph_counts_faces_by_euler():
    """Dreieck plus zwei isolierte Knoten: drei Komponenten; nach Euler n − m + f = 1 + c, also f = m − n + 1 + c = 3 − 5 + 1 + 3 = 2 Flächen."""
    e = A.embed(5, [(0, 1), (1, 2), (0, 2)])
    assert e.planar and e.components == 3 and e.faces == 2


def test_embedding_is_nonplanar_when_any_block_is():
    """K5 und ein Dreieck, durch einen Knoten verbunden: nichtplanar; der erste nichtplanare Block ist der K5-Block."""
    edges = [(u, v) for u in range(5) for v in range(u + 1, 5)] + [(4, 5), (5, 6), (4, 6)]
    e = A.embed(7, edges)
    assert not e.planar and e.faces is None and len(e.blocks[e.failed_block].nodes) == 5


def test_witness_of_k5_with_a_tail_is_k5_itself():
    edges = [(u, v) for u in range(5) for v in range(u + 1, 5)] + [(4, 5), (5, 6)]
    reduced, tests = A.witness_by_deletion(edges)
    assert list(reduced) == [(u, v) for u in range(5) for v in range(u + 1, 5)] and tests == len(edges)
    w = A.classify_witness(reduced, tests)
    assert w.kind == "K5" and w.branch == (0, 1, 2, 3, 4) and len(w.paths) == 10 and all(len(p) == 2 for p in w.paths)


def test_witness_of_a_subdivided_k33_has_two_longer_paths():
    inst = S.hand_graph("K3,3 mit Unterteilungen")
    reduced, _ = A.witness_by_deletion(inst.edges)
    w = A.classify_witness(reduced)
    assert reduced == inst.edges and w.kind == "K3,3" and len(w.branch) == 6 and len(w.paths) == 9
    assert sorted(len(p) for p in w.paths) == [2] * 7 + [3] * 2


def test_verify_witness_accepts_a_good_witness_and_names_defects():
    inst = S.hand_graph("K5")
    w = A.classify_witness(inst.edges)
    assert A.verify_witness(inst.edges, w) == []
    missing = A.Witness(w.kind, w.edges, w.branch, w.paths[:-1])
    assert any("genau einem Weg" in p for p in A.verify_witness(inst.edges, missing))
    foreign = A.Witness(w.kind, w.edges + ((0, 9),), w.branch, w.paths)
    assert any("nicht im Graphen" in p for p in A.verify_witness(inst.edges, foreign))
    assert A.verify_witness(inst.edges, A.Witness("?", w.edges, w.branch, w.paths))


def test_verify_witness_rejects_k5_branches_that_are_only_k33():
    g = S.hand_graph("K3,3")
    w = A.classify_witness(g.edges)
    fake = A.Witness("K5", w.edges, w.branch, w.paths)
    assert A.verify_witness(g.edges, fake)


def test_segments_cross_only_in_the_interior_of_both():
    assert A.segments_cross((0, 0), (2, 2), (0, 2), (2, 0))
    assert not A.segments_cross((0, 0), (2, 2), (2, 2), (4, 0))          # gemeinsamer Endpunkt
    assert not A.segments_cross((0, 0), (2, 0), (1, 0), (1, 2))          # Endpunkt der zweiten liegt auf der ersten (T-Stück)
    assert not A.segments_cross((0, 0), (2, 0), (0, 1), (2, 1))          # parallel
    assert not A.segments_cross((0, 0), (1, 1), (2, 2), (3, 3))          # kollinear, getrennt


def test_crossings_ignore_edges_sharing_a_vertex():
    pos = [(0, 0), (2, 2), (0, 2), (2, 0)]
    assert A.crossings(pos, [(0, 1), (2, 3)]) == [(0, 1)]
    assert A.crossings(pos, [(0, 1), (0, 2)]) == []


def test_greedy_cover_takes_the_edge_on_most_crossings_first():
    assert A.greedy_cover([(0, 1), (0, 2), (3, 4)]) == [0, 3]
    assert A.greedy_cover([]) == []


def test_euler_bound():
    assert S.euler_bound(4) == 6 and S.euler_bound(10) == 24 and S.euler_bound(10, bipartite=True) == 16
    assert S.euler_bound(2) == 1 and S.euler_bound(1) == 0
    assert A.euler_faces(4, 6, 1) == 4 and A.euler_faces(5, 3, 3) == 2


def test_k4_events_follow_the_documented_order():
    """K4: Anfangskreis (2, 1, 0) der Tiefensuche; der Knoten 3 hängt über 0, 1, 2 (zwei zulässige Flächen, Weg 0-3-1 über den kleinsten Anschlussknoten), die Kante 2-3 danach nur noch in einer Fläche."""
    r = A.embed_block([(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)])
    assert [(e.kind, e.path, e.admissible, e.faces) for e in r.events] == [("cycle", (2, 1, 0), 0, 2), ("path", (0, 3, 1), 2, 3), ("path", (2, 3), 1, 4)]
    assert r.events[1].fragment == A.Fragment((0, 1, 2), (3,)) and r.events[2].fragment == A.Fragment((2, 3), ())


def test_the_cycle_search_starts_at_the_smallest_vertex():
    adj = {0: {1, 3}, 1: {0, 2}, 2: {1, 3}, 3: {0, 2}}
    assert A.find_cycle(adj, {0, 1, 2, 3}) == [3, 2, 1, 0]


def _tampered(nodes, edges, faces):
    return A.BlockResult(tuple(nodes), tuple(edges), True, tuple(faces), (), 0)


def test_euler_ok_rejects_wrong_face_lists():
    k4 = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    good = [(0, 1, 2), (0, 2, 3), (0, 1, 3), (1, 2, 3)]
    assert A.euler_ok(_tampered(range(4), k4, good))
    # richtige Flächenzahl, aber eine Kante liegt auf drei Flächenseiten und eine auf einer: Euler stimmt, die Seitenprüfung nicht
    assert not A.euler_ok(_tampered(range(4), k4, [(0, 1, 2), (0, 1, 2), (0, 1, 3), (1, 2, 3)]))
    # Dreieck mit nur einer Fläche: Euler verletzt (3 − 3 + 1 ≠ 2); die Kurzfassung für kleine Blöcke darf hier nicht greifen
    assert not A.euler_ok(_tampered(range(3), [(0, 1), (0, 2), (1, 2)], [(0, 1, 2)]))
    assert A.euler_ok(_tampered(range(3), [(0, 1), (0, 2), (1, 2)], [(0, 1, 2), (0, 2, 1)]))


def test_a_segment_end_lying_on_the_other_segment_is_no_crossing():
    assert not A.segments_cross((0, 0), (2, 0), (1, -1), (1, 0))     # Ende der zweiten Strecke auf der ersten
    assert not A.segments_cross((1, -1), (1, 0), (0, 0), (2, 0))
    assert not A.segments_cross((0, 0), (2, 0), (1, 0), (1, 1))      # Anfang der zweiten Strecke auf der ersten


def test_fragments_are_listed_single_edges_first_then_components_by_smallest_vertex():
    """Quadrat 0-1-2-3 eingebettet; Diagonalen 0-2 und 1-3, dazu die Dächer 4 über 0, 1 und der Weg 5-6 zwischen 2 und 3: feste Reihenfolge, Tupel sortiert."""
    edges = [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2), (1, 3), (0, 4), (1, 4), (2, 5), (5, 6), (3, 6)]
    adj = A.adjacency(7, edges)
    frags, _ = A.fragments(adj, set(range(7)), {0, 1, 2, 3}, {(0, 1), (1, 2), (2, 3), (0, 3)})
    assert frags == [A.Fragment((0, 2), ()), A.Fragment((1, 3), ()), A.Fragment((0, 1), (4,)), A.Fragment((2, 3), (5, 6))]


def test_classify_witness_needs_both_the_branch_count_and_the_degrees():
    k5_minus = S.hand_graph("K5 minus eine Kante")                   # 5 Verzweigungsknoten, aber Grade 4, 4, 4, 3, 3: kein K5
    assert A.classify_witness(k5_minus.edges).kind == "?"
    k33 = S.hand_graph("K3,3")
    k33_chord = A.classify_witness(tuple(sorted(list(k33.edges) + [(0, 1)])))   # 6 Verzweigungsknoten, Grade 4, 4, 3, 3, 3, 3: kein K3,3
    assert k33_chord.kind == "?"


def test_verify_witness_names_each_defect_it_finds():
    k5 = S.hand_graph("K5")
    w = A.classify_witness(k5.edges)
    bad_end = A.Witness(w.kind, w.edges, w.branch, w.paths + ((0, 9),))                 # endet nicht in einem Verzweigungsknoten
    assert any("endet nicht in zwei verschiedenen Verzweigungsknoten" in p for p in A.verify_witness(k5.edges, bad_end))
    loop_path = A.Witness(w.kind, w.edges, w.branch, w.paths + ((1, 1),))                # Anfang gleich Ende
    assert any("endet nicht in zwei verschiedenen" in p for p in A.verify_witness(k5.edges, loop_path))
    missing_k5 = A.Witness("K5", w.edges, w.branch, w.paths[:-1])                       # ein Paar fehlt
    assert any("keine Unterteilung von K5" in p for p in A.verify_witness(k5.edges, missing_k5))
    k33 = S.hand_graph("K3,3")
    w33 = A.classify_witness(k33.edges)
    missing_k33 = A.Witness("K3,3", w33.edges, w33.branch, w33.paths[:-1])
    assert any("keine Unterteilung von K3,3" in p for p in A.verify_witness(k33.edges, missing_k33))
    wrong_sides = A.Witness("K3,3", w.edges, w.branch + (9,), w.paths)                  # sechs Knoten, aber K5 ist nicht bipartit
    assert any("keine Unterteilung von K3,3" in p for p in A.verify_witness(k5.edges, wrong_sides))


def test_single_edge_fragments_of_one_vertex_are_listed_by_their_other_end():
    """Fünfeck 0-1-2-3-4 eingebettet, Sehnen 0-2 und 0-3 am selben Knoten: erst 0-2, dann 0-3."""
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4), (0, 2), (0, 3)]
    adj = A.adjacency(5, edges)
    frags, _ = A.fragments(adj, set(range(5)), set(range(5)), {(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)})
    assert frags == [A.Fragment((0, 2), ()), A.Fragment((0, 3), ())]
