"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import dataclasses

import plt_evaluation as ev
import plt_scenario as S


def _hand(name):
    return ev.analyse_instance(S.hand_graph(name))


def test_plural():
    assert ev.plural(1, "Block", "Blöcke") == "1 Block" and ev.plural(0, "Block", "Blöcke") == "0 Blöcke" and ev.plural(2, "Weg", "Wege") == "2 Wege"


def test_num_uses_german_separators():
    assert ev.num(1234567.891, 1) == "1.234.567,9" and ev.num(0.5, 1) == "0,5" and ev.num(1000) == "1.000" and ev.num(7) == "7"


def test_verdict_planar_names_paths_faces_and_the_euler_check():
    kind, text = ev.verdict_planarity(_hand("Würfel"))
    assert kind == "success" and "**planar**" in text
    assert "1 Block, 4 Wege eingefügt" in text                    # Anfangskreis + 4 Wege: 2 + 4 = 6 Flächen
    assert "**6 Flächen**" in text and "n − m + f = 2 stimmt: 8 − 12 + 6 = 2" in text


def test_verdict_nonplanar_names_the_kind_the_edges_and_the_tests():
    kind, text = ev.verdict_planarity(_hand("K5"))
    assert kind == "error" and "**nicht planar**" in text
    assert "**K5** aus 10 von 10 Kanten (nach 10 Tests)" in text
    kind, text = ev.verdict_planarity(_hand("K3,3 mit Unterteilungen"))
    assert "**K3,3** aus 11 von 11 Kanten (nach 11 Tests)" in text


def test_verdict_nonplanar_without_witness_says_the_block_is_too_large():
    a = dataclasses.replace(_hand("K5"), witness=None)
    kind, text = ev.verdict_planarity(a)
    assert kind == "error" and "zu groß für den Kantenabbau" in text and "Unterteilung" not in text


def test_verdict_euler_three_cases():
    kind, text = ev.verdict_euler(_hand("K5"))                      # 10 > 9
    assert kind == "info" and "m = 10 Kanten liegt der Graph **über** der Schranke 3n − 6 = 9" in text
    kind, text = ev.verdict_euler(_hand("Würfel"))                  # 12 ≤ 18, planar
    assert kind == "info" and "m = 12 Kanten, die Schranke 3n − 6 = 18 lässt noch **6** zu" in text
    kind, text = ev.verdict_euler(_hand("K3,3"))                    # 9 ≤ 12, nichtplanar
    assert kind == "warning" and "m = 9 Kanten liegen **3 unter** der Schranke 3n − 6 = 12" in text and "notwendig, aber nicht hinreichend" in text


def test_verdict_euler_at_exactly_the_bound_is_not_over_it():
    kind, text = ev.verdict_euler(_hand("Oktaeder"))                # 12 = 12
    assert kind == "info" and "lässt noch **0** zu" in text


def test_tipping_density_is_inclusive_at_one_half():
    rows = [{"n": 20, "density": 10, "degree": 0.6, "share": 1.0}, {"n": 20, "density": 30, "degree": 1.8, "share": 0.51}, {"n": 20, "density": 50, "degree": 3.0, "share": 0.5}]
    assert ev.tipping_density(rows, 20) == 50
    assert ev.tipping_density(rows[:2], 20) is None
    assert ev.tipping_density(rows, 99) is None


def test_verdict_share_names_density_and_mean_degree():
    rows = [
        {"n": 20, "density": 10, "degree": 1.1, "share": 1.0}, {"n": 20, "density": 40, "degree": 4.4, "share": 0.4},
        {"n": 40, "density": 10, "degree": 1.2, "share": 1.0}, {"n": 40, "density": 40, "degree": 4.5, "share": 0.6},
    ]
    kind, text = ev.verdict_share(rows)
    assert kind == "info"
    assert "bei n = 20 fällt der Anteil planarer Graphen bei Dichte 40 % (mittlerer Grad 4,4) auf höchstens die Hälfte" in text
    assert "bei n = 40 bleibt der Anteil über der Hälfte" in text


def test_verdict_plus_names_the_share_after_one_extra_edge():
    rows = [{"n": 30, "k": 0, "nonplanar": 0.0}, {"n": 30, "k": 1, "nonplanar": 0.39}, {"n": 60, "k": 1, "nonplanar": 0.7}]
    kind, text = ev.verdict_plus(rows)
    assert kind == "info" and "n = 30: eine Zusatzkante macht 39 % der Graphen nichtplanar" in text and "n = 60: eine Zusatzkante macht 70 %" in text


def test_cost_exponent_and_verdict():
    rows = [{"n": 20, "steps": 1000, "m": 50}, {"n": 40, "steps": 4000, "m": 100}, {"n": 80, "steps": 16000, "m": 200}]
    assert abs(ev.cost_exponent(rows) - 2.0) < 1e-9
    kind, text = ev.verdict_cost(rows)
    assert "von 1.000 Schritten bei n = 20 auf 16.000 bei n = 80" in text and "n hoch **2,0**" in text and "keine Laufzeit" in text


def test_verdict_toronto_states_numbers_and_the_open_cause():
    w = ev.A.classify_witness(S.hand_graph("K3,3").edges)
    inst = S.Instance(10, tuple((i, i + 1) for i in range(9)), tuple((0.0, 0.0) for _ in range(10)), "t")
    t = {"witness": w, "inst": inst, "cover_size": 2, "crossings": 7, "curved_cross": 3}
    kind, text = ev.verdict_toronto(t)
    assert kind == "warning" and "Unterteilung von K3,3 aus 9 Kanten" in text
    assert "Streicht man 2 von 9 Kanten (22,2 %)" in text and ev.num(7621) == "7.621" and "Von den 7 Streckenkreuzungen" in text and "gehen 3 auf" in text
    assert "nicht entscheiden" in text
