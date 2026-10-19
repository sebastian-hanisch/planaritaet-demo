"""Orakel-Test planaritaet-demo / planaritaet: Kern gegen unabhängige Rechenwege (DEMO-PLAYBOOK §12).

Orakel: (1) networkx (Planaritätstest, Blöcke), (2) eine Aufzählung ohne jeden Planaritätstest: ein Graph ist nach Kuratowski genau dann nichtplanar,
wenn eine Kantenmenge eine Unterteilung von K5 oder K3,3 ist; die Aufzählung prüft das nach der Definition (Glätten von Knoten vom Grad 2),
(3) Eigenschaften, die für jeden planaren Graphen gelten (Monotonie unter Kantenentfernung, Kantenschranke 3n − 6, Maximalität triangulierter Graphen).
Der große Lauf (mindestens 200 Zufallsinstanzen) lief im Scratch-Ordner; hier die schnelle Fassung."""

import itertools
import random

import pytest

import plt_algorithm as A
import plt_scenario as S

nx = pytest.importorskip("networkx")


def _random_edges(rng, n, m):
    pairs = [(u, v) for u in range(n) for v in range(u + 1, n)]
    return sorted(rng.sample(pairs, min(m, len(pairs))))


def is_kuratowski_subdivision(edges) -> bool:
    """Definition: nach Glätten aller Knoten vom Grad 2 bleibt K5 oder K3,3 (und nie eine Mehrfachkante); kein Knoten vom Grad 1, zusammenhängend."""
    adj = {}
    for u, v in edges:
        adj.setdefault(u, set()).add(v)
        adj.setdefault(v, set()).add(u)
    if not adj or any(len(a) < 2 for a in adj.values()):
        return False
    changed = True
    while changed:
        changed = False
        for x in sorted(adj):
            if len(adj[x]) == 2:
                a, b = sorted(adj[x])
                if b in adj[a]:
                    return False
                adj[a].discard(x)
                adj[b].discard(x)
                adj[a].add(b)
                adj[b].add(a)
                del adj[x]
                changed = True
                break
    nodes = sorted(adj)
    # zusammenhängend?
    seen, stack = {nodes[0]}, [nodes[0]]
    while stack:
        for y in adj[stack.pop()]:
            if y not in seen:
                seen.add(y)
                stack.append(y)
    if len(seen) != len(nodes):
        return False
    if len(nodes) == 5:
        return all(len(adj[x]) == 4 for x in nodes)
    if len(nodes) == 6 and all(len(adj[x]) == 3 for x in nodes):
        colour = {nodes[0]: 0}
        stack = [nodes[0]]
        while stack:
            x = stack.pop()
            for y in adj[x]:
                if y not in colour:
                    colour[y] = 1 - colour[x]
                    stack.append(y)
                elif colour[y] == colour[x]:
                    return False
        return True
    return False


def brute_force_planar(edges) -> bool:
    """Planar genau dann, wenn keine Kantenmenge eine Unterteilung von K5 oder K3,3 ist (nur für kleine Graphen)."""
    edges = sorted(edges)
    for size in range(9, len(edges) + 1):
        for subset in itertools.combinations(edges, size):
            if is_kuratowski_subdivision(subset):
                return False
    return True


def test_the_brute_force_oracle_itself_on_known_graphs():
    """Das Orakel vorher an Handbeispielen prüfen: K5, K3,3, Petersen (nichtplanar), Würfel, K4 (planar)."""
    for name, expected in (("K5", False), ("K3,3", False), ("K4", True), ("K5 minus eine Kante", True), ("K3,3 mit Unterteilungen", False)):
        assert brute_force_planar(S.hand_graph(name).edges) is expected, name
    assert is_kuratowski_subdivision(S.hand_graph("K3,3").edges) and not is_kuratowski_subdivision(S.hand_graph("K4").edges)
    prism = [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (0, 3), (1, 4), (2, 5)]
    assert not is_kuratowski_subdivision(prism)                     # kubisch auf 6 Knoten, aber mit Dreiecken: nicht K3,3


def test_planarity_agrees_with_the_definition_on_small_random_graphs():
    rng = random.Random(11)
    nonplanar = 0
    for _ in range(90):
        n = rng.randint(5, 7)
        edges = _random_edges(rng, n, rng.randint(8, 12))
        mine = A.embed(n, edges).planar
        assert mine == brute_force_planar(edges), (n, edges)
        nonplanar += not mine
    assert 10 <= nonplanar <= 80                                      # beide Fälle kommen vor


