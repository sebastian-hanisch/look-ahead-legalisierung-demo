"""Kennzahlen, Vergleiche über Instanzen und Verdikte. Jedes Verdikt ist eine reine Funktion (Art, Text); die App ruft st.<Art>(Text).

Alle Aussagen gelten für die gerechneten Instanzen, die sechs erfundenen Familien, die **erfundenen Pads** (Zahl, Ort, Gewicht, Verbindungen) und die **einfachen** Fassungen dieser Demo (Pseudo-Anker, Zuordnung, rekursive Zweiteilung); Zeiten stehen nie in Verdikten.
Die Lücke ist (Kosten − Vergleichswert) / Vergleichswert; der Vergleichswert ist bis n = 9 das aufgezählte Optimum, ab n = 12 die beste von 100 Abstiegen (die Lücke ist dann eine **obere** Grenze der wahren Lücke).
Die Lücke zwischen oberen Kosten und unterer Länge ist (obere Kosten − untere Länge) / obere Kosten; beide Werte sind Näherungen, keine Schranken."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import lal_constants as C
import lal_loop as Lp
import lal_place as Pl
from lal_instance import hand_instance, make_instance


@dataclass(frozen=True)
class Settings:
    family: str = C.DEFAULT_FAMILY
    n: int = C.DEFAULT_N
    seed: int = C.DEFAULT_SEED
    pads: int = C.DEFAULT_PADS
    anchor: float = C.DEFAULT_ANCHOR
    rounds: int = C.DEFAULT_ROUNDS
    reweights: int = C.DEFAULT_REWEIGHTS
    legalizer: str = C.DEFAULT_LEGALIZER


# ----------------------------------------------------------------------------- Formatierung

def de(x: float, digits: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma und typografischem Minuszeichen."""
    return f"{x:.{digits}f}".replace(".", ",").replace("-", "−")


def pct(x: float, digits: int = 0) -> str:
    return de(100.0 * x, digits) + " %"


def fam(name: str) -> str:
    return C.FAMILY_NAMES.get(name, name)


def num(x: float) -> str:
    """Ganze Zahl ohne Nachkommastelle, sonst eine Stelle: 27 / 27,5 / −12,1."""
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else de(x, 1)


def rel(a: float, b: float) -> float:
    """(a − b) / b; NaN, wenn b = 0; Rundungsreste unter 1e-12 werden zu 0."""
    if not b:
        return float("nan")
    r = (a - b) / b
    return 0.0 if abs(r) < 1e-12 else r


def median_of(rows: list, key: str) -> float:
    return float(np.median([r[key] for r in rows]))


def lu_gap(upper: float, lower: float) -> float:
    """(obere Kosten − untere Länge) / obere Kosten."""
    return (upper - lower) / upper if upper else float("nan")


def runden(k: int) -> str:
    return f"{k} Runde" if k == 1 else f"{k} Runden"


def anchor_text(c: float) -> str:
    return de(c, 2).rstrip("0").rstrip(",")


# ----------------------------------------------------------------------------- eine Instanz

def run(inst, pads, c, legalizer: str, rounds: int, reweights: int, anchor: float) -> Lp.Loop:
    return Lp.run_loop(inst, pads, c, legalizer, rounds, reweights, anchor)


def instance_data(s: Settings) -> dict:
    """Instanz, Pads, Vergleichswert und die Schleife mit beiden Legalisierern (gleiche Einstellungen); `loop` ist die mit dem gewählten Legalisierer."""
    inst = make_instance(s.family, s.n, s.seed)
    pads = Pl.make_pads(inst, s.pads, s.seed, C.DEFAULT_FACTOR)
    c = Pl.linear_costs(inst, pads)
    ref, perm_ref, exact, mean = Pl.reference(inst, c, s.seed)
    loops = {leg: run(inst, pads, c, leg, s.rounds, s.reweights, s.anchor) for leg in C.LEGALIZERS}
    return {"inst": inst, "pads": pads, "c": c, "ref": ref, "ref_perm": perm_ref, "exact": exact, "mean": mean, "gap_mean": rel(mean, ref) if mean is not None else None, "loops": loops, "loop": loops[s.legalizer]}


