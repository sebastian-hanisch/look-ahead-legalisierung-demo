"""Orakel (ORACLE-PLAYBOOK §5): `scipy` für das angekerte System, die Zuordnung und vor allem die **echte untere Schranke** (das Minimum der linearen Länge über alle reellen Orte, ein LP je Achse); die Aufzählung für das Optimum.
Ohne scipy (nur requirements-dev.txt; die App braucht scipy nicht) werden die Tests übersprungen."""

import numpy as np
import pytest

import lal_constants as C
import lal_instance as I
import lal_loop as Lp
import lal_place as Pl

sp = pytest.importorskip("scipy.optimize")


def lp_lower_bound(inst, pads) -> float:
    """Minimum von Σ_{i<k} F |Δ| + Σ w |Δ| über alle reellen Orte (beide Achsen unabhängig, je ein LP mit Hilfsvariablen t ≥ |Δ|): eine echte untere Schranke der Kosten jeder Anordnung."""
    n = inst.n
    F = np.asarray(inst.F, dtype=float)
    pairs = [(i, k) for i in range(n) for k in range(i + 1, n) if F[i, k] > 0]
    padl = [(i, j) for i in range(n) for j in range(pads.count) if pads.w[i, j] > 0]
    total = 0.0
    for ax in (0, 1):
        m = len(pairs) + len(padl)
        if m == 0:
            continue
        cvec = np.concatenate([np.zeros(n), [F[i, k] for i, k in pairs], [pads.w[i, j] for i, j in padl]])
        A, b = [], []
        for e, (i, k) in enumerate(pairs):
            for s in (1, -1):
                row = np.zeros(n + m)
                row[i], row[k], row[n + e] = s, -s, -1
                A.append(row)
                b.append(0.0)
        for e, (i, j) in enumerate(padl):
            a = pads.pos[j, ax]
            for s in (1, -1):
                row = np.zeros(n + m)
                row[i], row[n + len(pairs) + e] = s, -1
                A.append(row)
                b.append(s * a)
        res = sp.linprog(cvec, A_ub=np.array(A), b_ub=np.array(b), bounds=[(None, None)] * n + [(0, None)] * m, method="highs")
        total += float(res.fun)
    return total


def test_the_lp_bound_equals_a_hand_value(hand):
    """Drei Bauteile auf einer Zeile (A–B 5, B–C 1), Pads bei −1 (an A) und 3 (an C) mit Gewicht 2: A bei −1, C bei 3, B bei A oder C: 5·0 + 1·4 + 0 + 0 = 4 (B neben A: 5|x_B − x_A| + |x_C − x_B| + 2|x_A + 1| + 2|x_C − 3| = 4)."""
    w = np.zeros((3, 2))
    w[0, 0] = w[2, 1] = 2.0
    pads = Pl.Pads(np.array([[-1.0, 0.0], [3.0, 0.0]]), w, 2.0, 1.0)
    assert lp_lower_bound(hand, pads) == pytest.approx(4.0, abs=1e-7)


@pytest.mark.parametrize("family", C.FAMILIES)
def test_the_lp_bound_is_below_the_enumerated_optimum_and_below_the_continuous_length_of_every_round(family):
    for seed in (100008, 100009):
        inst = I.make_instance(family, 6, seed)
        for p in C.PAD_CHOICES:
            pads = Pl.make_pads(inst, p, seed)
            c = Pl.linear_costs(inst, pads)
            lb = lp_lower_bound(inst, pads)
            ref = Pl.reference(inst, c, seed)[0]
            assert lb <= ref + 1e-7
            assert lb <= Pl.continuous_length(inst, Pl.positions(inst, pads, 30), pads) + 1e-7                         # die Umgewichtung liegt über dem Minimum
            for leg in C.LEGALIZERS:
                lp = Lp.run_loop(inst, pads, c, leg, 6, 2, 0.2)
                assert all(r.lower >= lb - 1e-7 for r in lp.rounds) and all(r.upper >= ref - 1e-9 for r in lp.rounds)


