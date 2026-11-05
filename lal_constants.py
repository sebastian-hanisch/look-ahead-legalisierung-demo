"""Konstanten: Größen, Raster, Familien der Flussmatrix, feste Reihen der Experimente, Farben und Presets."""

EXACT_SIZES = (6, 8, 9)                               # alle n! Anordnungen werden aufgezählt: das Optimum ist bekannt
LARGE_SIZES = (12, 16)                                # nicht aufgezählt: die beste von 100 Abstiegen mit linearem Term ersetzt das Optimum
SIZES = EXACT_SIZES + LARGE_SIZES
DEFAULT_N = 8
SWEEP_N = 8                                           # Vergleiche über feste Instanzen mit aufgezähltem Optimum
LARGE_SWEEP_N = 12                                    # Vergleich gegen die beste gefundene Lösung
GRID = {6: (2, 3), 8: (2, 4), 9: (3, 3), 12: (3, 4), 16: (4, 4)}    # Plätze als Raster (Zeilen, Spalten), Abstand = Manhattan
SEED_MAX, DEFAULT_SEED = 999999, 38
SWEEP_SEEDS = tuple(range(100000, 100020))            # feste Instanzen: nie ein einzelner Seed als Befund
SWEEP_SEEDS_SMALL = SWEEP_SEEDS[:10]                  # lange Konvergenz: zehn Instanzen je Familie
LARGE_SEEDS = SWEEP_SEEDS[:5]                         # n = 12: fünf Instanzen je Familie
STARTS = 100                                          # Zahl der steilsten Abstiege aus Zufallsstarts für die beste gefundene Lösung (ab n = 12)

PAD_CHOICES = (2, 4, 8)                               # Zahl der festen Pads (Anker) auf dem Ring um das Raster (ohne Pads fällt alles auf einen Punkt: Stück 9)
DEFAULT_PADS = 4
PAD_LINKS = 2                                         # jedes Pad hängt an so vielen zufälligen Bauteilen
DEFAULT_FACTOR = 1.0                                  # Pad-Gewicht = Faktor · Grundgewicht (Median der positiven Flüsse, mindestens 1); fest
FACTOR_CHOICES = (0.25, 1.0, 4.0, 16.0)               # Faktoren auf das Pad-Gewicht, nur für Kern-Tests (aus Stück 9); in dieser Demo ist das Pad-Gewicht fest
EPS = 0.3                                             # untere Grenze der Länge in der Umgewichtung F / max(|Δ|, EPS) (in Platzabständen)
CENTER_ANCHOR = 1e-6                                  # schwacher Anker in der Mitte: Bauteile ohne Weg zu einem Pad fallen auf einen Punkt, das System bleibt lösbar
RING_MARGIN = 1.5                                     # Abstand des Pad-Rings vom Raster der Plätze (in Platzabständen)
TIE_DECIMALS = 8                                      # Stellen (relativ zum größten Betrag), auf die Abstandsquadrate und Koordinaten vor Zuordnung und Sortierung gerundet werden: Gleichstände rechnerunabhängig

ANCHOR_CHOICES = (0.02, 0.2, 1.0)                     # c im Gewicht der Pseudo-Anker λ_t = c · Grundgewicht · t
DEFAULT_ANCHOR = 0.2
ROUND_CHOICES = (5, 15, 30, 60, 120)                  # Zahl der Runden der Schleife
DEFAULT_ROUNDS = 15
LONG_ROUNDS = 120
REWEIGHT_CHOICES = (0, 2)                             # Umgewichtungen der echten Verbindungen je Runde („Bound2Bound-artig“)
DEFAULT_REWEIGHTS = 2
LEGALIZERS = ("assign", "bisect")                     # Zuordnung (kleinste Summe der Abstandsquadrate) oder rekursive Zweiteilung
DEFAULT_LEGALIZER = "assign"
LEGALIZER_NAMES = {"assign": "Zuordnung", "bisect": "Rekursive Zweiteilung"}
LEGALIZER_HELP = {"assign": "Lineare Zuordnung der stetigen Orte auf die Plätze: kleinste Summe der Abstandsquadrate (wie in Stück 9).",
                  "bisect": "Den Block der Plätze entlang der längeren Seite teilen, die Bauteile nach der Koordinate sortieren, den ersten Teil dem ersten Block geben; bis ein Platz bleibt."}

FAMILIES = ("netlist", "uniform", "sparse", "cluster", "star", "skewed")
DEFAULT_FAMILY = "cluster"
FAMILY_NAMES = {"netlist": "Netzliste", "uniform": "Gleichverteilt", "sparse": "Dünn besetzt", "cluster": "Zwei Cluster", "star": "Stern", "skewed": "Wenige starke Flüsse"}
FAMILY_HELP = {
    "netlist": "Netzliste aus Dreiergruppen (IC, Kondensator, Widerstand), jedes Paar in einem Netz zählt Fluss 1: die Familie aus Stück 1.",
    "uniform": "Jedes Paar von Bauteilen hat einen zufälligen Fluss von 0 bis 9, gleichverteilt: dichte Matrix ohne Struktur.",
    "sparse": "Nur drei von zehn Paaren haben Fluss (1 bis 9), die übrigen keinen: dünn besetzt ohne weitere Struktur.",
    "cluster": "Zwei Gruppen von Bauteilen: innerhalb einer Gruppe starker Fluss (8 bis 10), zwischen den Gruppen schwacher (0 bis 2).",
    "star": "Ein Bauteil (die Nabe) hat starken Fluss (1 bis 9) zu allen anderen; zwischen den übrigen höchstens 1.",
    "skewed": "Die Flüsse sind schief verteilt: viele Paare ohne oder mit kleinem Fluss, wenige mit sehr großem (bis 60).",
}

