"""Darstellung: der Zustand des Abspielens (reine Funktion) und dass jede Figur ohne Fehler entsteht, mit festen Achsen."""

import plotly.graph_objects as go
import pytest

import plt_algorithm as A
import plt_constants as C
import plt_evaluation as ev
import plt_scenario as S
import plt_visualization as V

HOUSE = [(0, 1), (1, 2), (2, 3), (0, 3), (0, 4), (1, 4)]


def _house_block():
    return A.embed_block(HOUSE)


def test_playback_state_before_the_first_step_is_empty():
    s = V.playback_state(_house_block(), 0)
    assert s["edges"] == set() and s["nodes"] == set() and s["path"] == () and s["fragment"] is None and not s["failed"]


def test_playback_state_after_the_cycle_and_after_the_path():
    block = _house_block()
    one = V.playback_state(block, 1)
    assert one["edges"] == {(0, 1), (1, 2), (2, 3), (0, 3)} and one["nodes"] == {0, 1, 2, 3} and len(one["path"]) == 5   # geschlossener Kreis
    two = V.playback_state(block, 2)
    assert two["edges"] == set(HOUSE) and two["nodes"] == {0, 1, 2, 3, 4} and two["path"] == (0, 4, 1)
    assert two["fragment"] == A.Fragment((0, 1), (4,))


def test_playback_state_of_a_failing_block_ends_with_the_failed_fragment():
    k5 = A.embed_block(S.hand_graph("K5").edges)
    s = V.playback_state(k5, len(k5.events))
    assert s["failed"] and s["fragment"] is not None
    assert V.playback_state(k5, len(k5.events) + 5)["failed"]               # über das Ende hinaus: gleicher Zustand


def test_fragment_edges():
    assert V.fragment_edges(HOUSE, None) == []
    assert V.fragment_edges(HOUSE, A.Fragment((0, 2), ())) == [(0, 2)]
    assert sorted(V.fragment_edges(HOUSE, A.Fragment((0, 1), (4,)))) == [(0, 4), (1, 4)]


def test_crossing_point_of_an_x():
    assert V.crossing_point((0, 0), (2, 2), (0, 2), (2, 0)) == (1.0, 1.0)


def _fixed_axes(fig):
    return fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


@pytest.mark.parametrize("name", list(C.HAND_GRAPHS))
def test_every_textbook_graph_draws_in_every_mode(name):
    a = ev.analyse_instance(S.hand_graph(name))
    block = max(a.emb.blocks, key=lambda b: len(b.nodes))
    figs = [V.build_graph(a.inst), V.build_playback(a.inst, block, 0), V.build_playback(a.inst, block, len(block.events))]
    if a.witness is not None:
        figs.append(V.build_witness(a.inst, a.witness))
    for f in figs:
        assert isinstance(f, go.Figure) and _fixed_axes(f)


def test_playback_marks_the_failed_fragment_in_the_failure_colour():
    inst = S.hand_graph("K3,3")
    block = A.embed_block(inst.edges)
    fig = V.build_playback(inst, block, len(block.events))
    colours = {tr.line.color for tr in fig.data if tr.mode == "lines"} | {tr.marker.color for tr in fig.data if tr.mode and "markers" in tr.mode}
    assert C.COLOR_BAD in colours


def test_measure_figures_have_fixed_axes():
    share = [{"n": 20, "density": d, "degree": 1.0, "share": s} for d, s in ((10, 1.0), (50, 0.4), (100, 0.0))]
    plus = [{"n": 30, "k": k, "nonplanar": v} for k, v in ((0, 0.0), (1, 0.4))]
    cost = [{"n": 20, "steps": 1000, "m": 50}, {"n": 40, "steps": 4000, "m": 100}]
    for fig in (V.build_share(share), V.build_plus(plus), V.build_cost(cost)):
        assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_toronto_figures_build():
    t = ev.toronto_stats()
    for zoom in (False, True):
        fig = V.build_toronto(t, zoom_to_witness=zoom)
        assert isinstance(fig, go.Figure) and _fixed_axes(fig)
