"""Auswertung: Analyse einer Instanz, Messreihen (Kipppunkt, Zusatzkanten, Kosten), Toronto-Befund und die Verdikte als reine Funktionen."""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass

import plt_algorithm as A
import plt_constants as C
import plt_scenario as S


def plural(count: int, singular: str, plural_form: str) -> str:
    """„1 Block“, „2 Blöcke“."""
    return f"{count} {singular if count == 1 else plural_form}"


def num(x: float, digits: int = 0) -> str:
    """Zahl im deutschen Format: Tausenderpunkt, Dezimalkomma (die Texte der App und der Verdikte nutzen nur diese Schreibweise)."""
    text = f"{x:,.{digits}f}"
    return text.translate(str.maketrans({",": ".", ".": ","}))


@dataclass(frozen=True)
class Settings:
    net: str = C.DEFAULT_NET
    n: int = C.DEFAULT_N
    density: int = C.DEFAULT_DENSITY
    extra: int = C.DEFAULT_EXTRA
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Analysis:
    inst: S.Instance
    emb: A.Embedding
    witness: A.Witness | None
    bound: int                   # 3n − 6 (Höchstzahl der Kanten eines planaren Graphen)
    layout_crossings: int        # Kreuzungen der Zeichnung (nur Layout, sagt nichts über Planarität)


def analyse(settings: Settings) -> Analysis:
    inst = S.make_instance(settings.net, settings.n, settings.density, settings.extra, settings.seed)
    return analyse_instance(inst)


def analyse_instance(inst: S.Instance) -> Analysis:
    emb = A.embed(inst.n, inst.edges)
    witness = A.witness_for(emb, C.WITNESS_MAX_EDGES)
    return Analysis(inst, emb, witness, S.euler_bound(inst.n), len(A.crossings(inst.pos, inst.edges)))


# --- Messreihen -----------------------------------------------------------------------------------------------------------------------------


def mean_degree(n: int, density: int) -> float:
    """Mittlerer Grad eines Graphen mit n Knoten und der Dichte (in % von 3n − 6) in Kanten."""
    return 2 * S.target_edge_count(n, density) / n


def share_planar(net: str, n: int, density: int, extra: int, samples: int, seed0: int = 200000) -> float:
    """Anteil planarer Graphen unter `samples` Instanzen mit aufeinanderfolgenden Seeds."""
    count = 0
    for i in range(samples):
        inst = S.make_instance(net, n, density, extra, seed0 + i)
        count += A.is_planar_edges(inst.edges)
    return count / samples


def share_table(ns=C.SHARE_NS, densities=C.SHARE_DENSITIES, samples=C.SHARE_SAMPLES) -> list[dict]:
    """Anteil planarer Zufallsverbindungen über der Dichte, je Knotenzahl."""
    return [
        {"n": n, "density": d, "degree": mean_degree(n, d), "share": share_planar("gnc", n, d, 0, samples)}
        for n in ns
        for d in densities
    ]


def plus_table(ns=C.PLUS_NS, ks=C.PLUS_KS, samples=C.PLUS_SAMPLES) -> list[dict]:
    """Anteil nichtplanarer Graphen, wenn man zu einem verdünnten planaren Karten-Netz k Zusatzkanten legt."""
    rows = []
    for n in ns:
        for k in ks:
            nonplanar = 1.0 - share_planar("delaunay", n, C.PLUS_DENSITY, k, samples)
            rows.append({"n": n, "k": k, "nonplanar": nonplanar})
    return rows


def cost_table(ns=C.COST_NS, seeds=C.SWEEP_SEEDS) -> list[dict]:
    """Schritte des Fragmenttests auf voll trianguliertem Karten-Netz (Median über feste Instanzen) und Kantenzahl."""
    rows = []
    for n in ns:
        steps, edges = [], []
        for seed in seeds:
            inst = S.make_instance("delaunay", n, 100, 0, seed)
            emb = A.embed(inst.n, inst.edges)
            assert emb.planar
            steps.append(emb.steps)
            edges.append(inst.m)
        rows.append({"n": n, "steps": statistics.median(steps), "m": statistics.median(edges)})
    return rows


# --- Toronto --------------------------------------------------------------------------------------------------------------------------------