def gaps(v: dict, loop: Lp.Loop) -> list:
    """Lücke zum Vergleichswert je Runde."""
    return [rel(u, v["ref"]) for u in loop.uppers]


def anchor_curve(s: Settings, v: dict) -> list:
    """Für c = 0,02 / 0,2 / 1: Lücke der Runde 0 und der letzten Runde, Zahl der Änderungen, Lücke (oben − unten)."""
    out = []
    for c in C.ANCHOR_CHOICES:
        lp = run(v["inst"], v["pads"], v["c"], s.legalizer, s.rounds, s.reweights, c)
        out.append({"anchor": c, "gap0": rel(lp.rounds[0].upper, v["ref"]), "gapT": rel(lp.rounds[-1].upper, v["ref"]), "changes": lp.changes, "lu0": lu_gap(lp.rounds[0].upper, lp.rounds[0].lower), "luT": lu_gap(lp.rounds[-1].upper, lp.rounds[-1].lower)})
    return out


def reweight_pair(s: Settings, v: dict) -> list:
    """Dieselbe Schleife ohne und mit zwei Umgewichtungen je Runde."""
    out = []
    for rw in C.REWEIGHT_CHOICES:
        lp = run(v["inst"], v["pads"], v["c"], s.legalizer, s.rounds, rw, s.anchor)
        out.append({"reweights": rw, "gap0": rel(lp.rounds[0].upper, v["ref"]), "gapT": rel(lp.rounds[-1].upper, v["ref"]), "changes": lp.changes, "changed": lp.changed})
    return out


CHECKPOINTS = (0, 5, 15, 30, 60, 120)


def long_curve(s: Settings, v: dict) -> dict:
    """Die Schleife über 120 Runden: Lücke (oben − unten) an den Prüfpunkten, Lücke zum Vergleichswert am Ende, Änderungen der Anordnung."""
    lp = run(v["inst"], v["pads"], v["c"], s.legalizer, C.LONG_ROUNDS, s.reweights, s.anchor)
    return {"loop": lp, "lu": {k: lu_gap(lp.rounds[k].upper, lp.rounds[k].lower) for k in CHECKPOINTS}, "gapT": rel(lp.rounds[-1].upper, v["ref"]), "changes": lp.changes, "last_change": lp.last_change}


# ----------------------------------------------------------------------------- Zeilen für die Vergleiche

VARIANTS = (("assign", 2), ("assign", 0), ("bisect", 2), ("bisect", 0))


def row_of(family: str, n: int, seed: int, p: int, rounds: int = C.DEFAULT_ROUNDS, anchor: float = C.DEFAULT_ANCHOR) -> dict:
    """Eine Instanz: vier Schleifen (Zuordnung und Zweiteilung, mit zwei und ohne Umgewichtung); je Schleife Lücke der Runde 0 und der letzten Runde, Änderung der Anordnung, Lücke (oben − unten)."""
    inst = make_instance(family, n, seed)
    pads = Pl.make_pads(inst, p, seed, C.DEFAULT_FACTOR)
    c = Pl.linear_costs(inst, pads)
    ref, _, exact, mean = Pl.reference(inst, c, seed)
    row = {"family": family, "n": n, "seed": seed, "p": p, "ref": ref, "exact": exact, "gap_mean": rel(mean, ref) if mean is not None else float("nan")}
    for leg, rw in VARIANTS:
        lp = run(inst, pads, c, leg, rounds, rw, anchor)
        r0, rT = lp.rounds[0], lp.rounds[-1]
        row[f"{leg}{rw}"] = {"g0": rel(r0.upper, ref), "gT": rel(rT.upper, ref), "better": rT.upper < r0.upper - 1e-9, "worse": rT.upper > r0.upper + 1e-9, "changed": lp.changed, "lu0": lu_gap(r0.upper, r0.lower), "luT": lu_gap(rT.upper, rT.lower),
                                "below": min(lp.uppers) < ref - 1e-9, "last_change": lp.last_change}
    return row


