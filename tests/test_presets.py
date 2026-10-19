"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und was die Hilfetexte über das Ergebnis behaupten."""

import plt_algorithm as A
import plt_constants as C
import plt_evaluation as ev
import plt_presets as P
import plt_scenario as S


def _analysis(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_bounds():
    for preset in C.PRESETS.values():
        assert preset["net"] in C.NET_TYPES
        assert C.N_MIN <= preset["n"] <= C.N_MAX and C.DENSITY_MIN <= preset["density"] <= C.DENSITY_MAX
        assert C.EXTRA_MIN <= preset["extra"] <= C.EXTRA_MAX and 0 <= preset["seed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Lehrbeispiel: eine Karte"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_the_textbook_map_is_planar_and_below_the_bound():
    a = _analysis("Lehrbeispiel: eine Karte")
    assert a.emb.planar and a.inst.m < a.bound and a.layout_crossings == 0


def test_one_extra_edge_makes_the_map_nonplanar_below_the_bound():
    """Das Hilfetext-Versprechen: nichtplanar, obwohl die Schranke 3n − 6 noch nicht erreicht ist, und ein Zeuge ist da."""
    a = _analysis("Eine Kante zu viel")
    base = _analysis("Lehrbeispiel: eine Karte")
    assert a.inst.m == base.inst.m + 1 and not a.emb.planar and a.inst.m < a.bound and a.witness is not None


def test_the_grid_with_a_far_edge_is_nonplanar_with_few_drawing_crossings():
    a = _analysis("Raster mit Fernkante")
    assert not a.emb.planar and a.witness is not None and 1 <= a.layout_crossings <= 3


def test_random_pairs_near_the_tipping_point():
    planar, nonplanar = _analysis("Zufall: knapp planar"), _analysis("Zufall: schon nichtplanar")
    assert planar.emb.planar and planar.layout_crossings > 10                  # viele Kreuzungen der Kreis-Zeichnung, trotzdem planar
    assert not nonplanar.emb.planar and nonplanar.inst.m < nonplanar.bound    # weit unter der Euler-Schranke nichtplanar
    assert nonplanar.witness is not None and nonplanar.witness.kind == "K3,3"


def test_randomize_seed_stays_inside_the_bounds():
    import streamlit as st

    st.session_state.clear()
    P.randomize_seed()
    assert 0 <= st.session_state["seed_input"] <= C.SEED_MAX


def test_hand_graph_names_are_all_defined():
    for name in C.HAND_GRAPHS:
        assert S.hand_graph(name).n >= 4
    assert C.DEFAULT_HAND in C.HAND_GRAPHS and A is not None
