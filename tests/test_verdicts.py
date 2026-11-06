"""Verdikte (reine Funktionen in lal_evaluation.py) an handgesetzten Werten: Art, Schwellen und jede Zahl im Text (DEMO-PLAYBOOK §1b)."""

import numpy as np

import lal_loop as Lp
import lal_evaluation as ev


def _loop(uppers, lowers, perms=None, leg="assign", lam_step=0.4):
    perms = perms or [[0, 1, 2]] * len(uppers)
    rounds = tuple(Lp.Round(t, lam_step * t, np.zeros((3, 2)), perms[t], lowers[t], uppers[t], 1.0) for t in range(len(uppers)))
    return Lp.Loop(leg, 2, 0.2, rounds)


def _v(loop, ref=50.0, exact=True, mean=70.0, loops=None):
    inst = type("I", (), {"rows": 2, "cols": 4})()
    return {"inst": inst, "exact": exact, "ref": ref, "mean": mean, "gap_mean": (mean - ref) / ref if mean else None, "loop": loop, "loops": loops or {"assign": loop, "bisect": loop}}


def _row(p, a2=(0.10, 0.06), a0=(0.10, 0.10), b2=(0.09, 0.07), mean=0.3, ch=(True, False, True), better=(True, False), worse=(False, False), lu=(0.5, 0.4), exact=True):
    def var(g, changed, b, w):
        return {"g0": g[0], "gT": g[1], "better": b, "worse": w, "changed": changed, "lu0": lu[0], "luT": lu[1], "below": False, "last_change": 3}
    return {"family": "netlist", "p": p, "ref": 50.0, "exact": exact, "gap_mean": mean, "assign2": var(a2, ch[0], better[0], worse[0]), "assign0": var(a0, ch[1], better[1], worse[1]), "bisect2": var(b2, ch[2], True, False), "bisect0": var(b2, False, False, False)}


def test_loop_verdict_changed_unchanged_and_worse():
    s = ev.Settings("cluster", 8, 38, 4, 0.2, 3, 2, "assign")
    perms = [[0, 1, 2], [0, 1, 2], [1, 0, 2], [1, 0, 2]]
    lp = _loop([60, 60, 55, 55], [20, 24, 28, 31], perms)
    kind, text = ev.verdict_loop(s, _v(lp))
    assert kind == "success" and "Familie **Zwei Cluster**, 8 Bauteile, Raster 2×4, Seed 38, 4 Pads, Legalisierer Zuordnung, 3 Runden, c = 0,2, 2 Umgewichtungen je Runde" in text
    assert "ändert sich in 1 Runde (zuletzt in Runde 2)" in text and "sinken von 60 (Lücke 20,0 %) auf 55 (Lücke 10,0 %) gegen das aufgezählte Optimum 50" in text and "beste Runde: Kosten 55" in text
    assert "Untere Länge 20 → 31, Lücke zwischen oberen Kosten und unterer Länge 67 % → 44 %" in text
    same = _loop([60, 60, 60, 60], [20, 24, 28, 31])
    k2, t2 = ev.verdict_loop(s, _v(same))
    assert k2 == "info" and "**bleibt bis zur letzten Runde gleich**" in t2 and "halten sie fest" not in t2
    worse = _loop([55, 55, 60, 60], [20, 24, 28, 31], [[0, 1, 2], [0, 1, 2], [1, 0, 2], [1, 0, 2]])
    k3, t3 = ev.verdict_loop(s, _v(worse))
    assert k3 == "warning" and "steigen von 55 (Lücke 10,0 %) auf 60 (Lücke 20,0 %)" in t3
    assert "die beste von 100 Abstiegen (obere Grenze) 50" in ev.verdict_loop(s, _v(lp, exact=False, mean=None))[1]


def test_converge_and_legalizer_verdicts():
    s = ev.Settings(rounds=3)
    lp = _loop([60, 60, 55, 55], [20, 24, 28, 31], [[0, 1, 2], [0, 1, 2], [1, 0, 2], [1, 0, 2]])
    kind, text = ev.verdict_converge(s, _v(lp))
    assert kind == "info" and "steigt in jeder Runde (20 → 31)" in text and "(60 → 55)" in text and "sinkt von 67 % auf 44 %" in text and "Ankergewicht auf 1,2 wächst" in text and "eine bessere Anordnung trägt nur bei, wenn sich die Anordnung ändert" in text
    bad = _loop([60, 60, 55, 55], [20, 24, 22, 31])
    assert "steigt nicht in jeder Runde" in ev.verdict_converge(s, _v(bad))[1]
    other = _loop([55, 55, 55, 55], [20, 24, 28, 31], leg="bisect")
    text = ev.verdict_legalizers(s, _v(lp, loops={"assign": lp, "bisect": other}))[1]
    assert "Zuordnung: Runde 0 Kosten 60 (Lücke 20,0 %), nach 3 Runden 55 (Lücke 10,0 %), Anordnung ändert sich in 1 Runde" in text and "Rekursive Zweiteilung: Runde 0 Kosten 55 (Lücke 10,0 %), nach 3 Runden 55 (Lücke 10,0 %), Anordnung ändert sich in 0 Runden" in text


