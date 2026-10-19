"""Plotly-Figuren: Graph mit Hervorhebungen, Abspielen des Fragmenttests, Zeuge, Messreihen und Toronto-Karte. Alle Achsen fest (fixedrange)."""

from __future__ import annotations

import plotly.graph_objects as go

import plt_constants as C


def _edge_trace(pos, edges, color, width, name=None, dash=None, showlegend=False):
    """Alle Kanten einer Farbe als eine Spur (Linienstücke durch None getrennt)."""
    xs, ys = [], []
    for u, v in edges:
        xs += [pos[u][0], pos[v][0], None]
        ys += [pos[u][1], pos[v][1], None]
    return go.Scatter(
        x=xs, y=ys, mode="lines", line=dict(color=color, width=width, dash=dash), hoverinfo="skip", name=name or "", showlegend=showlegend and bool(edges)
    )


def _node_trace(pos, nodes, color, size, labels=True, name=None, showlegend=False, text_color="white"):
    nodes = list(nodes)
    return go.Scatter(
        x=[pos[v][0] for v in nodes],
        y=[pos[v][1] for v in nodes],
        mode="markers+text" if labels else "markers",
        marker=dict(color=color, size=size, line=dict(color="white", width=1)),
        text=[str(v) for v in nodes] if labels else None,
        textfont=dict(color=text_color, size=max(8, size - 10)),
        textposition="middle center",
        hovertext=[f"Knoten {v}" for v in nodes],
        hoverinfo="text",
        name=name or "",
        showlegend=showlegend and bool(nodes),
    )