def sweep(family: str, n: int, seeds, pads_list) -> list:
    return [row_of(family, n, s, p) for s in seeds for p in pads_list]


def long_row(family: str, n: int, seed: int, p: int) -> dict:
    """Eine Instanz über 120 Runden (Zuordnung, zwei Umgewichtungen, c = 0,2): Lücke (oben − unten) an den Prüfpunkten, Lücke zum Optimum am Ende, Änderungen der Anordnung."""
    inst = make_instance(family, n, seed)
    pads = Pl.make_pads(inst, p, seed, C.DEFAULT_FACTOR)
    c = Pl.linear_costs(inst, pads)
    ref = Pl.reference(inst, c, seed)[0]
    lp = run(inst, pads, c, "assign", C.LONG_ROUNDS, C.DEFAULT_REWEIGHTS, C.DEFAULT_ANCHOR)
    mono = all(lp.rounds[i + 1].lower >= lp.rounds[i].lower - 1e-9 for i in range(C.LONG_ROUNDS))
    return {"family": family, "n": n, "seed": seed, "p": p, "ref": ref, "lu": {k: lu_gap(lp.rounds[k].upper, lp.rounds[k].lower) for k in CHECKPOINTS}, "gapT": rel(lp.rounds[-1].upper, ref), "changes": lp.changes, "last_change": lp.last_change, "mono": mono}


def sweep_long(family: str, n: int, seeds, p: int = C.DEFAULT_PADS) -> list:
    return [long_row(family, n, s, p) for s in seeds]


def pooled(by_family: dict) -> list:
    return [r for f in C.FAMILIES if f in by_family for r in by_family[f]]


def variant_summary(rows: list, p: int, leg: str, rw: int) -> dict:
    rs = [r for r in rows if r["p"] == p]
    k = f"{leg}{rw}"
    return {"p": p, "count": len(rs), "g0": median_of([r[k] for r in rs], "g0"), "gT": median_of([r[k] for r in rs], "gT"), "better": sum(r[k]["better"] for r in rs), "worse": sum(r[k]["worse"] for r in rs),
            "changed": sum(r[k]["changed"] for r in rs), "lu0": median_of([r[k] for r in rs], "lu0"), "luT": median_of([r[k] for r in rs], "luT")}


def mean_gap(rows: list, p: int) -> float:
    return median_of([r for r in rows if r["p"] == p], "gap_mean")


def family_gaps(rows: list, p: int, leg: str, rw: int, key: str) -> list:
    return [median_of([r[f"{leg}{rw}"] for r in rows if r["family"] == f and r["p"] == p], key) for f in C.FAMILIES]


# ----------------------------------------------------------------------------- Verdikte

def _head(s: Settings, v: dict) -> str:
    inst = v["inst"]
    return f"Familie **{fam(s.family)}**, {s.n} Bauteile, Raster {inst.rows}×{inst.cols}, Seed {s.seed}, {s.pads} Pads"


def _refname(v: dict) -> str:
    return "das aufgezählte Optimum" if v["exact"] else "die beste von 100 Abstiegen (obere Grenze)"