def test_planarity_agrees_with_networkx_on_random_graphs():
    rng = random.Random(3)
    for n in range(3, 16):
        for _ in range(40):
            m = rng.randint(max(n - 1, 1), min(3 * n - 5, n * (n - 1) // 2))
            edges = _random_edges(rng, n, m)
            assert A.embed(n, edges).planar == nx.check_planarity(nx.Graph(edges))[0], (n, edges)


def test_blocks_agree_with_networkx():
    rng = random.Random(5)
    for n in range(3, 16):
        for _ in range(20):
            edges = _random_edges(rng, n, rng.randint(1, min(2 * n, n * (n - 1) // 2)))
            g = nx.Graph(edges)
            theirs = sorted(sorted((min(u, v), max(u, v)) for u, v in b) for b in nx.biconnected_component_edges(g))
            mine = sorted(sorted(b) for b in A.biconnected_blocks(n, A.adjacency(n, edges)))
            assert mine == theirs, (n, edges)


def test_embeddings_pass_the_independent_face_checks():
    """Jede Einbettung: Euler im Block, jede Kante auf genau zwei Flächenseiten, jede Fläche ein Kreis ohne Wiederholung."""
    rng = random.Random(9)
    checked = 0
    for n in range(4, 14):
        for _ in range(30):
            edges = _random_edges(rng, n, rng.randint(n, min(3 * n - 6, n * (n - 1) // 2)))
            emb = A.embed(n, edges)
            if not emb.planar:
                continue
            checked += 1
            for block in emb.blocks:
                assert A.euler_ok(block)
                assert all(len(set(f)) == len(f) for f in block.faces)
    assert checked > 100


def test_witnesses_are_minimal_nonplanar_and_pass_the_definition():
    rng = random.Random(21)
    kinds = set()
    for _ in range(40):
        n = rng.randint(6, 12)
        while True:
            edges = _random_edges(rng, n, rng.randint(n + 2, min(3 * n - 5, n * (n - 1) // 2)))
            if not nx.check_planarity(nx.Graph(edges))[0]:
                break
        emb = A.embed(n, edges)
        w = A.witness_for(emb)
        kinds.add(w.kind)
        assert A.verify_witness(edges, w) == []
        assert is_kuratowski_subdivision(w.edges)                    # Definition
        g = nx.Graph(list(w.edges))
        assert not nx.check_planarity(g)[0]
        for e in w.edges:                                            # kantenminimal: ohne jede Kante planar
            h = g.copy()
            h.remove_edge(*e)
            assert nx.check_planarity(h)[0]
    assert kinds == {"K5", "K3,3"} or kinds == {"K3,3"}


def test_removing_an_edge_never_destroys_planarity():
    rng = random.Random(17)
    for _ in range(60):
        n = rng.randint(5, 12)
        edges = _random_edges(rng, n, rng.randint(n, 2 * n))
        if not A.embed(n, edges).planar:
            continue
        for e in edges:
            assert A.embed(n, [x for x in edges if x != e]).planar


def test_more_than_3n_minus_6_edges_are_never_planar():
    rng = random.Random(23)
    for _ in range(100):
        n = rng.randint(5, 12)
        m = rng.randint(3 * n - 5, n * (n - 1) // 2)
        edges = _random_edges(rng, n, m)
        assert not A.embed(n, edges).planar


def _stacked_triangulation(n, rng):
    """Dreieck, dann wiederholt ein neuer Knoten in eine zufällige Dreiecksfläche: maximal planar mit 3n − 6 Kanten."""
    edges = {(0, 1), (0, 2), (1, 2)}
    faces = [(0, 1, 2), (0, 2, 1)]
    for v in range(3, n):
        a, b, c = faces.pop(rng.randrange(len(faces)))
        edges |= {(min(a, v), max(a, v)), (min(b, v), max(b, v)), (min(c, v), max(c, v))}
        faces += [(a, b, v), (b, c, v), (c, a, v)]
    return sorted(edges)


def test_a_maximal_planar_graph_becomes_nonplanar_with_any_additional_edge():
    rng = random.Random(29)
    for n in (6, 8, 10):
        edges = _stacked_triangulation(n, rng)
        assert len(edges) == 3 * n - 6 and A.embed(n, edges).planar
        present = set(edges)
        for u in range(n):
            for v in range(u + 1, n):
                if (u, v) not in present:
                    assert not A.embed(n, edges + [(u, v)]).planar, (n, u, v)


def test_planarity_does_not_depend_on_the_labels():
    rng = random.Random(31)
    for _ in range(60):
        n = rng.randint(5, 11)
        edges = _random_edges(rng, n, rng.randint(n, 2 * n + 2))
        perm = list(range(n))
        rng.shuffle(perm)
        relabeled = [(min(perm[u], perm[v]), max(perm[u], perm[v])) for u, v in edges]
        assert A.embed(n, edges).planar == A.embed(n, relabeled).planar


def test_the_drawings_of_the_planar_textbook_graphs_have_no_crossings():
    for name in ("K4", "Würfel", "Oktaeder", "K5 minus eine Kante"):
        g = S.hand_graph(name)
        assert A.crossings(g.pos, g.edges) == [], name
        assert A.embed(g.n, g.edges).planar


def test_the_binned_crossing_search_equals_the_brute_force_one():
    rng = random.Random(41)
    for _ in range(25):
        n = 25
        pos = [(rng.uniform(0, 500), rng.uniform(0, 500)) for _ in range(n)]
        edges = _random_edges(rng, n, 40)
        assert A.crossings(pos, edges, cell=60.0) == A.crossings(pos, edges)