def toronto_stats() -> dict:
    """Befund zur Toronto-Karte: Größe, Streckenkreuzungen, Krümmung, Überdeckung; der Zeuge aus `data/toronto_befund.json` wird hier unabhängig geprüft."""
    inst, length = S.load_toronto()
    fixed = json.loads((S.DATA / "toronto_befund.json").read_text(encoding="utf-8"))
    pairs = A.crossings(inst.pos, inst.edges, C.TORONTO_CROSS_CELL)
    curvature = {}
    for (u, v) in inst.edges:
        dx, dy = inst.pos[u][0] - inst.pos[v][0], inst.pos[u][1] - inst.pos[v][1]
        straight = math.hypot(dx, dy)
        curvature[(u, v)] = length[(u, v)] / straight if straight > 0 else float("inf")
    ratios = sorted(curvature.values())
    curved_cross = sum(1 for i, j in pairs if curvature[inst.edges[i]] >= 1.2 or curvature[inst.edges[j]] >= 1.2)
    straight_cross = sum(1 for i, j in pairs if curvature[inst.edges[i]] < 1.05 and curvature[inst.edges[j]] < 1.05)
    cover = A.greedy_cover(pairs)
    witness_edges = tuple(tuple(e) for e in fixed["witness_edges"])
    witness = A.classify_witness(witness_edges)
    problems = A.verify_witness(inst.edges, witness)
    witness_nonplanar = not A.is_planar_edges(witness_edges)
    return {
        "inst": inst,
        "length": length,
        "pairs": pairs,
        "crossings": len(pairs),
        "involved_edges": len({k for p in pairs for k in p}),
        "median_ratio": ratios[len(ratios) // 2],
        "share_curved": sum(1 for r in ratios if r > 1.05) / len(ratios),
        "curved_cross": curved_cross,
        "straight_cross": straight_cross,
        "cover": cover,
        "cover_size": len(cover),
        "witness": witness,
        "witness_problems": problems,
        "witness_nonplanar": witness_nonplanar,
        "fixed": fixed,
    }


# --- Verdikte (reine Funktionen: Art, Text) -------------------------------------------------------------------------------------------------


def verdict_planarity(a: Analysis) -> tuple[str, str]:
    """Hauptergebnis: planar (mit Einbettung) oder nicht planar (mit Zeuge)."""
    emb = a.emb
    if emb.planar:
        paths = sum(1 for b in emb.blocks for e in b.events if e.kind == "path")
        return (
            "success",
            f"Der Graph ist **planar**: Der Fragmenttest hat ihn eingebettet ({plural(len(emb.blocks), 'Block', 'Blöcke')}, {plural(paths, 'Weg', 'Wege')} eingefügt, {emb.steps} Schritte). "
            f"Die Einbettung hat **{emb.faces} Flächen**; die Euler-Formel n − m + f = {1 + emb.components} stimmt: {emb.n} − {emb.m} + {emb.faces} = {emb.n - emb.m + emb.faces}.",
        )
    if a.witness is None:
        return "error", f"Der Graph ist **nicht planar**: Ein Fragment hat keine Fläche, in der alle seine Anschlussknoten liegen ({emb.steps} Schritte). Der Block ist zu groß für den Kantenabbau, einen Zeugen gibt es hier nicht."
    w = a.witness
    return (
        "error",
        f"Der Graph ist **nicht planar**: Ein Fragment hat keine Fläche, in der alle seine Anschlussknoten liegen. Der Kantenabbau liefert den Beleg: "
        f"eine Unterteilung von **{w.kind}** aus {len(w.edges)} von {emb.m} Kanten (nach {w.tests} Tests).",
    )


def verdict_euler(a: Analysis) -> tuple[str, str]:
    """Kantenschranke 3n − 6: notwendig, nicht hinreichend."""
    m, bound = a.emb.m, a.bound
    if m > bound:
        return "info", f"Mit m = {m} Kanten liegt der Graph **über** der Schranke 3n − 6 = {bound}: Schon die Kantenzahl schließt Planarität aus."
    gap = bound - m
    if a.emb.planar:
        return "info", f"m = {m} Kanten, die Schranke 3n − 6 = {bound} lässt noch **{gap}** zu. Planar ist der Graph aus eigenem Recht, nicht wegen der Schranke."
    return (
        "warning",
        f"m = {m} Kanten liegen **{gap} unter** der Schranke 3n − 6 = {bound}, und der Graph ist trotzdem nicht planar: Die Kantenschranke ist notwendig, aber nicht hinreichend.",
    )


def tipping_density(rows: list[dict], n: int) -> int | None:
    """Kleinste gemessene Dichte, bei der höchstens die Hälfte der Graphen planar ist; None, wenn der Anteil nie so weit fällt."""
    for r in sorted((r for r in rows if r["n"] == n), key=lambda r: r["density"]):
        if r["share"] <= 0.5:
            return r["density"]
    return None


def verdict_share(rows: list[dict]) -> tuple[str, str]:
    """Kipppunkt der Planarität in Zufallsverbindungen."""
    parts = []
    for n in sorted({r["n"] for r in rows}):
        d = tipping_density(rows, n)
        if d is None:
            parts.append(f"bei n = {n} bleibt der Anteil über der Hälfte")
        else:
            row = next(r for r in rows if r["n"] == n and r["density"] == d)
            parts.append(f"bei n = {n} fällt der Anteil planarer Graphen bei Dichte {d} % (mittlerer Grad {num(row['degree'], 1)}) auf höchstens die Hälfte")
    return "info", "Zufallsverbindungen kippen weit vor der Höchstdichte: " + "; ".join(parts) + ". Die Euler-Schranke erlaubt dagegen bis Dichte 100 % (mittlerer Grad knapp 6)."


def verdict_plus(rows: list[dict]) -> tuple[str, str]:
    """Wie schnell eine Zusatzkante einen planaren Graphen kippt."""
    parts = []
    for n in sorted({r["n"] for r in rows}):
        one = next((r for r in rows if r["n"] == n and r["k"] == 1), None)
        if one is not None:
            parts.append(f"n = {n}: eine Zusatzkante macht {num(one['nonplanar'] * 100)} % der Graphen nichtplanar")
    return "info", "Ein dünnes planares Karten-Netz verträgt wenig Zusatz: " + "; ".join(parts) + "."


def cost_exponent(rows: list[dict]) -> float:
    """Steigung der Schritte über n im doppelt-logarithmischen Maßstab zwischen der kleinsten und größten Größe."""
    first, last = rows[0], rows[-1]
    return math.log(last["steps"] / first["steps"]) / math.log(last["n"] / first["n"])


def verdict_cost(rows: list[dict]) -> tuple[str, str]:
    """Wachstum der Schritte des Fragmenttests mit n."""
    first, last = rows[0], rows[-1]
    return (
        "info",
        f"Auf voll triangulierten Karten wächst der Aufwand von {num(first['steps'])} Schritten bei n = {first['n']} auf {num(last['steps'])} bei n = {last['n']}: "
        f"etwa mit n hoch **{num(cost_exponent(rows), 1)}**. Das ist die Zahl der Besuche und Flächenprüfungen dieser Umsetzung, keine Laufzeit.",
    )


def verdict_toronto(t: dict) -> tuple[str, str]:
    """Ehrlicher Befund zur Karte: nichtplanar, aber nahe an planar; Ursache offen."""
    w = t["witness"]
    n_all = t["inst"].m
    return (
        "warning",
        f"Die Karte ist **nicht planar**: Der Zeuge ist eine Unterteilung von {w.kind} aus {len(w.edges)} Kanten (nachgeprüft). "
        f"Sie ist aber nahe an planar: Streicht man {t['cover_size']} von {num(n_all)} Kanten ({num(t['cover_size'] / n_all * 100, 1)} %), die an Streckenkreuzungen beteiligt sind, wird sie planar. "
        f"Von den {t['crossings']} Streckenkreuzungen der Zeichnung gehen {t['curved_cross']} auf mindestens eine stark gekrümmte Kante zurück, die als Gerade gezeichnet ist. "
        f"**Ob Brücken, Tunnel oder nicht verschmolzene Knoten die Ursache sind, lässt sich mit diesen Daten nicht entscheiden** (sie enthalten keine Brücken- oder Tunnelmarken).",
    )
