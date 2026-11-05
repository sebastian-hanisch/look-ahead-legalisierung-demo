"""Zeilen für die Vergleiche, Zusammenfassungen und Instanzdaten: Handwerte und Eigenschaften."""

import math

import numpy as np
import pytest

import lal_constants as C
import lal_evaluation as ev
import lal_instance as I
import lal_loop as Lp
import lal_place as Pl


def test_helpers():
    assert ev.de(-1.5, 1) == "−1,5" and ev.pct(0.266, 1) == "26,6 %" and ev.fam("star") == "Stern" and ev.num(27.0) == "27" and ev.num(26.5) == "26,5" and ev.runden(1) == "1 Runde" and ev.runden(0) == "0 Runden" and ev.anchor_text(0.02) == "0,02" and ev.anchor_text(1.0) == "1"
    assert ev.rel(110, 100) == pytest.approx(0.1) and math.isnan(ev.rel(5, 0)) and ev.rel(100 + 1e-14, 100) == 0.0 and ev.lu_gap(100, 40) == pytest.approx(0.6) and math.isnan(ev.lu_gap(0, 1))
    assert ev.median_of([{"v": 1}, {"v": 5}, {"v": 2}], "v") == 2.0


def test_instance_data_has_both_loops_and_the_reference(land6):
    inst, ls = land6
    s = ev.Settings("netlist", 6, 35, rounds=5)
    v = ev.instance_data(s)
    assert set(v["loops"]) == set(C.LEGALIZERS) and v["loop"] is v["loops"][s.legalizer] and v["exact"] and len(v["loop"].rounds) == 6
    assert v["ref"] == Pl.reference(inst, v["c"], 35)[0] and v["gap_mean"] > 0 and ev.gaps(v, v["loop"])[0] == pytest.approx((v["loop"].rounds[0].upper - v["ref"]) / v["ref"])
    big = ev.instance_data(ev.Settings("sparse", 12, 100000, 4, rounds=2))
    assert not big["exact"] and big["mean"] is None and big["gap_mean"] is None


def test_curves_and_pairs():
    s = ev.Settings("cluster", 8, 38, rounds=5)
    v = ev.instance_data(s)
    ac = ev.anchor_curve(s, v)
    assert [c["anchor"] for c in ac] == list(C.ANCHOR_CHOICES) and all(c["luT"] < c["lu0"] for c in ac) and [c["luT"] for c in ac] == sorted(c["luT"] for c in ac)[::-1]
    pair = ev.reweight_pair(s, v)
    assert [p["reweights"] for p in pair] == list(C.REWEIGHT_CHOICES) and all(p["gapT"] <= p["gap0"] + 1e-12 for p in pair)
    lc = ev.long_curve(s, v)
    assert list(lc["lu"]) == list(ev.CHECKPOINTS) and lc["lu"][120] < lc["lu"][0] and len(lc["loop"].rounds) == 121 and lc["changes"] == lc["loop"].changes


def test_row_of_and_summaries():
    rows = ev.sweep("sparse", 6, (100000, 100001, 100002), (2, 8))
    assert len(rows) == 6 and {r["p"] for r in rows} == {2, 8} and all(r["exact"] and r["ref"] > 0 for r in rows)
    r = rows[0]
    inst = I.make_instance("sparse", 6, 100000)
    pads = Pl.make_pads(inst, 2, 100000)
    c = Pl.linear_costs(inst, pads)
    lp = Lp.run_loop(inst, pads, c, "bisect", 15, 0, 0.2)
    assert r["ref"] == Pl.reference(inst, c, 100000)[0] and set(k for k in r if k[0] in "ab" and k[-1] in "02") == {f"{l}{w}" for l, w in ev.VARIANTS}
    assert r["bisect0"]["g0"] == pytest.approx((lp.rounds[0].upper - r["ref"]) / r["ref"]) and r["bisect0"]["gT"] == pytest.approx((lp.rounds[-1].upper - r["ref"]) / r["ref"]) and r["bisect0"]["changed"] == lp.changed
    sm = ev.variant_summary(rows, 2, "assign", 2)
    assert sm["count"] == 3 and sm["g0"] == float(np.median([x["assign2"]["g0"] for x in rows if x["p"] == 2])) and sm["changed"] <= 3 and sm["better"] + sm["worse"] <= sm["changed"]
    assert len(ev.pooled({"sparse": rows, "star": rows})) == 12 and len(ev.family_gaps(rows, 2, "assign", 2, "g0")) == 6
    assert ev.mean_gap(rows, 2) > 0


def test_long_rows():
    rows = ev.sweep_long("star", 6, (100000, 100001), 4)
    assert len(rows) == 2 and all(r["mono"] and list(r["lu"]) == list(ev.CHECKPOINTS) and r["lu"][120] < r["lu"][0] and r["changes"] >= 0 for r in rows)


def test_hand_data():
    a, b = ev.hand_anchor_data(), ev.hand_bisect_data()
    assert a["x"] == pytest.approx([3 / 58, 14 / 29, 123 / 58], abs=1e-5) and b["slots"] == [(0, 0), (0, 1), (1, 0), (1, 1)]