def verdict_loop(s: Settings, v: dict):
    """Was die Schleife aus der ersten Rundung macht."""
    lp = v["loop"]
    r0, rT = lp.rounds[0], lp.rounds[-1]
    g0, gT = rel(r0.upper, v["ref"]), rel(rT.upper, v["ref"])
    best = min(lp.uppers)
    kind = "success" if rT.upper < r0.upper - 1e-9 else "info"
    head = f"{_head(s, v)}, Legalisierer {C.LEGALIZER_NAMES[s.legalizer]}, {s.rounds} Runden, c = {anchor_text(s.anchor)}, {s.reweights} Umgewichtungen je Runde"
    if not lp.changed:
        return "info", (f"{head}: die Anordnung der Runde 0 (Kosten {num(r0.upper)}, Lücke {pct(g0, 1)} gegen {_refname(v)} {num(v['ref'])}) **bleibt bis zur letzten Runde gleich**; die Pseudo-Anker halten sie fest. "
                        f"Untere Länge {num(r0.lower)} → {num(rT.lower)}, Lücke zwischen oberen Kosten und unterer Länge {pct(lu_gap(r0.upper, r0.lower))} → {pct(lu_gap(rT.upper, rT.lower))}.")
    txt = (f"{head}: die Anordnung ändert sich in {runden(lp.changes)} (zuletzt in Runde {lp.last_change}); die Kosten sinken von {num(r0.upper)} (Lücke {pct(g0, 1)}) auf {num(rT.upper)} (Lücke {pct(gT, 1)}) gegen {_refname(v)} {num(v['ref'])}"
           if rT.upper < r0.upper - 1e-9 else f"{head}: die Anordnung ändert sich in {runden(lp.changes)} (zuletzt in Runde {lp.last_change}); die Kosten steigen von {num(r0.upper)} (Lücke {pct(g0, 1)}) auf {num(rT.upper)} (Lücke {pct(gT, 1)}) gegen {_refname(v)} {num(v['ref'])}")
    return ("success" if kind == "success" else "warning"), txt + f"; beste Runde: Kosten {num(best)}. Untere Länge {num(r0.lower)} → {num(rT.lower)}, Lücke zwischen oberen Kosten und unterer Länge {pct(lu_gap(r0.upper, r0.lower))} → {pct(lu_gap(rT.upper, rT.lower))}."


def verdict_converge(s: Settings, v: dict):
    """Annäherung von unterer Länge und oberen Kosten in der gewählten Schleife."""
    lp = v["loop"]
    r0, rT = lp.rounds[0], lp.rounds[-1]
    mono = all(lp.rounds[i + 1].lower >= lp.rounds[i].lower - 1e-9 for i in range(len(lp.rounds) - 1))
    return "info", (f"Die untere Länge {'steigt in jeder Runde' if mono else 'steigt nicht in jeder Runde'} ({num(r0.lower)} → {num(rT.lower)}), die oberen Kosten ändern sich nur, wenn sich die Anordnung ändert ({num(r0.upper)} → {num(rT.upper)}): "
                    f"die Lücke zwischen beiden sinkt von {pct(lu_gap(r0.upper, r0.lower))} auf {pct(lu_gap(rT.upper, rT.lower))}, **weil das Ankergewicht auf {de(rT.lam, 1)} wächst und die Bauteile an ihre Plätze zieht**, nicht weil die Anordnung besser wird. "
                    f"Echte untere Schranke für diese Pads: das Minimum der linearen Länge über alle reellen Orte; sie liegt in den Messungen weit unter dem Optimum (README).")


def verdict_legalizers(s: Settings, v: dict):
    """Zuordnung gegen Zweiteilung (gleiche Einstellungen)."""
    parts = []
    for leg in C.LEGALIZERS:
        lp = v["loops"][leg]
        parts.append(f"{C.LEGALIZER_NAMES[leg]}: Runde 0 Kosten {num(lp.rounds[0].upper)} (Lücke {pct(rel(lp.rounds[0].upper, v['ref']), 1)}), nach {s.rounds} Runden {num(lp.rounds[-1].upper)} (Lücke {pct(rel(lp.rounds[-1].upper, v['ref']), 1)}), Anordnung ändert sich in {runden(lp.changes)}")
    return "info", f"{_head(s, v)}: " + "; ".join(parts) + f"; Vergleichswert {num(v['ref'])} ({_refname(v)})."