def test_the_anchored_system_equals_scipy_least_squares():
    for fam in C.FAMILIES:
        inst = I.make_instance(fam, 8, 100010)
        pads = Pl.make_pads(inst, 4, 100010)
        anchors = inst.xy[[2, 4, 1, 7, 0, 3, 6, 5]].astype(float)
        lam = 0.9
        X = Lp.positions_anchored(inst, pads, anchors, lam)
        A = Pl.system_matrix(inst, pads) + (lam + C.CENTER_ANCHOR) * np.eye(8)
        center = inst.xy.astype(float).mean(axis=0)
        for ax in (0, 1):
            b = (pads.w * pads.pos[None, :, ax]).sum(axis=1) + lam * anchors[:, ax] + C.CENTER_ANCHOR * center[ax]
            assert X[:, ax] == pytest.approx(np.linalg.lstsq(A, b, rcond=None)[0], abs=1e-7)


def test_the_assignment_legalizer_equals_scipy_and_enumeration():
    rng = np.random.default_rng(5)
    from itertools import permutations

    for fam in C.FAMILIES:
        inst = I.make_instance(fam, 6, 100011)
        X = rng.uniform(-0.5, 3, size=(6, 2))
        perm = Lp.legalize(inst, X, "assign")
        d2 = ((X[:, None, :] - inst.xy[None, :, :].astype(float)) ** 2).sum(axis=2)
        r, cc = sp.linear_sum_assignment(d2)
        assert d2[np.arange(6), perm].sum() == pytest.approx(d2[r, cc].sum(), abs=1e-6)
        assert d2[np.arange(6), perm].sum() == pytest.approx(min(d2[np.arange(6), list(q)].sum() for q in permutations(range(6))), abs=1e-6)
        bis = Lp.legalize(inst, X, "bisect")
        assert d2[np.arange(6), bis].sum() >= d2[np.arange(6), perm].sum() - 1e-9                               # die Zuordnung ist für die Abstandsquadrate optimal


def test_the_loop_never_beats_the_enumerated_optimum():
    for fam in C.FAMILIES:
        inst = I.make_instance(fam, 6, 100012)
        for p in C.PAD_CHOICES:
            pads = Pl.make_pads(inst, p, 100012)
            c = Pl.linear_costs(inst, pads)
            ref = Pl.reference(inst, c, 100012)[0]
            for leg in C.LEGALIZERS:
                assert min(Lp.run_loop(inst, pads, c, leg, 10, 2, 0.2).uppers) >= ref - 1e-9


def test_the_lp_bound_gaps_at_eight_components_and_the_continuous_length_ratio():
    """Lücke der echten unteren Schranke zum aufgezählten Optimum (Median über 120 Instanzen je Pad-Zahl) und Länge der Umgewichtung (30 Schritte) im Verhältnis zur Schranke; nie darunter, nie über dem Optimum."""
    exp = {2: (67.2, 1.083), 4: (58.8, 1.067), 8: (32.8, 1.034)}
    for p, (gap, ratio) in exp.items():
        gaps, ratios = [], []
        for fam in C.FAMILIES:
            for seed in range(100000, 100020):
                inst = I.make_instance(fam, 8, seed)
                pads = Pl.make_pads(inst, p, seed)
                c = Pl.linear_costs(inst, pads)
                ref = Pl.reference(inst, c, seed)[0]
                lb = lp_lower_bound(inst, pads)
                length = Pl.continuous_length(inst, Pl.positions(inst, pads, 30), pads)
                assert lb <= ref + 1e-7 and length >= lb - 1e-7
                gaps.append((ref - lb) / ref)
                ratios.append(length / lb)
        assert 100 * float(np.median(gaps)) == pytest.approx(gap, abs=0.06) and float(np.median(ratios)) == pytest.approx(ratio, abs=0.0006), p
