"""Rechnet den schweren Teil des Toronto-Befunds einmal vor und schreibt `data/toronto_befund.json`.

Aufruf (aus dem Demo-Ordner): python tools/toronto_befund.py
Der Zeuge wird durch Kantenabbau in Teilmengen (ddmin) gesucht, weil der Abbau je Kante bei m = 7 621 Kanten m Tests bräuchte. Die App prüft den Zeugen
unabhängig (`verify_witness`, Nichtplanarität des Zeugen allein) und rechnet alle übrigen Zahlen selbst nach; hier steht nur, was zu langsam ist.
Das Ergebnis von `networkx` dient in tests/test_claims.py als Gegenprobe."""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import plt_algorithm as A  # noqa: E402
import plt_constants as C  # noqa: E402
import plt_scenario as S  # noqa: E402


def ddmin(edges, nonplanar):
    """Kantenminimale Teilmenge, die nichtplanar bleibt (Delta-Debugging nach Zeller und Hildebrandt); gibt die Menge und die Testzahl."""
    current = list(edges)
    granularity = 2
    tests = 0
    while len(current) >= 2:
        size = max(1, len(current) // granularity)
        chunks = [current[i : i + size] for i in range(0, len(current), size)]
        progressed = False
        for chunk in chunks:
            drop = set(chunk)
            rest = [e for e in current if e not in drop]
            tests += 1
            if nonplanar(rest):
                current = rest
                granularity = max(granularity - 1, 2)
                progressed = True
                break
        if not progressed:
            if granularity >= len(current):
                break
            granularity = min(len(current), granularity * 2)
    return current, tests


def main():
    inst, _ = S.load_toronto()
    start = time.perf_counter()
    emb = A.embed(inst.n, inst.edges)
    block = emb.blocks[emb.failed_block]
    print("Fragmenttest:", "planar" if emb.planar else "nicht planar", f"Block {len(block.nodes)} Knoten, {len(block.edges)} Kanten, {round(time.perf_counter() - start, 2)} s")
    witness_edges, tests = ddmin(block.edges, lambda es: not A.is_planar_edges(es))
    w = A.classify_witness(witness_edges, tests)
    print("Zeuge:", w.kind, len(w.edges), "Kanten,", tests, "Tests; Prüfung:", A.verify_witness(inst.edges, w) or "in Ordnung")
    pairs = A.crossings(inst.pos, inst.edges, C.TORONTO_CROSS_CELL)
    cover = A.greedy_cover(pairs)
    kept = [e for i, e in enumerate(inst.edges) if i not in set(cover)]
    t0 = time.perf_counter()
    planar_after = A.embed(inst.n, kept).planar
    print("Nach dem Streichen von", len(cover), "Kanten: planar =", planar_after, f"({round(time.perf_counter() - t0, 1)} s, eigener Fragmenttest)")
    out = {
        "source": "OpenStreetMap, ODbL 1.0 (Auszug aus bfs-demo, ungerichtet vereinigt)",
        "block_nodes": len(block.nodes),
        "block_edges": len(block.edges),
        "witness_edges": [list(e) for e in w.edges],
        "witness_tests": tests,
        "cover_edges": [list(inst.edges[i]) for i in cover],
        "planar_after_cover": planar_after,
    }
    (ROOT / "data" / "toronto_befund.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("geschrieben:", ROOT / "data" / "toronto_befund.json")


if __name__ == "__main__":
    main()