def verdict_anchor(s: Settings, curve: list):
    txt = "; ".join(f"c = {anchor_text(c['anchor'])}: Lücke {pct(c['gap0'], 1)} → {pct(c['gapT'], 1)}, {c['changes']} Änderungen, Lücke oben/unten {pct(c['lu0'])} → {pct(c['luT'])}" for c in curve)
    return "info", f"Gleiche Instanz, {C.LEGALIZER_NAMES[s.legalizer]}, {s.rounds} Runden, Ankergewicht λ_t = c · Grundgewicht · t: {txt}. Starke Anker nähern die beiden Werte schnell an und halten die erste Anordnung fest; schwache lassen sie weit auseinander."


def verdict_reweight(s: Settings, pair: list):
    a, b = pair
    return "info", (f"Gleiche Instanz, {C.LEGALIZER_NAMES[s.legalizer]}: ohne Umgewichtung Lücke {pct(a['gap0'], 1)} → {pct(a['gapT'], 1)} ({'Anordnung ändert sich' if a['changed'] else 'Anordnung bleibt'}), mit zwei Umgewichtungen je Runde {pct(b['gap0'], 1)} → {pct(b['gapT'], 1)} "
                    f"({'Anordnung ändert sich' if b['changed'] else 'Anordnung bleibt'}; {b['changes']} Änderungen). Eine Instanz, kein Befund über die Familie.")


def verdict_long(s: Settings, lc: dict):
    txt = ", ".join(f"{k}: {pct(lc['lu'][k])}" for k in CHECKPOINTS)
    return "info", (f"Lücke (obere Kosten − untere Länge) / obere Kosten nach 0 / 5 / 15 / 30 / 60 / 120 Runden: {txt}; die Anordnung ändert sich in {runden(lc['changes'])} (zuletzt in Runde {lc['last_change']}), Lücke zum Vergleichswert am Ende {pct(lc['gapT'], 1)}. "
                    "Die Annäherung kommt vom wachsenden Ankergewicht.")


def verdict_sweep(n: int, rows: list):
    """Vergleich über feste Instanzen: Schleife mit Zuordnung und Umgewichtung, Runde 0 gegen letzte Runde, je Zahl der Pads."""
    ps = sorted({r["p"] for r in rows})
    exact = rows[0]["exact"]
    parts = []
    for p in ps:
        a = variant_summary(rows, p, "assign", 2)
        parts.append(f"{p} Pads: {pct(a['g0'], 1)} → {pct(a['gT'], 1)} (Anordnung ändert sich in {a['changed']}, wird besser in {a['better']}, schlechter in {a['worse']} von {a['count']})")
    nr = "; ".join(f"{p} Pads: {pct(variant_summary(rows, p, 'assign', 0)['g0'], 1)} → {pct(variant_summary(rows, p, 'assign', 0)['gT'], 1)}" for p in ps)
    return "info", (f"Bei n = {n}, Median der Lücke über {variant_summary(rows, ps[0], 'assign', 2)['count']} Instanzen je Zahl der Pads, Zuordnung mit zwei Umgewichtungen je Runde, Runde 0 → Runde {C.DEFAULT_ROUNDS}: " + "; ".join(parts) + f". Ohne Umgewichtung: {nr}."
                    + ("" if exact else " Der Vergleichswert ist die beste von 100 Abstiegen: obere Grenze der Lücke."))