def _layout(fig, title=None, height=420, equal=True, legend=True):
    fig.update_layout(
        title=dict(text=title, x=0, font=dict(size=14)) if title else None,
        height=height,
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        showlegend=legend,
        legend=dict(orientation="h", y=-0.02, x=0),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(visible=False, fixedrange=True)
    fig.update_yaxes(visible=False, fixedrange=True, **(dict(scaleanchor="x", scaleratio=1) if equal else {}))
    return fig


def build_graph(inst, title=None, height=420, highlight_edges=(), highlight_nodes=()):
    """Der Graph in seiner Lage; optional Kanten und Knoten hervorgehoben (z. B. die Fläche oder der Zeuge)."""
    fig = go.Figure()
    marked = set(highlight_edges)
    fig.add_trace(_edge_trace(inst.pos, [e for e in inst.edges if e not in marked], C.COLOR_EDGE, 2))
    if marked:
        fig.add_trace(_edge_trace(inst.pos, sorted(marked), C.COLOR_PATH, 4))
    plain = [v for v in range(inst.n) if v not in set(highlight_nodes)]
    fig.add_trace(_node_trace(inst.pos, plain, C.COLOR_WAIT, 22 if inst.n <= 40 else 14, labels=inst.n <= 40))
    if highlight_nodes:
        fig.add_trace(_node_trace(inst.pos, sorted(highlight_nodes), C.COLOR_PATH, 24 if inst.n <= 40 else 16, labels=inst.n <= 40))
    return _layout(fig, title, height, legend=False)


def playback_state(block, step: int) -> dict:
    """Zustand des Fragmenttests nach `step` Ereignissen (0 = noch nichts): eingebettete Kanten und Knoten, der letzte Weg, das gewählte Fragment."""
    events = block.events[: max(0, step)]
    embedded_edges: set[tuple[int, int]] = set()
    embedded_nodes: set[int] = set()
    last_path: tuple[int, ...] = ()
    fragment = None
    failed = False
    for ev in events:
        if ev.kind == "fail":
            failed = True
            fragment = ev.fragment
            continue
        path = ev.path + ((ev.path[0],) if ev.kind == "cycle" else ())
        for i in range(len(path) - 1):
            embedded_edges.add((min(path[i], path[i + 1]), max(path[i], path[i + 1])))
        embedded_nodes |= set(ev.path)
        last_path = path
        fragment = ev.fragment
    return {"edges": embedded_edges, "nodes": embedded_nodes, "path": last_path, "fragment": fragment, "failed": failed}


def fragment_edges(block_edges, fragment) -> list[tuple[int, int]]:
    """Kanten des Fragments: Anschlusskanten und Kanten im Inneren (bei einer Einzelkante diese Kante)."""
    if fragment is None:
        return []
    if not fragment.interior:
        return [(fragment.attach[0], fragment.attach[1])]
    inside = set(fragment.interior)
    return [e for e in block_edges if e[0] in inside or e[1] in inside]


def build_playback(inst, block, step: int, title=None, height=440):
    """Der Graph nach `step` Schritten des Fragmenttests: eingebettet (grün), zuletzt eingefügter Weg (rot), gewähltes Fragment (orange), Rest (grau)."""
    state = playback_state(block, step)
    block_edges = set(block.edges)
    fig = go.Figure()
    outside = [e for e in inst.edges if e not in block_edges]
    todo = [e for e in block.edges if e not in state["edges"]]
    frag_edges = [e for e in fragment_edges(block.edges, state["fragment"]) if e not in state["edges"]]
    frag_set = set(frag_edges)
    todo = [e for e in todo if e not in frag_set]
    fig.add_trace(_edge_trace(inst.pos, outside, "rgba(150,150,150,0.2)", 1.5))
    fig.add_trace(_edge_trace(inst.pos, todo, C.COLOR_EDGE, 2, "noch nicht eingebettet", showlegend=True))
    bad = state["failed"]
    fig.add_trace(_edge_trace(inst.pos, frag_edges, C.COLOR_BAD if bad else C.COLOR_FRAGMENT, 4, "Fragment ohne zulässige Fläche" if bad else "gewähltes Fragment", showlegend=True))
    path_edges = {(min(a, b), max(a, b)) for a, b in zip(state["path"], state["path"][1:])}
    fig.add_trace(_edge_trace(inst.pos, sorted(state["edges"] - path_edges), C.COLOR_BASE, 4, "eingebettet", showlegend=True))
    fig.add_trace(_edge_trace(inst.pos, sorted(path_edges), C.COLOR_PATH, 6, "zuletzt eingefügter Weg", showlegend=True))
    frag_nodes = set(state["fragment"].interior) | set(state["fragment"].attach) if state["fragment"] else set()
    plain = [v for v in range(inst.n) if v not in state["nodes"] and v not in frag_nodes]
    size = 22 if inst.n <= 40 else 14
    labels = inst.n <= 40
    fig.add_trace(_node_trace(inst.pos, plain, C.COLOR_WAIT, size, labels))
    fig.add_trace(_node_trace(inst.pos, sorted(frag_nodes - state["nodes"]), C.COLOR_BAD if bad else C.COLOR_FRAGMENT, size, labels))
    fig.add_trace(_node_trace(inst.pos, sorted(state["nodes"]), C.COLOR_BASE, size, labels))
    return _layout(fig, title, height)


def build_witness(inst, witness, title=None, height=420):
    """Der Zeuge: die Wege zwischen den Verzweigungsknoten je in eigener Farbe, alle übrigen Kanten grau."""
    fig = go.Figure()
    wset = set(witness.edges)
    fig.add_trace(_edge_trace(inst.pos, [e for e in inst.edges if e not in wset], "rgba(150,150,150,0.25)", 1.5))
    for i, path in enumerate(witness.paths):
        edges = [(min(a, b), max(a, b)) for a, b in zip(path, path[1:])]
        fig.add_trace(_edge_trace(inst.pos, edges, C.COLOR_PALETTE[i % len(C.COLOR_PALETTE)], 4))
    branch = set(witness.branch)
    inner = sorted({x for p in witness.paths for x in p[1:-1]})
    other = [v for v in range(inst.n) if v not in branch and v not in set(inner)]
    size = 22 if inst.n <= 40 else 14
    fig.add_trace(_node_trace(inst.pos, other, C.COLOR_WAIT, size - 4 if inst.n <= 40 else 8, labels=inst.n <= 40))
    fig.add_trace(_node_trace(inst.pos, inner, "#555555", size - 6 if inst.n <= 40 else 8, labels=False))
    fig.add_trace(_node_trace(inst.pos, sorted(branch), C.COLOR_PATH, size + 6 if inst.n <= 40 else 18, labels=inst.n <= 40))
    return _layout(fig, title, height, legend=False)


def build_share(rows, title="Anteil planarer Graphen"):
    """Anteil planarer Zufallsverbindungen über der Dichte (je Knotenzahl eine Linie)."""
    fig = go.Figure()
    for i, n in enumerate(sorted({r["n"] for r in rows})):
        sub = sorted((r for r in rows if r["n"] == n), key=lambda r: r["density"])
        fig.add_trace(
            go.Scatter(
                x=[r["density"] for r in sub],
                y=[r["share"] * 100 for r in sub],
                mode="lines+markers",
                name=f"n = {n}",
                line=dict(color=C.COLOR_PALETTE[i % len(C.COLOR_PALETTE)], width=3),
                hovertemplate="Dichte %{x} %: %{y:.0f} % planar<extra>n = " + str(n) + "</extra>",
            )
        )
    fig.add_vline(x=100, line=dict(color="#888", dash="dot"), annotation_text="Euler-Schranke 3n − 6", annotation_position="top left")
    fig.update_layout(title=dict(text=title, x=0, font=dict(size=14)), height=360, margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.2, x=0))
    fig.update_xaxes(title="Dichte (% von 3n − 6 Kanten)", fixedrange=True, range=[0, 105])
    fig.update_yaxes(title="planar (%)", fixedrange=True, range=[-3, 103])
    return fig