# Netzliste (wie in Stück 1 bis 5)
N_NETS_PER_COMPONENT = 1.5
NET_SIZES = (2, 3, 4)
NET_WEIGHTS = (5, 3, 2)
LOCAL_NET_PERCENT = 70
GROUP = 3
# Dünn besetzt, Cluster, Stern, schief (wie in Stück 2)
SPARSE_PERCENT = 30
UNIFORM_MAX = 9
CLUSTER_STRONG, CLUSTER_WEAK_MAX = 8, 2
SKEW_VALUES = (0, 1, 2, 4, 8, 16, 32, 60)
SKEW_WEIGHTS = (45, 22, 13, 8, 6, 3, 2, 1)           # ganzzahlige Gewichte (Summe 100), schweres Ende

HAND_FLOWS = ((0, 1, 5), (1, 2, 1))                   # Handbeispiel 1: drei Bauteile auf einer Zeile, Fluss A–B 5, B–C 1
HAND_GRID = (1, 3)
HAND_GAP_FLOWS = ((0, 2, 1), (0, 3, 1), (1, 2, 1), (1, 3, 1))   # Handbeispiel 3: vier Bauteile auf einer Zeile, A und B gegen C und D
HAND_GAP_GRID = (1, 4)
HAND_GRID_FLOWS = ((0, 1, 3), (0, 2, 1), (1, 3, 2), (2, 3, 4))  # Handbeispiel 2 (aus Stück 1): Raster 2×2
HAND_GRID_GRID = (2, 2)

COLORS = {"best": "#2F6B65", "local": "#c0504d", "pad": "#b08a2e", "cont": "#c0504d", "other": "rgba(150,150,150,0.6)", "line": "#4c78a8", "ok": "#2F6B65", "warn": "#b08a2e", "bad": "#b34a4a",
          "family": {"netlist": "#4c78a8", "uniform": "#9c755f", "sparse": "#b08a2e", "cluster": "#2F6B65", "star": "#8e6bb0", "skewed": "#c0504d"}}

_BASE = {"family": DEFAULT_FAMILY, "n": DEFAULT_N, "seed": DEFAULT_SEED, "pads": DEFAULT_PADS, "anchor": DEFAULT_ANCHOR, "rounds": DEFAULT_ROUNDS, "reweights": DEFAULT_REWEIGHTS, "legalizer": DEFAULT_LEGALIZER}
PRESETS = {
    "Standardfall: Zwei Cluster, Zuordnung": dict(_BASE),
    "Rekursive Zweiteilung": dict(_BASE, legalizer="bisect"),
    "Ohne Umgewichtung": dict(_BASE, reweights=0),
    "Schwache Anker": dict(_BASE, anchor=0.02),
    "Starke Anker": dict(_BASE, anchor=1.0),
    "Zwei Pads": dict(_BASE, pads=2),
    "Zwölf Bauteile": dict(_BASE, n=12),
}
PRESET_HELP = {
    "Standardfall: Zwei Cluster, Zuordnung": "Zwei Gruppen von Bauteilen (Familie aus Stück 2) mit acht Bauteilen, vier Pads, 15 Runden, Pseudo-Anker mit c = 0,2 und zwei Umgewichtungen je Runde; Legalisierer: Zuordnung.",
    "Rekursive Zweiteilung": "Derselbe Fall mit der Zweiteilung als Legalisierer: sie erhält die Reihenfolge der Bauteile entlang der Achsen.",
    "Ohne Umgewichtung": "Ohne Umgewichtung je Runde ändert die Schleife die Anordnung kaum: die Anker halten die erste Rundung fest.",
    "Schwache Anker": "Das Ankergewicht wächst langsam (c = 0,02): die untere Länge nähert sich den oberen Kosten kaum.",
    "Starke Anker": "Das Ankergewicht wächst schnell (c = 1): die Bauteile sitzen nach wenigen Runden auf ihren Plätzen.",
    "Zwei Pads": "Nur zwei feste Pads: die erste Rundung ist am schlechtesten, die Schleife gewinnt am meisten.",
    "Zwölf Bauteile": "Zwölf Bauteile auf dem 3×4-Raster: nicht aufzählbar; verglichen wird mit der besten von 100 steilsten Abstiegen (obere Grenze der Lücke).",
}


def n_text(n: int) -> str:
    """Anzahl mit Leerzeichen als Tausendertrenner: 362880 → „362 880“."""
    return f"{n:,}".replace(",", " ")


assert set(PRESETS) == set(PRESET_HELP) and set(FAMILY_NAMES) == set(FAMILIES) == set(FAMILY_HELP)
assert all(p["n"] in SIZES and p["family"] in FAMILIES and 0 <= p["seed"] <= SEED_MAX and p["pads"] in PAD_CHOICES and p["anchor"] in ANCHOR_CHOICES and p["rounds"] in ROUND_CHOICES and p["reweights"] in REWEIGHT_CHOICES and p["legalizer"] in LEGALIZERS for p in PRESETS.values())
assert all(r * c == n for n, (r, c) in GRID.items()) and sum(SKEW_WEIGHTS) == 100 and set(GRID) == set(SIZES)