def verdict_sweep_legalizers(rows: list):
    ps = sorted({r["p"] for r in rows})
    txt = "; ".join(f"{p} Pads: Zuordnung {pct(variant_summary(rows, p, 'assign', 2)['g0'], 1)} → {pct(variant_summary(rows, p, 'assign', 2)['gT'], 1)}, Zweiteilung {pct(variant_summary(rows, p, 'bisect', 2)['g0'], 1)} → {pct(variant_summary(rows, p, 'bisect', 2)['gT'], 1)} "
                     f"(Zweiteilung schlechter in {variant_summary(rows, p, 'bisect', 2)['worse']})" for p in ps)
    return "info", f"Legalisierer im Vergleich (zwei Umgewichtungen je Runde, Median Runde 0 → Runde {C.DEFAULT_ROUNDS}): {txt}."


def verdict_sweep_long(rows: list):
    cps = ", ".join(f"{k}: {pct(median_of([{'x': r['lu'][k]} for r in rows], 'x'))}" for k in CHECKPOINTS)
    return "info", (f"Über {len(rows)} Instanzen (vier Pads, Zuordnung, zwei Umgewichtungen, c = 0,2), Median der Lücke (oben − unten) nach 0 / 5 / 15 / 30 / 60 / 120 Runden: {cps}; die Anordnung ändert sich im Median in {runden(int(np.median([r['changes'] for r in rows])))} (höchstens {max(r['changes'] for r in rows)}), "
                    f"Lücke zum Optimum am Ende {pct(median_of(rows, 'gapT'), 1)}; die untere Länge steigt in {sum(r['mono'] for r in rows)} von {len(rows)} Instanzen in jeder Runde.")


def verdict_core(s: Settings, v: dict):
    lp = v["loop"]
    r0, rT = lp.rounds[0], lp.rounds[-1]
    return "info", (f"Die Schleife legalisiert bei {_head(s, v)} in jeder Runde auf die Plätze und hängt die Bauteile mit wachsendem Gewicht an ihre Plätze: Lücke {pct(rel(r0.upper, v['ref']), 1)} → {pct(rel(rT.upper, v['ref']), 1)} gegen {_refname(v)}, "
                    f"Lücke zwischen oberen Kosten und unterer Länge {pct(lu_gap(r0.upper, r0.lower))} → {pct(lu_gap(rT.upper, rT.lower))}. Ob die Schleife die Anordnung wirklich verbessert, ob die Legalisierer sich unterscheiden und wie schnell sich die Werte annähern: Experiment 1 bis 5.")


# ----------------------------------------------------------------------------- Handbeispiele

def hand_anchor_data() -> dict:
    """Drei Bauteile auf einer Zeile (Fluss A–B 5, B–C 1), Pads bei x = −1 (an A) und x = 3 (an C) mit Gewicht 2, dazu Pseudo-Anker am Platz 0, 1, 2 mit Gewicht 1: die Lösung von Hand (x_A = 3/58, x_B = 14/29, x_C = 123/58)."""
    inst = hand_instance()
    w = np.zeros((3, 2))
    w[0, 0] = w[2, 1] = 2.0
    pads = Pl.Pads(np.array([[-1.0, 0.0], [3.0, 0.0]]), w, 2.0, 1.0)
    X = Lp.positions_anchored(inst, pads, inst.xy.astype(float), 1.0, 0)
    return {"inst": inst, "pads": pads, "x": [float(x) for x in X[:, 0]]}


def hand_bisect_data() -> dict:
    """Vier Bauteile auf dem 2×2-Raster an den stetigen Orten (0,2 | 0,1), (0,1 | 0,9), (0,9 | 0,2), (0,8 | 0,8): die Zweiteilung teilt nach x (A, B links), dann nach y."""
    from lal_constants import HAND_GRID_FLOWS, HAND_GRID_GRID

    inst = hand_instance(HAND_GRID_FLOWS, *HAND_GRID_GRID)
    X = np.array([[0.2, 0.1], [0.1, 0.9], [0.9, 0.2], [0.8, 0.8]])
    perm = Lp.bisect_legalize(inst, X)
    return {"inst": inst, "x": X, "perm": perm, "slots": [tuple(int(c) for c in inst.xy[p]) for p in perm]}
