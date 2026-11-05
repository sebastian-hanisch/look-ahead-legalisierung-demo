"""Abbildungen: sie entstehen für jede Eingabe, Achsen sind gesperrt, Beschriftungen und Daten stimmen mit den Werten überein; PDF-Export."""

import lal_constants as C
import lal_evaluation as ev
import lal_instance as I
import lal_visualization as V
from lal_pdf_export import build_pdf


def _locked(fig):
    return fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_positions_chart_for_every_round_and_size():
    for n in (6, 9, 12):
        s = ev.Settings("uniform", n, 100000, 4, rounds=2)
        v = ev.instance_data(s)
        for rnd in v["loop"].rounds:
            fig = V.build_positions(v["inst"], v["pads"], rnd.X, rnd.perm, "Test")
            names = [t.name for t in fig.data]
            assert names[0] == "Plätze" and names[-1] == "stetige Orte" and "Pads (fest)" in names and "Rundung auf den Platz" in names and _locked(fig) and len(fig.data[-1].x) == n


def test_loop_curve_carries_the_values(land6):
    s = ev.Settings("netlist", 6, 35, rounds=5)
    v = ev.instance_data(s)
    fig = V.build_loop_curve(v["loop"], v["ref"])
    assert [t.name for t in fig.data] == ["obere Kosten (legale Anordnung)", "untere Länge (stetige Lösung)", "Vergleichswert"] and list(fig.data[0].y) == v["loop"].uppers and list(fig.data[1].y) == v["loop"].lowers
    assert list(fig.data[0].x) == list(range(6)) and list(fig.data[2].y) == [v["ref"], v["ref"]] and _locked(fig)


def test_gap_curve_has_one_line_per_legalizer():
    s = ev.Settings("cluster", 8, 38, rounds=4)
    v = ev.instance_data(s)
    fig = V.build_gap_curve(v["loops"], v["ref"], C.LEGALIZER_NAMES)
    assert [t.name for t in fig.data] == [C.LEGALIZER_NAMES[k] for k in C.LEGALIZERS] and list(fig.data[0].y) == [100 * (u - v["ref"]) / v["ref"] for u in v["loops"]["assign"].uppers] and _locked(fig)


def test_anchor_sweep_and_long_charts():
    s = ev.Settings("cluster", 8, 38, rounds=4)
    v = ev.instance_data(s)
    ac = ev.anchor_curve(s, v)
    f1 = V.build_anchor_bars(ac)
    assert list(f1.data[0].x) == [f"c = {c:g}" for c in C.ANCHOR_CHOICES] and list(f1.data[1].y) == [100 * c["luT"] for c in ac] and _locked(f1)
    rows = [r for f in C.FAMILIES for r in ev.sweep(f, 6, (100000, 100001), (2, 8))]
    f2 = V.build_sweep_bars(rows, ev.median_of, ev.variant_summary, "t")
    assert [t.name for t in f2.data] == ["Runde 0 (Zuordnung)", "Zuordnung, 2 Umgewichtungen", "Zuordnung, ohne Umgewichtung", "Zweiteilung, 2 Umgewichtungen"] and list(f2.data[0].x) == ["2 Pads", "8 Pads"] and _locked(f2)
    lrows = [ev.long_row(f, 6, 100000, 4) for f in C.FAMILIES]
    f3 = V.build_long_curve(lrows, ev.CHECKPOINTS, "t")
    assert list(f3.data[0].x) == [str(k) for k in ev.CHECKPOINTS] and len(f3.data[0].y) == 6 and f3.data[0].y[-1] < f3.data[0].y[0] and _locked(f3)


def test_arrangement_chart_for_every_family_and_size(hand):
    for fam in C.FAMILIES:
        for n in (6, 9, 12, 16):
            assert len(V.build_arrangement(I.make_instance(fam, n, 3), list(range(n)), fam).data[-1].x) == n
    assert len(V.build_arrangement(hand, [0, 1, 2], "Hand").data[-1].x) == 3


def test_the_pdf_export_returns_a_pdf_for_an_exact_and_a_large_instance():
    s = ev.Settings("netlist", 6, 35, rounds=3)
    assert build_pdf(s, ev.instance_data(s))[:5] == b"%PDF-"
    s2 = ev.Settings("uniform", 12, 35, 2, 1.0, 5, 0, "bisect")
    data = build_pdf(s2, ev.instance_data(s2))
    assert data[:5] == b"%PDF-" and len(data) > 1500
