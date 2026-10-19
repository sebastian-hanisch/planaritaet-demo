"""Kern: Planarität per Fragmentverfahren (Demoucron–Malgrange–Pertuiset), Einbettung als Flächenliste, Kuratowski-Zeuge per Kantenabbau.

Eine Einheit ist eine Regel: Blöcke bestimmen, Kreis suchen, Fragmente bestimmen, zulässige Flächen, ein Fragment wählen, einen Weg suchen,
eine Fläche teilen, einen Zeugen verkleinern, einen Zeugen prüfen. Kein Zufall, keine Modul-Globals: Gleichstand entscheidet die kleinere
Knotennummer. Graphen sind einfach und ungerichtet; Knoten 0 bis n − 1, Kanten als sortierte Paare."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass


def adjacency(n: int, edges) -> list[set[int]]:
    adj: list[set[int]] = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    return adj


def components(n: int, adj) -> int:
    """Zahl der Zusammenhangskomponenten (isolierte Knoten zählen mit)."""
    seen = [False] * n
    count = 0
    for s in range(n):
        if seen[s]:
            continue
        count += 1
        seen[s] = True
        queue = deque([s])
        while queue:
            x = queue.popleft()
            for y in adj[x]:
                if not seen[y]:
                    seen[y] = True
                    queue.append(y)
    return count


def biconnected_blocks(n: int, adj) -> list[list[tuple[int, int]]]:
    """Blöcke (zweifach zusammenhängende Teile) als Kantenlisten; eine Brücke ist ein Block mit einer Kante. Ein Graph ist genau dann planar, wenn jeder Block es ist."""
    disc = [-1] * n
    low = [0] * n
    clock = 0
    edge_stack: list[tuple[int, int]] = []
    blocks: list[list[tuple[int, int]]] = []
    for root in range(n):
        if disc[root] != -1:
            continue
        disc[root] = low[root] = clock
        clock += 1
        stack = [(root, -1, iter(sorted(adj[root])))]
        while stack:
            v, parent, it = stack[-1]
            advanced = False
            for w in it:
                if w == parent:
                    continue
                if disc[w] == -1:
                    edge_stack.append((v, w))
                    disc[w] = low[w] = clock
                    clock += 1
                    stack.append((w, v, iter(sorted(adj[w]))))
                    advanced = True
                    break
                if disc[w] < disc[v]:
                    edge_stack.append((v, w))
                    low[v] = min(low[v], disc[w])
            if advanced:
                continue
            stack.pop()
            if stack:
                p = stack[-1][0]
                low[p] = min(low[p], low[v])
                if low[v] >= disc[p]:
                    block = []
                    while True:
                        e = edge_stack.pop()
                        block.append((min(e), max(e)))
                        if e == (p, v):
                            break
                    blocks.append(sorted(block))
    return blocks


def find_cycle(adj, nodes) -> list[int] | None:
    """Ein Kreis in einem zweifach zusammenhängenden Teil (Tiefensuche, kleinster Nachbar zuerst); None, wenn es keinen gibt."""
    start = min(nodes)
    parent = {start: None}
    depth = {start: 0}
    stack = [(start, iter(sorted(w for w in adj[start] if w in nodes)))]
    while stack:
        v, it = stack[-1]
        advanced = False
        for w in it:
            if w == parent[v]:
                continue
            if w in parent:
                if depth[w] < depth[v]:
                    cycle = [v]
                    x = v
                    while x != w:
                        x = parent[x]
                        cycle.append(x)
                    return cycle
                continue
            parent[w] = v
            depth[w] = depth[v] + 1
            stack.append((w, iter(sorted(y for y in adj[w] if y in nodes))))
            advanced = True
            break
        if not advanced:
            stack.pop()
    return None


@dataclass(frozen=True)
class Fragment:
    """Eine Brücke relativ zum bisher Eingebetteten: eine Kante zwischen zwei eingebetteten Knoten oder eine Komponente der übrigen Knoten samt Anschlusskanten."""

    attach: tuple[int, ...]       # eingebettete Knoten, mit denen das Fragment verbunden ist (sortiert)
    interior: tuple[int, ...]     # noch nicht eingebettete Knoten des Fragments (sortiert, leer bei einer einzelnen Kante)


def fragments(adj, nodes, embedded: set[int], embedded_edges: set[tuple[int, int]]) -> tuple[list[Fragment], int]:
    """Alle Fragmente und die Zahl der dafür besuchten Nachbarn (Schritte). Einzelkanten zuerst, dann Komponenten nach kleinster Knotennummer."""
    steps = 0
    found: list[Fragment] = []
    for u in sorted(embedded):
        for v in sorted(adj[u]):
            if v > u and v in embedded and (u, v) not in embedded_edges:
                found.append(Fragment((u, v), ()))
    seen: set[int] = set()
    for s in sorted(nodes):
        if s in embedded or s in seen:
            continue
        comp = {s}
        attach: set[int] = set()
        queue = deque([s])
        while queue:
            x = queue.popleft()
            for y in sorted(adj[x]):
                if y not in nodes:
                    continue
                steps += 1
                if y in embedded:
                    attach.add(y)
                elif y not in comp:
                    comp.add(y)
                    queue.append(y)
        seen |= comp
        found.append(Fragment(tuple(sorted(attach)), tuple(sorted(comp))))
    return found, steps


def admissible_faces(fragment: Fragment, face_sets: list[set[int]]) -> list[int]:
    """Nummern der Flächen, die alle Anschlussknoten des Fragments enthalten (nur dort kann es eingezeichnet werden)."""
    need = set(fragment.attach)
    return [i for i, members in enumerate(face_sets) if need <= members]


def choose_fragment(options: list[tuple[Fragment, list[int]]]) -> int:
    """Index des Fragments mit den wenigsten zulässigen Flächen (das erste bei Gleichstand): hat eines nur eine, muss es dorthin."""
    best = 0
    for i, (_, adm) in enumerate(options):
        if len(adm) < len(options[best][1]):
            best = i
    return best


def path_in_fragment(adj, nodes, fragment: Fragment) -> list[int]:
    """Ein kürzester Weg zwischen zwei verschiedenen Anschlussknoten durch das Fragment (bei einer Einzelkante: die Kante)."""
    a = fragment.attach[0]
    if not fragment.interior:
        return [a, fragment.attach[1]]
    inside = set(fragment.interior)
    attach = set(fragment.attach)
    prev: dict[int, int | None] = {a: None}
    queue = deque([a])
    end = None
    while queue and end is None:
        x = queue.popleft()
        for y in sorted(adj[x]):
            if y not in nodes or y in prev:
                continue
            if y in inside:
                prev[y] = x
                queue.append(y)
            elif y in attach and y != a and x in inside:
                prev[y] = x
                end = y
                break
    path = [end]
    while path[-1] != a:
        path.append(prev[path[-1]])
    path.reverse()
    return path


def split_face(face: list[int], path: list[int]) -> tuple[list[int], list[int]]:
    """Teilt die Fläche (zyklische Knotenfolge) durch den Weg zwischen zwei ihrer Knoten in zwei Flächen."""
    a, b = path[0], path[-1]
    interior = path[1:-1]
    k = len(face)
    i, j = face.index(a), face.index(b)
    first = [face[(i + t) % k] for t in range(((j - i) % k) + 1)]    # von a bis b
    second = [face[(j + t) % k] for t in range(((i - j) % k) + 1)]   # von b bis a
    return first + interior[::-1], second + interior


@dataclass(frozen=True)
class Event:
    """Ein Schritt des Fragmenttests, zum Abspielen: der Anfangskreis oder ein eingefügter Weg (kind = 'cycle'/'path') bzw. das Scheitern ('fail')."""

    kind: str
    path: tuple[int, ...]
    fragment: Fragment | None = None
    fragments: int = 0            # Zahl der Fragmente in diesem Schritt
    admissible: int = 0           # zulässige Flächen des gewählten Fragments (0 bei 'fail')
    faces: int = 2                # Flächenzahl NACH dem Schritt


@dataclass(frozen=True)
class BlockResult:
    nodes: tuple[int, ...]
    edges: tuple[tuple[int, int], ...]
    planar: bool
    faces: tuple[tuple[int, ...], ...]     # nur bei planar und mindestens drei Knoten
    events: tuple[Event, ...]
    steps: int


def embed_block(edges) -> BlockResult:
    """Fragmenttest für einen zweifach zusammenhängenden Block: Einbettung (Flächenliste) oder Scheitern mit dem Fragment ohne zulässige Fläche."""
    edges = tuple(sorted((min(u, v), max(u, v)) for u, v in edges))
    nodes = sorted({x for e in edges for x in e})
    if len(nodes) <= 2:
        return BlockResult(tuple(nodes), edges, True, (), (), 0)
    adj: dict[int, set[int]] = {x: set() for x in nodes}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    node_set = set(nodes)
    cycle = find_cycle(adj, node_set)
    faces = [list(cycle), list(cycle[::-1])]
    face_sets = [set(cycle), set(cycle)]
    embedded = set(cycle)
    embedded_edges = {(min(cycle[i], cycle[(i + 1) % len(cycle)]), max(cycle[i], cycle[(i + 1) % len(cycle)])) for i in range(len(cycle))}
    events = [Event("cycle", tuple(cycle), None, 0, 0, 2)]
    steps = 0
    all_edges = set(edges)
    while len(embedded_edges) < len(all_edges):
        frags, s = fragments(adj, node_set, embedded, embedded_edges)
        steps += s
        options = []
        for frag in frags:
            adm = admissible_faces(frag, face_sets)
            steps += len(face_sets)
            if not adm:
                events.append(Event("fail", (), frag, len(frags), 0, len(faces)))
                return BlockResult(tuple(nodes), edges, False, (), tuple(events), steps)
            options.append((frag, adm))
        frag, adm = options[choose_fragment(options)]
        path = path_in_fragment(adj, node_set, frag)
        fi = adm[0]
        f1, f2 = split_face(faces[fi], path)
        faces[fi], face_sets[fi] = f1, set(f1)
        faces.append(f2)
        face_sets.append(set(f2))
        embedded |= set(path)
        embedded_edges |= {(min(path[i], path[i + 1]), max(path[i], path[i + 1])) for i in range(len(path) - 1)}
        events.append(Event("path", tuple(path), frag, len(frags), len(adm), len(faces)))
    return BlockResult(tuple(nodes), edges, True, tuple(tuple(f) for f in faces), tuple(events), steps)


@dataclass(frozen=True)
class Embedding:
    """Ergebnis für den ganzen Graphen: ein Block-Ergebnis je Block, die Flächenzahl nach Euler und die Gesamtzahl der Schritte."""

    n: int
    m: int
    components: int
    blocks: tuple[BlockResult, ...]
    planar: bool
    failed_block: int | None      # Index des ersten nichtplanaren Blocks
    steps: int

    @property
    def faces(self) -> int | None:
        """Flächenzahl des ganzen Graphen nach der Euler-Formel (bei planaren Graphen): m − n + 1 + Komponenten."""
        return euler_faces(self.n, self.m, self.components) if self.planar else None


def euler_faces(n: int, m: int, components_count: int) -> int:
    """Euler-Formel für planare Graphen mit c Komponenten: n − m + f = 1 + c."""
    return m - n + 1 + components_count


def euler_ok(block: BlockResult) -> bool:
    """Prüft für einen planar eingebetteten Block die Euler-Formel (n_b − m_b + f_b = 2) und dass jede Kante auf genau zwei Flächenseiten liegt."""
    if len(block.nodes) <= 2:
        return True
    if len(block.nodes) - len(block.edges) + len(block.faces) != 2:
        return False
    sides: dict[tuple[int, int], int] = {}
    for face in block.faces:
        for i in range(len(face)):
            e = (min(face[i], face[(i + 1) % len(face)]), max(face[i], face[(i + 1) % len(face)]))
            sides[e] = sides.get(e, 0) + 1
    return set(sides) == set(block.edges) and all(c == 2 for c in sides.values())


def embed(n: int, edges) -> Embedding:
    """Fragmenttest für den ganzen Graphen: alle Blöcke, in der Reihenfolge der Tiefensuche; bricht beim ersten nichtplanaren Block nicht ab (Schritte zählen mit)."""
    adj = adjacency(n, edges)
    results = [embed_block(b) for b in biconnected_blocks(n, adj)]
    failed = next((i for i, r in enumerate(results) if not r.planar), None)
    return Embedding(n, len({(min(u, v), max(u, v)) for u, v in edges}), components(n, adj), tuple(results), failed is None, failed, sum(r.steps for r in results))


def is_planar_edges(edges) -> bool:
    """Planarität einer Kantenliste (Knoten beliebige nichtnegative Zahlen); bricht beim ersten nichtplanaren Block ab."""
    labels = sorted({x for e in edges for x in e})
    index = {x: i for i, x in enumerate(labels)}
    relabeled = [(index[u], index[v]) for u, v in edges]
    adj = adjacency(len(labels), relabeled)
    return all(embed_block(b).planar for b in biconnected_blocks(len(labels), adj))


# --- Zeuge ----------------------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Witness:
    """Unterteilung von K5 oder K3,3: kantenminimaler nichtplanarer Teilgraph, seine Verzweigungsknoten und die Wege dazwischen."""

    kind: str                                   # "K5", "K3,3" oder "?"
    edges: tuple[tuple[int, int], ...]
    branch: tuple[int, ...]                     # Knoten vom Grad ≥ 3 im Zeugen
    paths: tuple[tuple[int, ...], ...]          # Wege zwischen Verzweigungsknoten (Endpunkte Verzweigungsknoten, innen Knoten vom Grad 2)
    tests: int = 0                              # Zahl der Planaritätstests beim Abbau


def witness_by_deletion(edges, planar_test=is_planar_edges) -> tuple[tuple[tuple[int, int], ...], int]:
    """Kantenabbau: jede Kante probeweise streichen, bleibt der Rest nichtplanar, bleibt sie gestrichen. Ergebnis: kantenminimaler nichtplanarer Teilgraph und Testzahl."""
    current = sorted((min(u, v), max(u, v)) for u, v in edges)
    tests = 0
    for e in list(current):
        trial = [x for x in current if x != e]
        tests += 1
        if not planar_test(trial):
            current = trial
    return tuple(current), tests


def classify_witness(edges, tests: int = 0) -> Witness:
    """Art (K5/K3,3), Verzweigungsknoten und Wege eines kantenminimalen nichtplanaren Graphen."""
    adj: dict[int, set[int]] = {}
    for u, v in edges:
        adj.setdefault(u, set()).add(v)
        adj.setdefault(v, set()).add(u)
    branch = tuple(sorted(x for x in adj if len(adj[x]) >= 3))
    paths: set[tuple[int, ...]] = set()
    for b in branch:
        for w in sorted(adj[b]):
            walk = [b, w]
            while walk[-1] not in branch:
                nxt = [y for y in sorted(adj[walk[-1]]) if y != walk[-2]]
                walk.append(nxt[0])
            if walk[0] > walk[-1]:
                walk.reverse()
            paths.add(tuple(walk))
    degrees = sorted(len(adj[b]) for b in branch)
    if len(branch) == 5 and degrees == [4] * 5:
        kind = "K5"
    elif len(branch) == 6 and degrees == [3] * 6:
        kind = "K3,3"
    else:
        kind = "?"
    return Witness(kind, tuple(sorted((min(u, v), max(u, v)) for u, v in edges)), branch, tuple(sorted(paths)), tests)


def verify_witness(graph_edges, witness: Witness) -> list[str]:
    """Unabhängige Prüfung eines Zeugen ohne Planaritätstest: Liste der Verstöße (leer = Zeuge in Ordnung).

    Prüft: Kanten stammen aus dem Graphen; Wege laufen nur über Knoten vom Grad 2; jede Zeugenkante liegt auf genau einem Weg; die Verzweigungsknoten
    sind durch die Wege wie die Ecken von K5 (alle zehn Paare) bzw. K3,3 (alle neun Paare zwischen zwei Dreiergruppen) verbunden."""
    problems: list[str] = []
    graph = {(min(u, v), max(u, v)) for u, v in graph_edges}
    wedges = set(witness.edges)
    if not wedges <= graph:
        problems.append("Zeugenkante nicht im Graphen")
    deg: dict[int, int] = {}
    for u, v in wedges:
        deg[u] = deg.get(u, 0) + 1
        deg[v] = deg.get(v, 0) + 1
    branch = set(witness.branch)
    if branch != {x for x, d in deg.items() if d >= 3}:
        problems.append("Verzweigungsknoten passen nicht zu den Graden")
    covered: dict[tuple[int, int], int] = {}
    pairs: dict[tuple[int, int], int] = {}
    for path in witness.paths:
        if path[0] not in branch or path[-1] not in branch or path[0] == path[-1]:
            problems.append(f"Weg {path} endet nicht in zwei verschiedenen Verzweigungsknoten")
            continue
        if any(x in branch or deg.get(x, 0) != 2 for x in path[1:-1]):
            problems.append(f"Weg {path} läuft über einen Knoten, der nicht Grad 2 hat")
        for i in range(len(path) - 1):
            e = (min(path[i], path[i + 1]), max(path[i], path[i + 1]))
            covered[e] = covered.get(e, 0) + 1
        key = (path[0], path[-1])
        pairs[key] = pairs.get(key, 0) + 1
    if set(covered) != wedges or any(c != 1 for c in covered.values()):
        problems.append("Zeugenkanten liegen nicht auf genau einem Weg")
    if any(c != 1 for c in pairs.values()):
        problems.append("zwei Wege verbinden dasselbe Paar von Verzweigungsknoten")
    pair_set = set(pairs)
    if witness.kind == "K5":
        need = {(a, b) for a in witness.branch for b in witness.branch if a < b}
        if len(branch) != 5 or pair_set != need:
            problems.append("keine Unterteilung von K5")
    elif witness.kind == "K3,3":
        side = _bipartition(sorted(branch), pair_set)
        if len(branch) != 6 or side is None or sorted(side.values()).count(0) != 3 or len(pair_set) != 9:
            problems.append("keine Unterteilung von K3,3")
    else:
        problems.append("weder K5 noch K3,3")
    return problems


def _bipartition(nodes, pair_set) -> dict[int, int] | None:
    """Zweifärbung des Graphen auf den Verzweigungsknoten; None, wenn er nicht bipartit ist."""
    adj: dict[int, list[int]] = {x: [] for x in nodes}
    for a, b in pair_set:
        adj[a].append(b)
        adj[b].append(a)
    side: dict[int, int] = {}
    for s in nodes:
        if s in side:
            continue
        side[s] = 0
        queue = deque([s])
        while queue:
            x = queue.popleft()
            for y in adj[x]:
                if y not in side:
                    side[y] = 1 - side[x]
                    queue.append(y)
                elif side[y] == side[x]:
                    return None
    return side


def witness_for(embedding: Embedding, max_edges: int = 400) -> Witness | None:
    """Zeuge für einen nichtplanaren Graphen: Kantenabbau im ersten nichtplanaren Block (höchstens `max_edges` Kanten); None bei planar oder zu großem Block."""
    if embedding.failed_block is None:
        return None
    block = embedding.blocks[embedding.failed_block]
    if len(block.edges) > max_edges:
        return None
    reduced, tests = witness_by_deletion(block.edges)
    return classify_witness(reduced, tests)


# --- Zeichnung und Kreuzungen ---------------------------------------------------------------------------------------------------------------


def segments_cross(p1, p2, q1, q2) -> bool:
    """Schneiden sich die Strecken p1p2 und q1q2 im Inneren beider Strecken (gemeinsame Endpunkte und Überlagerungen zählen nicht)?"""
    rx, ry = p2[0] - p1[0], p2[1] - p1[1]
    sx, sy = q2[0] - q1[0], q2[1] - q1[1]
    denom = rx * sy - ry * sx
    if denom == 0:
        return False
    qpx, qpy = q1[0] - p1[0], q1[1] - p1[1]
    t = (qpx * sy - qpy * sx) / denom
    s = (qpx * ry - qpy * rx) / denom
    return 1e-9 < t < 1 - 1e-9 and 1e-9 < s < 1 - 1e-9


def crossings(pos, edges, cell: float | None = None) -> list[tuple[int, int]]:
    """Paare (i, j), i < j, von Kantenindizes, deren Strecken sich kreuzen (ohne gemeinsamen Endpunkt). Mit `cell` wird ein Raster zur Vorauswahl benutzt."""
    found = []
    if cell is None:
        for i in range(len(edges)):
            a, b = edges[i]
            for j in range(i + 1, len(edges)):
                c, d = edges[j]
                if len({a, b, c, d}) == 4 and segments_cross(pos[a], pos[b], pos[c], pos[d]):
                    found.append((i, j))
        return found
    buckets: dict[tuple[int, int], list[int]] = {}
    for i, (a, b) in enumerate(edges):
        x0, x1 = sorted((pos[a][0], pos[b][0]))
        y0, y1 = sorted((pos[a][1], pos[b][1]))
        for cx in range(int(x0 // cell), int(x1 // cell) + 1):
            for cy in range(int(y0 // cell), int(y1 // cell) + 1):
                buckets.setdefault((cx, cy), []).append(i)
    seen: set[tuple[int, int]] = set()
    for members in buckets.values():
        for ii in range(len(members)):
            i = members[ii]
            a, b = edges[i]
            for jj in range(ii + 1, len(members)):
                j = members[jj]
                if (i, j) in seen:
                    continue
                seen.add((i, j))
                c, d = edges[j]
                if len({a, b, c, d}) == 4 and segments_cross(pos[a], pos[b], pos[c], pos[d]):
                    found.append((i, j))
    return sorted(found)


def greedy_cover(pairs) -> list[int]:
    """Kantenindizes, die alle Kreuzungen berühren: wiederholt die Kante an den meisten noch offenen Kreuzungen streichen (Gleichstand: kleinster Index)."""
    open_pairs = {tuple(p) for p in pairs}
    chosen = []
    while open_pairs:
        count: dict[int, int] = {}
        for i, j in open_pairs:
            count[i] = count.get(i, 0) + 1
            count[j] = count.get(j, 0) + 1
        best = min(count, key=lambda x: (-count[x], x))
        chosen.append(best)
        open_pairs = {p for p in open_pairs if best not in p}
    return chosen