def build_plus(rows, title="Anteil nichtplanarer Graphen nach k Zusatzkanten"):
    fig = go.Figure()
    for i, n in enumerate(sorted({r["n"] for r in rows})):
        sub = sorted((r for r in rows if r["n"] == n), key=lambda r: r["k"])
        fig.add_trace(
            go.Bar(
                x=[f"k = {r['k']}" for r in sub],
                y=[r["nonplanar"] * 100 for r in sub],
                name=f"n = {n}",
                marker_color=C.COLOR_PALETTE[i % len(C.COLOR_PALETTE)],
                hovertemplate="%{x}: %{y:.0f} % nichtplanar<extra>n = " + str(n) + "</extra>",
            )
        )
    fig.update_layout(title=dict(text=title, x=0, font=dict(size=14)), height=340, barmode="group", margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.2, x=0))
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(title="nichtplanar (%)", fixedrange=True, range=[0, 105])
    return fig


def build_cost(rows, title="Schritte des Fragmenttests"):
    fig = go.Figure()
    xs = [r["n"] for r in rows]
    fig.add_trace(go.Scatter(x=xs, y=[r["steps"] for r in rows], mode="lines+markers", name="Fragmenttest", line=dict(color=C.COLOR_BASE, width=3)))
    base = rows[0]
    fig.add_trace(
        go.Scatter(x=xs, y=[base["steps"] * (x / base["n"]) ** 2 for x in xs], mode="lines", name="zum Vergleich: n hoch 2", line=dict(color="#888", dash="dot"))
    )
    fig.update_layout(title=dict(text=title, x=0, font=dict(size=14)), height=380, margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.35, x=0))
    fig.update_xaxes(title="Knoten n", type="log", fixedrange=True, tickmode="array", tickvals=xs, ticktext=[str(x) for x in xs])
    fig.update_yaxes(title="Schritte", type="log", fixedrange=True)
    return fig


def crossing_point(p1, p2, q1, q2):
    """Schnittpunkt zweier sich kreuzender Strecken."""
    rx, ry = p2[0] - p1[0], p2[1] - p1[1]
    sx, sy = q2[0] - q1[0], q2[1] - q1[1]
    denom = rx * sy - ry * sx
    t = ((q1[0] - p1[0]) * sy - (q1[1] - p1[1]) * sx) / denom
    return p1[0] + t * rx, p1[1] + t * ry


def build_toronto(t, zoom_to_witness=False, height=520):
    """Toronto-Karte: Kanten grau, Streckenkreuzungen rot, gestrichene Kanten (Überdeckung) orange, Zeuge türkis; optional auf die Umgebung des Zeugen gezoomt."""
    inst = t["inst"]
    fig = go.Figure()
    witness_edges = set(t["witness"].edges)
    cover_edges = {inst.edges[i] for i in t["cover"]}
    pos = inst.pos
    window = None
    if zoom_to_witness:
        nodes = sorted({x for e in witness_edges for x in e})
        xs, ys = [pos[v][0] for v in nodes], [pos[v][1] for v in nodes]
        pad = 60.0
        window = (min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad)

    def inside(e):
        if window is None:
            return True
        return any(window[0] <= pos[v][0] <= window[1] and window[2] <= pos[v][1] <= window[3] for v in e)

    rest = [e for e in inst.edges if e not in witness_edges and e not in cover_edges and inside(e)]
    fig.add_trace(_edge_trace(pos, rest, "rgba(150,150,150,0.55)", 1.2 if not zoom_to_witness else 2, "Kanten der Karte", showlegend=True))
    fig.add_trace(_edge_trace(pos, [e for e in cover_edges if e not in witness_edges and inside(e)], C.COLOR_FRAGMENT, 3, "an Kreuzungen beteiligt (Überdeckung)", showlegend=True))
    fig.add_trace(_edge_trace(pos, sorted(witness_edges), C.COLOR_BASE, 4, "Zeuge (Unterteilung von K3,3)", showlegend=True))
    cx, cy = [], []
    for i, j in t["pairs"]:
        a, b = inst.edges[i]
        c, d = inst.edges[j]
        x, y = crossing_point(pos[a], pos[b], pos[c], pos[d])
        if window is None or (window[0] <= x <= window[1] and window[2] <= y <= window[3]):
            cx.append(x)
            cy.append(y)
    fig.add_trace(
        go.Scatter(
            x=cx, y=cy, mode="markers", name="Streckenkreuzung", marker=dict(color=C.COLOR_PATH, size=8 if zoom_to_witness else 6, symbol="x"),
            hoverinfo="skip",
        )
    )
    if zoom_to_witness:
        branch = list(t["witness"].branch)
        fig.add_trace(_node_trace(pos, branch, C.COLOR_PATH, 18, labels=False, name="Verzweigungsknoten", showlegend=True))
    return _layout(fig, None, height, legend=True)