def test_anchor_reweight_and_long_verdicts():
    s = ev.Settings()
    curve = [{"anchor": 0.02, "gap0": 0.17, "gapT": 0.17, "changes": 0, "lu0": 0.52, "luT": 0.51}, {"anchor": 1.0, "gap0": 0.17, "gapT": 0.06, "changes": 1, "lu0": 0.52, "luT": 0.26}]
    text = ev.verdict_anchor(s, curve)[1]
    assert "c = 0,02: Lücke 17,0 % → 17,0 %, 0 Änderungen, Lücke oben/unten 52 % → 51 %; c = 1: Lücke 17,0 % → 6,0 %, 1 Änderungen, Lücke oben/unten 52 % → 26 %" in text and "Zuordnung, 15 Runden" in text
    pair = [{"reweights": 0, "gap0": 0.17, "gapT": 0.17, "changes": 0, "changed": False}, {"reweights": 2, "gap0": 0.17, "gapT": 0.06, "changes": 1, "changed": True}]
    text = ev.verdict_reweight(s, pair)[1]
    assert "ohne Umgewichtung Lücke 17,0 % → 17,0 % (Anordnung bleibt)" in text and "mit zwei Umgewichtungen je Runde 17,0 % → 6,0 % (Anordnung ändert sich; 1 Änderungen)" in text
    lc = {"lu": {0: 0.6, 5: 0.56, 15: 0.48, 30: 0.36, 60: 0.22, 120: 0.12}, "gapT": 0.055, "changes": 0, "last_change": 0}
    text = ev.verdict_long(s, lc)[1]
    assert "0: 60 %, 5: 56 %, 15: 48 %, 30: 36 %, 60: 22 %, 120: 12 %" in text and "ändert sich in 0 Runden (zuletzt in Runde 0)" in text and "am Ende 5,5 %" in text and "wachsenden Ankergewicht" in text


def test_sweep_verdicts():
    rows = [_row(2), _row(2), _row(4, a2=(0.09, 0.05), a0=(0.09, 0.09)), _row(4, a2=(0.09, 0.05), a0=(0.09, 0.09))]
    kind, text = ev.verdict_sweep(8, rows)
    assert kind == "info" and "Bei n = 8, Median der Lücke über 2 Instanzen je Zahl der Pads" in text and "2 Pads: 10,0 % → 6,0 % (Anordnung ändert sich in 2, wird besser in 2, schlechter in 0 von 2)" in text and "4 Pads: 9,0 % → 5,0 %" in text
    assert "Ohne Umgewichtung: 2 Pads: 10,0 % → 10,0 %; 4 Pads: 9,0 % → 9,0 %" in text and "obere Grenze" not in text
    assert "obere Grenze der Lücke" in ev.verdict_sweep(12, [_row(2, exact=False)])[1]
    text = ev.verdict_sweep_legalizers(rows)[1]
    assert "2 Pads: Zuordnung 10,0 % → 6,0 %, Zweiteilung 9,0 % → 7,0 % (Zweiteilung schlechter in 0)" in text
    lrows = [{"lu": {0: 0.6, 5: 0.5, 15: 0.4, 30: 0.3, 60: 0.2, 120: 0.1}, "changes": c, "gapT": 0.05, "mono": True} for c in (0, 0, 3)]
    text = ev.verdict_sweep_long(lrows)[1]
    assert "Über 3 Instanzen" in text and "0: 60 %, 5: 50 %, 15: 40 %, 30: 30 %, 60: 20 %, 120: 10 %" in text and "im Median in 0 Runden (höchstens 3)" in text and "am Ende 5,0 %" in text and "in 3 von 3 Instanzen in jeder Runde" in text


def test_core_verdict_quotes_the_numbers():
    s = ev.Settings(rounds=3)
    lp = _loop([60, 60, 55, 55], [20, 24, 28, 31])
    text = ev.verdict_core(s, _v(lp))[1]
    assert "Lücke 20,0 % → 10,0 % gegen das aufgezählte Optimum" in text and "Lücke zwischen oberen Kosten und unterer Länge 67 % → 44 %" in text and "Experiment 1 bis 5" in text
