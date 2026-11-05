"""Die Zahlen der README (Abschnitte „Befunde“ und „Grenzen“) als Tests: Standardfall, Handbeispiele und die Vergleiche über feste Instanzen.
Prozentwerte auf eine Stelle (Toleranz 0,05), Zählungen exakt, je Familie auf ganze Prozent gerundet (Toleranz 0,51); Zeiten stehen nie in Tests (DEMO-PLAYBOOK §1b, Wiederholbarkeit)."""

import numpy as np
import pytest

import lal_constants as C
import lal_evaluation as ev


def pc(x):
    return 100 * x


@pytest.fixture(scope="module")
def standard():
    s = ev.Settings()
    return s, ev.instance_data(s)


@pytest.fixture(scope="module")
def sweep8():
    return ev.pooled({f: ev.sweep(f, C.SWEEP_N, C.SWEEP_SEEDS, C.PAD_CHOICES) for f in C.FAMILIES})


@pytest.fixture(scope="module")
def long8():
    return ev.pooled({f: ev.sweep_long(f, C.SWEEP_N, C.SWEEP_SEEDS_SMALL) for f in C.FAMILIES})


@pytest.fixture(scope="module")
def sweep12():
    return ev.pooled({f: ev.sweep(f, C.LARGE_SWEEP_N, C.LARGE_SEEDS, C.PAD_CHOICES) for f in C.FAMILIES})


def test_standard_instance_numbers(standard):
    s, v = standard
    assert (s.family, s.n, s.seed, s.pads, s.anchor, s.rounds, s.reweights, s.legalizer) == ("cluster", 8, 38, 4, 0.2, 15, 2, "assign") and v["exact"] and v["ref"] == 226.0
    a, b = v["loops"]["assign"], v["loops"]["bisect"]
    assert a.uppers == [265.0] * 12 + [240.0] * 4 and a.changes == 1 and a.last_change == 12 and b.uppers == [240.0] * 16 and b.changes == 0
    assert pc(ev.gaps(v, a)[0]) == pytest.approx(17.3, abs=0.05) and pc(ev.gaps(v, a)[-1]) == pytest.approx(6.2, abs=0.05) and pc(v["gap_mean"]) == pytest.approx(36.3, abs=0.05)
    assert a.lowers[0] == pytest.approx(52.1, abs=0.05) and a.lowers[-1] == pytest.approx(67.0, abs=0.05) and pc(ev.lu_gap(a.uppers[0], a.lowers[0])) == pytest.approx(80.3, abs=0.05) and pc(ev.lu_gap(a.uppers[-1], a.lowers[-1])) == pytest.approx(72.1, abs=0.05)
    assert all(a.lowers[i + 1] > a.lowers[i] for i in range(15))


def test_standard_instance_curves(standard):
    s, v = standard
    exp = {0.02: (17.3, 17.3, 0, 79.8), 0.2: (17.3, 6.2, 1, 72.1), 1.0: (17.3, 6.2, 1, 53.1)}
    for c in ev.anchor_curve(s, v):
        g0, gT, ch, luT = exp[c["anchor"]]
        assert pc(c["gap0"]) == pytest.approx(g0, abs=0.05) and pc(c["gapT"]) == pytest.approx(gT, abs=0.05) and c["changes"] == ch and pc(c["luT"]) == pytest.approx(luT, abs=0.05) and pc(c["lu0"]) == pytest.approx(80.3, abs=0.05)
    a, b = ev.reweight_pair(s, v)
    assert (a["reweights"], b["reweights"]) == (0, 2) and pc(a["gap0"]) == pytest.approx(28.8, abs=0.05) and not a["changed"] and a["gap0"] == a["gapT"] and pc(b["gap0"]) == pytest.approx(17.3, abs=0.05) and pc(b["gapT"]) == pytest.approx(6.2, abs=0.05) and b["changes"] == 1
    lc = ev.long_curve(s, v)
    assert [round(pc(lc["lu"][k]), 1) for k in ev.CHECKPOINTS] == pytest.approx([80.3, 78.7, 72.1, 65.3, 56.6, 42.5], abs=0.051) and pc(lc["gapT"]) == pytest.approx(6.2, abs=0.05) and (lc["changes"], lc["last_change"]) == (1, 12)


def test_hand_examples():
    a, b = ev.hand_anchor_data(), ev.hand_bisect_data()
    assert a["x"] == pytest.approx([3 / 58, 14 / 29, 123 / 58], abs=1e-5) and b["slots"] == [(0, 0), (0, 1), (1, 0), (1, 1)]


