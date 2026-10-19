"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: laedt app.py mit den
Standardeinstellungen, klickt jeden Preset-Button und faehrt jeden Slider an seine Grenzen und prueft, dass
kein Python-Fehler auftritt - insbesondere `streamlit.errors.StreamlitDuplicateElementId` (mehrere
st.plotly_chart-Aufrufe ohne eindeutiges key= koennen zufaellig identischen Inhalt rendern und kollidieren)
und `StreamlitAPIException` bei Slidern mit berechneten Grenzen (min == max)."""

import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
AUTOPLAY_MARKER = "\u25b6"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_app_loads_without_exception():
    _fresh_app()


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label:
            continue
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


def _selectbox(at, key):
    return next(s for s in list(at.sidebar.selectbox) + list(at.main.selectbox) if s.key == key)


def test_every_selectbox_option_does_not_raise():
    """Netztyp und Lehrbuch-Graph: jede Option einzeln (der allgemeine Slider-Test deckt Auswahlfelder nicht ab). AppTest kennt nur die Rohwerte, nicht die Beschriftungen."""
    import plt_constants as C

    at = _fresh_app()
    assert {s.key for s in list(at.sidebar.selectbox) + list(at.main.selectbox)} >= {"net_select", "hand_select"}
    for key, options in (("net_select", tuple(C.NET_TYPES)), ("hand_select", C.HAND_GRAPHS)):
        for option in options:
            fresh = _fresh_app()
            _selectbox(fresh, key).set_value(option).run(timeout=TIMEOUT)
            assert not fresh.exception, (key, option, [str(e) for e in fresh.exception])


def _many_blocks_app():
    """Karte mit 60 Knoten bei Dichte 40 %: sieben Blöcke mit mindestens drei Knoten (feste Einstellung)."""
    at = _fresh_app()
    at.sidebar.slider(key="n_slider").set_value(60)
    at.sidebar.slider(key="density_slider").set_value(40)
    at.sidebar.number_input(key="seed_input").set_value(1)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_every_block_and_every_step_of_a_graph_with_many_blocks():
    """Jeder Block lässt sich wählen, der Schrittregler geht bis an beide Enden."""
    import plt_evaluation as ev

    emb = ev.analyse(ev.Settings("delaunay", 60, 40, 0, 1)).emb
    blocks = [i for i, b in enumerate(emb.blocks) if len(b.nodes) >= 3]
    assert len(blocks) == 7
    for index in blocks:
        at = _many_blocks_app()
        _selectbox(at, "main_block").set_value(index).run(timeout=TIMEOUT)
        assert not at.exception, (index, [str(e) for e in at.exception])
        for edge in ("min", "max"):
            slider = next(s for s in at.main.slider if s.key.startswith("main_step_"))
            slider.set_value(slider.min if edge == "min" else slider.max).run(timeout=TIMEOUT)
            assert not at.exception, (index, edge, [str(e) for e in at.exception])
