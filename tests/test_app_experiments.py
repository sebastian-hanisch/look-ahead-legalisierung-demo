"""Pfade der App, die der Rauchtest nicht erreicht: die Experimente im Seiteninhalt, PDF, jede Familie, jede Einstellung, große Instanzen, die Rechenknöpfe (DEMO-PLAYBOOK §1d)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

import lal_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
KIND = {"family_select": "selectbox", "n_select": "select_slider", "seed_input": "number_input", "pads_select": "select_slider", "anchor_select": "select_slider", "rounds_select": "select_slider", "reweights_select": "select_slider",
        "legalizer_select": "selectbox"}


def _app(**state) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    for key, value in state.items():
        getattr(at.sidebar, KIND[key])(key=key).set_value(value)
    if state:
        at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join(str(e.value) for e in list(at.success) + list(at.info) + list(at.warning) + list(at.error) + list(at.markdown))


def test_default_page_shows_the_metrics_and_the_verdicts():
    at = _app()
    values = {m.label: m.value for m in at.metric}
    assert set(values) == {"Lücke, Runde 0", "Lücke, Runde 15", "Lücke oben/unten", "Optimum", "Änderungen der Anordnung"}
    assert values["Lücke, Runde 0"] == "17,3 %" and values["Lücke, Runde 15"] == "6,2 %" and values["Optimum"] == "226" and values["Änderungen der Anordnung"] == "1"
    text = _texts(at)
    for part in ("Familie **Zwei Cluster**, 8 Bauteile, Raster 2×4, Seed 38, 4 Pads, Legalisierer Zuordnung, 15 Runden", "die Anordnung ändert sich in 1 Runde (zuletzt in Runde 12)", "weil das Ankergewicht", "Zuordnung: Runde 0 Kosten 265", "Experiment 1 bis 5"):
        assert part in text, part


def test_the_experiments_the_hand_examples_the_limits_table_and_the_formulation_are_on_the_page():
    at = _app()
    headings = [s.value for s in at.subheader]
    assert [h.split(":")[0] for h in headings if h.startswith("🔬 Experiment")] == [f"🔬 Experiment {i}" for i in (1, 2, 3, 4, 5)] and "🚧 Wo die Annahmen enden" in headings
    assert [e.label for e in at.expander] == ["So funktioniert es", "Handbeispiele zum Nachrechnen", "📐 Mathematische Formulierung"]
    assert not at.error and len(at.get("plotly_chart")) == 6
    assert any("x_A = 3/58" in str(m.value) for m in at.markdown)


def test_every_family_every_setting_and_size_renders():
    for fam in C.FAMILIES:
        at = _app(family_select=fam, n_select=6)
        assert f"Familie **{C.FAMILY_NAMES[fam]}**" in _texts(at) and len(at.get("plotly_chart")) == 6
    for key, values in (("pads_select", C.PAD_CHOICES), ("anchor_select", C.ANCHOR_CHOICES), ("rounds_select", C.ROUND_CHOICES[:3]), ("reweights_select", C.REWEIGHT_CHOICES), ("legalizer_select", C.LEGALIZERS)):
        for value in values:
            at = _app(n_select=6, **{key: value})
            assert len(at.get("plotly_chart")) == 6 and not at.exception, (key, value)
    for n in (9, 12, 16):
        at = _app(n_select=n, rounds_select=5)
        assert f"{n} Bauteile" in _texts(at) and len(at.get("plotly_chart")) == 6


def test_the_legalizer_and_the_weights_change_the_result():
    base = {m.label: m.value for m in _app().metric}
    bis = {m.label: m.value for m in _app(legalizer_select="bisect").metric}
    assert base["Lücke, Runde 0"] != bis["Lücke, Runde 0"]
    nr = _app(reweights_select=0)
    assert any(m.label == "Änderungen der Anordnung" and m.value == "0" for m in nr.metric) and "bleibt bis zur letzten Runde gleich" in _texts(nr)
    five = _app(rounds_select=5)
    assert any(m.label == "Lücke, Runde 5" for m in five.metric)


def test_the_round_view_follows_the_round_count():
    at = _app()
    sl = [s for s in at.select_slider if s.key == "round_view_15"]
    assert len(sl) == 1
    sl[0].set_value(7).run()
    assert not at.exception and any("Runde 7:" in str(c.proto) for c in at.get("plotly_chart"))
    at2 = _app(rounds_select=60)
    assert any(s.key == "round_view_60" for s in at2.select_slider) and not at2.exception


def test_the_pdf_button_makes_a_download():
    at = _app(n_select=6)
    at.button(key="pdf_make").click().run()
    assert not at.exception
    assert any(d.proto.label == "⬇️ PDF herunterladen" for d in at.get("download_button"))


def test_the_comparison_buttons_fill_their_sections(monkeypatch):
    monkeypatch.setattr(C, "SWEEP_SEEDS", C.SWEEP_SEEDS[:2])                       # nur für die Geschwindigkeit des Tests: die echten Reihen stehen in test_claims.py
    monkeypatch.setattr(C, "SWEEP_SEEDS_SMALL", C.SWEEP_SEEDS[:1])
    monkeypatch.setattr(C, "LARGE_SEEDS", C.SWEEP_SEEDS[:1])
    at = _app(n_select=6)
    assert [b.label for b in at.button if "⏱️" in b.label] == ["⏱️ Vergleich rechnen (n = 8)", "⏱️ 120 Runden für die gewählte Instanz rechnen", "⏱️ Konvergenz über feste Instanzen rechnen", "⏱️ Große Instanzen rechnen (n = 12)"]
    at.button(key="sweep_button").click().run()
    assert not at.exception and "Bei n = 8, Median der Lücke über 12 Instanzen je Zahl der Pads" in _texts(at) and "Legalisierer im Vergleich" in _texts(at) and len(at.get("plotly_chart")) == 6 + 1
    at.button(key="long_button").click().run()
    assert not at.exception and "nach 0 / 5 / 15 / 30 / 60 / 120 Runden" in _texts(at) and len(at.get("plotly_chart")) == 6 + 1 + 1
    at.button(key="long_sweep_button").click().run()
    assert not at.exception and "Über 6 Instanzen (vier Pads" in _texts(at)
    at.button(key="large_button").click().run()
    assert not at.exception and "Bei n = 12, Median der Lücke über 6 Instanzen je Zahl der Pads" in _texts(at) and "obere Grenze der Lücke" in _texts(at)