def test_n8_sweep_counts_and_pooled_gaps(sweep8):
    assert len(sweep8) == 360 and all(r["exact"] for r in sweep8) and not any(r[f"{l}{w}"]["below"] for r in sweep8 for l, w in ev.VARIANTS)
    exp = {  # p: {(Legalisierer, Umgewichtungen): (g0, gT, besser, schlechter, geändert)}
        2: {("assign", 2): (14.5, 10.8, 42, 0, 44), ("assign", 0): (14.1, 10.4, 31, 0, 31), ("bisect", 2): (11.6, 9.7, 32, 0, 33), ("bisect", 0): (11.7, 10.3, 20, 1, 21)},
        4: {("assign", 2): (8.8, 6.3, 22, 0, 23), ("assign", 0): (9.3, 9.2, 4, 1, 5), ("bisect", 2): (9.1, 6.2, 23, 5, 28), ("bisect", 0): (9.7, 9.1, 10, 1, 11)},
        8: {("assign", 2): (4.4, 3.6, 10, 0, 10), ("assign", 0): (6.2, 5.9, 2, 0, 2), ("bisect", 2): (4.3, 3.5, 13, 2, 15), ("bisect", 0): (6.3, 6.3, 1, 0, 1)},
    }
    for p, d in exp.items():
        for (leg, rw), (g0, gT, better, worse, changed) in d.items():
            sm = ev.variant_summary(sweep8, p, leg, rw)
            assert sm["count"] == 120 and pc(sm["g0"]) == pytest.approx(g0, abs=0.051) and pc(sm["gT"]) == pytest.approx(gT, abs=0.051), (p, leg, rw)
            assert (sm["better"], sm["worse"], sm["changed"]) == (better, worse, changed), (p, leg, rw)
    assert [round(pc(ev.mean_gap(sweep8, p)), 1) for p in C.PAD_CHOICES] == pytest.approx([38.1, 34.5, 26.1], abs=0.051)


def test_n8_gap_between_upper_and_lower_after_15_rounds(sweep8):
    for p, (lu0, luT) in {2: (68.4, 52.7), 4: (59.5, 47.3), 8: (33.5, 25.5)}.items():
        sm = ev.variant_summary(sweep8, p, "assign", 2)
        assert pc(sm["lu0"]) == pytest.approx(lu0, abs=0.06) and pc(sm["luT"]) == pytest.approx(luT, abs=0.06), p
    # die Anordnung der Runde 0 ist in 78 / 98 / 110 von 120 Instanzen die der Runde 15 (Zuordnung, zwei Umgewichtungen)
    assert [sum(not r["assign2"]["changed"] for r in sweep8 if r["p"] == p) for p in C.PAD_CHOICES] == [76, 97, 110]


def test_n8_per_family_for_the_assignment_loop(sweep8):
    """Zuordnung mit zwei Umgewichtungen, Runde 0 → Runde 15, je Familie auf ganze Prozent gerundet (Toleranz 0,51)."""
    g0 = {2: (14, 9, 19, 15, 11, 29), 4: (11, 6, 10, 6, 7, 11), 8: (6, 3, 2, 1, 6, 6)}
    gT = {2: (12, 9, 16, 2, 11, 14), 4: (11, 6, 9, 4, 7, 9), 8: (6, 3, 2, 0, 4, 6)}
    for p in C.PAD_CHOICES:
        for f, x0, xT, a, b in zip(C.FAMILIES, g0[p], gT[p], ev.family_gaps(sweep8, p, "assign", 2, "g0"), ev.family_gaps(sweep8, p, "assign", 2, "gT")):
            assert pc(a) == pytest.approx(x0, abs=0.51) and pc(b) == pytest.approx(xT, abs=0.51), (p, f)


def test_long_convergence_over_sixty_instances(long8):
    assert len(long8) == 60 and all(r["lu"][120] < r["lu"][0] for r in long8)
    assert [round(pc(float(np.median([r["lu"][k] for r in long8])))) for k in ev.CHECKPOINTS] == [60, 56, 48, 36, 22, 12]
    assert int(np.median([r["changes"] for r in long8])) == 0 and max(r["changes"] for r in long8) == 3 and max(r["last_change"] for r in long8) == 5 and sum(r["mono"] for r in long8) == 59
    assert pc(float(np.median([r["gapT"] for r in long8]))) == pytest.approx(5.5, abs=0.06)
    assert sum(r["changes"] == 0 for r in long8) >= 40


def test_n12_beyond_enumeration(sweep12):
    assert len(sweep12) == 90 and not any(r["exact"] for r in sweep12)
    exp = {2: {("assign", 2): (26.3, 10.6, 21, 1, 22), ("assign", 0): (21.4, 16.6, 9, 0, 10), ("bisect", 2): (24.5, 14.0, 16, 0, 16), ("bisect", 0): (23.7, 20.6, 11, 0, 11)},
           4: {("assign", 2): (11.8, 10.6, 7, 0, 7), ("assign", 0): (10.4, 10.4, 4, 0, 4), ("bisect", 2): (14.4, 11.0, 12, 2, 14), ("bisect", 0): (10.2, 8.8, 4, 1, 5)},
           8: {("assign", 2): (7.0, 5.9, 9, 0, 9), ("assign", 0): (8.8, 8.4, 1, 0, 1), ("bisect", 2): (6.4, 6.2, 4, 4, 8), ("bisect", 0): (11.3, 11.3, 4, 0, 4)}}
    for p, d in exp.items():
        for (leg, rw), (g0, gT, better, worse, changed) in d.items():
            sm = ev.variant_summary(sweep12, p, leg, rw)
            assert sm["count"] == 30 and pc(sm["g0"]) == pytest.approx(g0, abs=0.051) and pc(sm["gT"]) == pytest.approx(gT, abs=0.051), (p, leg, rw)
            assert (sm["better"], sm["worse"], sm["changed"]) == (better, worse, changed), (p, leg, rw)
