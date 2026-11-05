"""Look-ahead-Legalisierung - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 10 der Reihe „Anordnen: relaxieren und runden“: die Platzierung mit festen Pads (Stück 9) wird in einer Schleife an ihre Legalisierung zurückgebunden (SimPL-artig): jedes Bauteil hängt mit wachsendem Gewicht an dem Platz, auf den es zuletzt gesetzt wurde.
Untere Länge und obere Kosten nähern sich, aber vor allem, weil das Ankergewicht wächst; die Anordnung verbessert sich nur in einem Teil der Instanzen. Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import lal_constants as C
from lal_evaluation import (
    CHECKPOINTS,
    Settings,
    anchor_curve,
    anchor_text,
    de,
    fam,
    hand_anchor_data,
    hand_bisect_data,
    instance_data,
    long_curve,
    lu_gap,
    mean_gap,
    median_of,
    num,
    pct,
    pooled,
    reweight_pair,
    rel,
    runden,
    sweep,
    sweep_long,
    variant_summary,
    verdict_anchor,
    verdict_converge,
    verdict_core,
    verdict_legalizers,
    verdict_long,
    verdict_loop,
    verdict_reweight,
    verdict_sweep,
    verdict_sweep_legalizers,
    verdict_sweep_long,
)
from lal_layout import dunkles_design, kopf_css
from lal_pdf_export import build_pdf
from lal_presets import bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sidebar_presets, sync_query_params
from lal_visualization import build_anchor_bars, build_gap_curve, build_long_curve, build_loop_curve, build_positions, build_sweep_bars

st.set_page_config(page_title="Look-ahead-Legalisierung – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner="Rechne die Schleife …")
def _instance(settings: Settings):
    return instance_data(settings)


@st.cache_data(show_spinner=False)
def _anchor(settings: Settings):
    return anchor_curve(settings, _instance(settings))


@st.cache_data(show_spinner=False)
def _reweight(settings: Settings):
    return reweight_pair(settings, _instance(settings))


@st.cache_data(show_spinner="Rechne 120 Runden …")
def _long(settings: Settings):
    return long_curve(settings, _instance(settings))


@st.cache_data(show_spinner=False)
def _sweep(family, n, seeds, pads_list):
    return sweep(family, n, seeds, pads_list)


@st.cache_data(show_spinner=False)
def _sweep_long(family, n, seeds):
    return sweep_long(family, n, seeds)


def verdict(pair):
    kind, text = pair
    getattr(st, kind)(text)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in lal_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🔁 Look-ahead-Legalisierung")
st.markdown(
    """
**Wie weit liegen untere und obere Werte der Platzierung auseinander, und bringt die Rückbindung an die Legalisierung etwas?** Dieselbe Aufgabe wie in Stück 1 bis 9: `n` Bauteile auf `n` Plätze, Kosten gleich der Summe aus **Fluss mal Abstand**, dazu **feste Pads**. Stück 9 hat die Bauteile an beliebigen Punkten platziert und **einmal** auf die Plätze gerundet.
Hier läuft das in einer **Schleife** (in der Art von SimPL): Runde für Runde setzt die **Legalisierung** jedes Bauteil auf einen Platz, und die nächste Platzierung hängt jedes Bauteil mit **wachsendem Gewicht** an diesen Platz (ein **Pseudo-Anker**). Die **untere Länge** ist die lineare Länge der stetigen Lösung, die **oberen Kosten** sind die der legalen Anordnung.
Zwei Legalisierer: die **Zuordnung** (kleinste Summe der Abstandsquadrate) und die **rekursive Zweiteilung** (Plätze teilen, Bauteile nach der Koordinate sortieren).
Die sechs Familien der Flussmatrix sind **eigene, einfache Erfindungen** (aus Stück 2), die **Pads ebenso**; die Schleife ist eine **eigene einfache Fassung**, nicht SimPL. Stück 10 der Reihe „Anordnen: relaxieren und runden“.

Weiter unten: **fünf Experimente** (**🔬**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert es", expanded=True):
    st.markdown(
        """
1. **Runde 0:** die quadratische Platzierung aus Stück 9 (lineares System je Achse mit den festen Pads, `0` oder `2` Umgewichtungen), dann die Legalisierung auf die Plätze.
2. **Runde t:** jedes Bauteil bekommt einen **Pseudo-Anker** an seinem Platz der Vorrunde mit dem Gewicht `λ_t = c · Grundgewicht · t`; das System wird mit den zusätzlichen Gliedern `λ_t · (x − Platz)²` neu gelöst und wieder legalisiert.
3. **Untere Länge, obere Kosten:** die lineare Länge der stetigen Lösung (ohne Pseudo-Anker) und die Kosten der legalen Anordnung. Beide sind **Näherungen**; die echte untere Schranke (das Minimum der linearen Länge über alle reellen Orte) liegt weit unter dem Optimum (siehe README).
4. **Warum nähern sich beide an?** Je größer `λ_t`, desto näher liegen die stetigen Orte an den Plätzen, also steigt die untere Länge zu den oberen Kosten: **das ist das Ankergewicht, nicht die Qualität der Anordnung.** Ob die Anordnung besser wird, zeigt die Lücke zum Vergleichswert.
5. **Die Lücke:** (Kosten − Vergleichswert) / Vergleichswert; bis n = 9 ist der Vergleichswert das aufgezählte Optimum, ab n = 12 die beste von 100 steilsten Abstiegen (obere Grenze der Lücke).
6. **Feste Instanzen:** Vergleiche laufen über feste Seeds (n = 8: 20 Instanzen je Familie, n = 12: 5), nie über einen einzelnen.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Die Instanz**")
    family = st.selectbox("Familie der Flussmatrix", C.FAMILIES, key="family_select", format_func=lambda f: C.FAMILY_NAMES[f], help="Wie der Fluss zwischen den Bauteilen verteilt ist. Die Beschreibung steht unter dem Regler.")
    st.caption(C.FAMILY_HELP[family])
    n = st.select_slider("Bauteile n", options=C.SIZES, key="n_select", help="Bis n = 9 wird alles aufgezählt (Vergleichswert: Optimum); ab n = 12 steht die beste von 100 steilsten Abstiegen an seiner Stelle.")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz", width="stretch", on_click=randomize_seed)
    pads_n = st.select_slider("Zahl der Pads", options=C.PAD_CHOICES, key="pads_select", help="Feste Anker auf dem Ring um das Raster (Gewicht: Grundgewicht, Median der positiven Flüsse).")
    st.markdown("**Die Schleife**")
    legalizer = st.selectbox("Legalisierer", C.LEGALIZERS, key="legalizer_select", format_func=lambda k: C.LEGALIZER_NAMES[k], help="Zuordnung: kleinste Summe der Abstandsquadrate. Rekursive Zweiteilung: die Plätze teilen und die Bauteile nach der Koordinate sortieren.")
    st.caption(C.LEGALIZER_HELP[legalizer])
    anchor = st.select_slider("Ankergewicht c", options=C.ANCHOR_CHOICES, key="anchor_select", format_func=lambda c: f"{c:g}", help="Die Pseudo-Anker haben in Runde t das Gewicht c · Grundgewicht · t.")
    rounds = st.select_slider("Runden", options=C.ROUND_CHOICES, key="rounds_select", help="Zahl der Runden nach Runde 0.")
    reweights = st.select_slider("Umgewichtungen je Runde", options=C.REWEIGHT_CHOICES, key="reweights_select", help="Wie oft das System je Runde mit Gewichten F / |Δ| neu gerechnet wird („Bound2Bound-artig“, Stück 9).")

sync_query_params({"family_select": family, "n_select": int(n), "seed_input": int(seed), "pads_select": int(pads_n), "anchor_select": float(anchor), "rounds_select": int(rounds), "reweights_select": int(reweights), "legalizer_select": legalizer})
settings = Settings(family, int(n), int(seed), int(pads_n), float(anchor), int(rounds), int(reweights), legalizer)

v = _instance(settings)
lp = v["loop"]
r0, rT = lp.rounds[0], lp.rounds[-1]
ref_label = "Optimum" if v["exact"] else "Beste gefundene Lösung"

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
m1, m2, m3 = st.columns(3)
m4, m5 = st.columns(2)
m1.metric("Lücke, Runde 0", pct(rel(r0.upper, v["ref"]), 1), delta=f"Kosten {num(r0.upper)}", delta_color="off", help="Kosten der Anordnung nach der Legalisierung der Platzierung ohne Pseudo-Anker (Stück 9), gegen den Vergleichswert.")
m2.metric(f"Lücke, Runde {settings.rounds}", pct(rel(rT.upper, v["ref"]), 1), delta=f"Kosten {num(rT.upper)}", delta_color="off", help="Dasselbe nach den Runden der Schleife.")
m3.metric("Lücke oben/unten", pct(lu_gap(rT.upper, rT.lower)), delta=f"Runde 0: {pct(lu_gap(r0.upper, r0.lower))}", delta_color="off", help="(obere Kosten − untere Länge) / obere Kosten in der letzten Runde; beide Werte sind Näherungen.")
m4.metric(ref_label, num(v["ref"]), help="Die kleinsten Kosten aller n! Anordnungen (aufgezählt)." if v["exact"] else "Die beste von 100 steilsten Abstiegen aus Zufallsstarts: eine obere Schranke des Optimums.")
m5.metric("Änderungen der Anordnung", str(lp.changes), delta=(f"zuletzt in Runde {lp.last_change}" if lp.changes else "die Anordnung bleibt"), delta_color="off", help="In wie vielen Runden sich die legale Anordnung gegenüber der Vorrunde ändert.")
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(build_positions(v["inst"], v["pads"], r0.X, r0.perm, f"Runde 0 (Kosten {num(r0.upper)})"), width="stretch", key="positions_first")
with c2:
    st.plotly_chart(build_positions(v["inst"], v["pads"], rT.X, rT.perm, f"Runde {settings.rounds} (Kosten {num(rT.upper)})"), width="stretch", key="positions_last")

if st.button("📄 PDF des aktuellen Ergebnisses erstellen", key="pdf_make"):
    st.session_state["pdf_made"] = (settings, build_pdf(settings, v))
made = st.session_state.get("pdf_made")
if made and made[0] == settings:
    st.download_button("⬇️ PDF herunterladen", data=made[1], file_name="look-ahead-legalisierung.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie weit liegen untere und obere Werte auseinander?")
verdict(verdict_core(settings, v))

st.markdown("---")

# --- Experiment 1 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Eine Runde mit Pseudo-Ankern")
st.caption("Die stetigen Orte (rot) in der gewählten Runde, ihre Pads (Rauten) und der Platz, auf den die Legalisierung jedes Bauteil setzt (gestrichelt). Je größer die Runde, desto kürzer die Striche: die Anker ziehen die Bauteile an die Plätze.")
shown = st.select_slider("Runde anzeigen", options=list(range(settings.rounds + 1)), value=min(1, settings.rounds), key=f"round_view_{settings.rounds}")
rs = lp.rounds[shown]
st.plotly_chart(build_positions(v["inst"], v["pads"], rs.X, rs.perm, f"Runde {shown}: Ankergewicht {de(rs.lam, 2)}, Verschiebung {de(rs.disp, 1)}, Kosten {num(rs.upper)}"), width="stretch", key="round_positions")
with st.expander("Handbeispiele zum Nachrechnen"):
    h = hand_anchor_data()
    b2 = hand_bisect_data()
    st.markdown(
        f"**Pseudo-Anker von Hand:** drei Bauteile auf einer Zeile (Plätze bei x = 0, 1, 2), Fluss A–B 5, B–C 1; Pads bei x = −1 (an A) und x = 3 (an C) mit Gewicht 2, dazu ein Pseudo-Anker mit Gewicht 1 an jedem Bauteil, auf dem Platz 0, 1, 2. Die Gleichungen: `8·x_A − 5·x_B = −2`, `7·x_B − 5·x_A − x_C = 1`, `4·x_C − x_B = 8`. "
        f"Von Hand: `29·x_B = 14`, also **x_A = 3/58 ≈ {de(h['x'][0], 3)}, x_B = 14/29 ≈ {de(h['x'][1], 3)}, x_C = 123/58 ≈ {de(h['x'][2], 3)}** (ohne die Pseudo-Anker lag x_B bei 3/11 ≈ 0,273: sie ziehen die Bauteile zu den Plätzen).\n\n"
        f"**Rekursive Zweiteilung von Hand:** vier Bauteile A, B, C, D auf dem 2×2-Raster an den stetigen Orten (0,2 | 0,1), (0,1 | 0,9), (0,9 | 0,2), (0,8 | 0,8). Die Spalten sind nicht kürzer als die Zeilen, also wird nach x geteilt: B (0,1) und A (0,2) gehen in die linke Spalte, D (0,8) und C (0,9) in die rechte. "
        f"In jeder Spalte entscheidet y: A (0,1) vor B (0,9), C (0,2) vor D (0,8). Ergebnis: A auf {b2['slots'][0]}, B auf {b2['slots'][1]}, C auf {b2['slots'][2]}, D auf {b2['slots'][3]} (Spalte, Zeile)."
    )

st.markdown("---")

# --- Experiment 2 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Die Schleife: untere Länge und obere Kosten")
st.caption("Je Runde die Kosten der legalen Anordnung (rot, eine Treppe: sie ändert sich nur, wenn sich die Anordnung ändert) und die untere Länge der stetigen Lösung (blau); gestrichelt der Vergleichswert.")
st.plotly_chart(build_loop_curve(lp, v["ref"]), width="stretch", key="loop_curve")
verdict(verdict_loop(settings, v))
verdict(verdict_converge(settings, v))

st.markdown("---")

# --- Experiment 3 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Die Legalisierer und der Vergleich über feste Instanzen")
st.caption("Die Lücke zum Vergleichswert je Runde für beide Legalisierer (gleiche Einstellungen); darunter, über feste Instanzen, Runde 0 gegen die letzte Runde.")
st.plotly_chart(build_gap_curve(v["loops"], v["ref"], C.LEGALIZER_NAMES), width="stretch", key="gap_curve")
verdict(verdict_legalizers(settings, v))
st.markdown(f"**Vergleich über feste Instanzen** (n = {C.SWEEP_N}, je Familie {len(C.SWEEP_SEEDS)} Instanzen, 2, 4 und 8 Pads, 15 Runden, c = 0,2, Optimum aufgezählt).")
if not st.session_state.get("sweep_ok"):
    st.info("Der Vergleich rechnet 6 Reihen zu je 20 Instanzen, drei Pad-Zahlen und vier Schleifen und dauert rund eine halbe Minute (auf Streamlit Cloud länger). Mit dem Knopf starten:")
    if st.button("⏱️ Vergleich rechnen (n = 8)", key="sweep_button"):
        bar = st.progress(0.0, text="Rechne die Familien …")
        for i, f in enumerate(C.FAMILIES):
            _sweep(f, C.SWEEP_N, C.SWEEP_SEEDS, C.PAD_CHOICES)
            bar.progress((i + 1) / len(C.FAMILIES), text=f"{C.FAMILY_NAMES[f]} fertig")
        st.session_state["sweep_ok"] = True
        st.rerun()
else:
    rows = pooled({f: _sweep(f, C.SWEEP_N, C.SWEEP_SEEDS, C.PAD_CHOICES) for f in C.FAMILIES})
    st.plotly_chart(build_sweep_bars(rows, median_of, variant_summary, f"Lücke nach der Rundung, n = {C.SWEEP_N}"), width="stretch", key="sweep_chart")
    table = []
    for p in C.PAD_CHOICES:
        a2, a0, b2s = variant_summary(rows, p, "assign", 2), variant_summary(rows, p, "assign", 0), variant_summary(rows, p, "bisect", 2)
        table.append({"Pads": p, "Runde 0 (Zuordnung)": pct(a2["g0"], 1), "Ende, Zuordnung, 2 Umgewichtungen": pct(a2["gT"], 1), "Ende, Zuordnung, ohne": pct(a0["gT"], 1), "Ende, Zweiteilung, 2 Umgewichtungen": pct(b2s["gT"], 1), "Zufall (mittlere Kosten)": pct(mean_gap(rows, p)),
                      "Anordnung ändert sich (Zuordnung, 2 Umgew.)": f"{a2['changed']} von {a2['count']}", "besser / schlechter": f"{a2['better']} / {a2['worse']}"})
    st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
    verdict(verdict_sweep(C.SWEEP_N, rows))
    verdict(verdict_sweep_legalizers(rows))

st.markdown("---")

# --- Experiment 4 ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Ankergewicht und Umgewichtung")
st.caption("Dieselbe Instanz mit c = 0,02 / 0,2 / 1: die Lücke zwischen oberen Kosten und unterer Länge in Runde 0 und am Ende. Darunter dieselbe Schleife ohne und mit Umgewichtung.")
ac = _anchor(settings)
st.plotly_chart(build_anchor_bars(ac), width="stretch", key="anchor_bars")
verdict(verdict_anchor(settings, ac))
verdict(verdict_reweight(settings, _reweight(settings)))

st.markdown("---")

# --- Experiment 5: Konvergenz und Grenze --------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Konvergenz und Grenze")
st.caption("Über 120 Runden: wie die Lücke zwischen oberen Kosten und unterer Länge schrumpft, und ob sich dabei die Anordnung noch ändert. Für die gewählte Instanz und über feste Instanzen (n = 8, je Familie zehn Instanzen, vier Pads), dazu n = 12.")
if st.button("⏱️ 120 Runden für die gewählte Instanz rechnen", key="long_button"):
    st.session_state["long_for"] = settings
if st.session_state.get("long_for") == settings:
    lc = _long(settings)
    st.plotly_chart(build_loop_curve(lc["loop"], v["ref"], "120 Runden: obere Kosten und untere Länge"), width="stretch", key="long_curve")
    verdict(verdict_long(settings, lc))
if not st.session_state.get("long_ok"):
    st.info("Der Vergleich über 60 Instanzen mit 120 Runden dauert rund eine halbe Minute (auf Streamlit Cloud länger). Mit dem Knopf starten:")
    if st.button("⏱️ Konvergenz über feste Instanzen rechnen", key="long_sweep_button"):
        bar = st.progress(0.0, text="Rechne die Familien …")
        for i, f in enumerate(C.FAMILIES):
            _sweep_long(f, C.SWEEP_N, C.SWEEP_SEEDS_SMALL)
            bar.progress((i + 1) / len(C.FAMILIES), text=f"{C.FAMILY_NAMES[f]} fertig")
        st.session_state["long_ok"] = True
        st.rerun()
else:
    lrows = pooled({f: _sweep_long(f, C.SWEEP_N, C.SWEEP_SEEDS_SMALL) for f in C.FAMILIES})
    st.plotly_chart(build_long_curve(lrows, CHECKPOINTS, f"Lücke oben/unten, n = {C.SWEEP_N}, vier Pads"), width="stretch", key="long_sweep_chart")
    verdict(verdict_sweep_long(lrows))
if not st.session_state.get("large_ok"):
    st.info(f"Der Vergleich für n = {C.LARGE_SWEEP_N} (je Familie {len(C.LARGE_SEEDS)} Instanzen, 2, 4 und 8 Pads, Vergleichswert: beste von {C.STARTS} Abstiegen) dauert rund eine halbe Minute (auf Streamlit Cloud länger). Mit dem Knopf starten:")
    if st.button(f"⏱️ Große Instanzen rechnen (n = {C.LARGE_SWEEP_N})", key="large_button"):
        bar = st.progress(0.0, text="Rechne die Familien …")
        for i, f in enumerate(C.FAMILIES):
            _sweep(f, C.LARGE_SWEEP_N, C.LARGE_SEEDS, C.PAD_CHOICES)
            bar.progress((i + 1) / len(C.FAMILIES), text=f"{C.FAMILY_NAMES[f]} fertig")
        st.session_state["large_ok"] = True
        st.rerun()
else:
    rows_big = pooled({f: _sweep(f, C.LARGE_SWEEP_N, C.LARGE_SEEDS, C.PAD_CHOICES) for f in C.FAMILIES})
    st.plotly_chart(build_sweep_bars(rows_big, median_of, variant_summary, f"Lücke nach der Rundung, n = {C.LARGE_SWEEP_N}"), width="stretch", key="large_chart")
    verdict(verdict_sweep(C.LARGE_SWEEP_N, rows_big))

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Pads sind erfunden** | Zahl, Ort, Gewicht und Verbindungen der Pads sind eigene Erfindungen (aus Stück 9); eine andere Ankeranordnung kann die Lücken ändern. | – |
| **Die sechs Familien sind erfunden** | Echte Platinen haben andere Strukturen; Aussagen über Familien gelten nur für diese. | – |
| **Pseudo-Anker am legalen Platz, Gewicht `c · Grundgewicht · t`** | SimPL setzt die Anker an gestreckte Orte und wählt das Gewicht anders; die Schleife hier ist eine eigene einfache Fassung. Die Aussage „die Anordnung friert ein“ gilt für diese Fassung. | – |
| **Die rekursive Zweiteilung ist keine nichtlineare Skalierung** | Weder die Skalierung von SimPL noch Abacus (zeilenweise Zuordnung) sind gebaut. | Matching-Linie |
| **Untere Länge und obere Kosten sind Näherungen** | Die untere Länge der angekerten Lösung ist keine Schranke; die echte untere Schranke (reelle Orte, ein LP je Achse) liegt weit unter dem Optimum und wird nur in den Tests gerechnet. | – |
| **Die Annäherung kommt vom Ankergewicht** | „Konvergenz“ ist hier kein Gütemaß: bei großem Gewicht sitzen die Bauteile fest auf ihren Plätzen, gleichgültig wie gut die Anordnung ist. | – |
| **Vergleichswert ab n = 12** | Die beste von 100 Abstiegen ist eine obere Grenze des Optimums, die Lücke eine obere Grenze der wahren Lücke. | – |
| **Keine Detailplatzierung** | Nach der Schleife wird nicht getauscht; ein Abstieg mit Vertauschungen (Stück 12) könnte die Anordnung weiter verbessern. | Stück 12 |
| **Wenige Instanzen** | n = 8: 20 Instanzen je Familie (Konvergenz: 10), n = 12: 5; kleine Unterschiede sind nicht belastbar. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Die Aufgabe und die Platzierung (wie in Stück 9).** Flüsse $F$, Plätze $s_1, \dots, s_n$, Pads $a_j$ mit Gewichten $w_{ij}$; Kosten einer Anordnung $\pi$: $\mathrm{cost}(\pi) = \sum_{i<k} F_{ik} \lVert s_{\pi_i} - s_{\pi_k} \rVert_1 + \sum_{i,j} w_{ij} \lVert s_{\pi_i} - a_j \rVert_1$.
Die quadratische Platzierung löst je Achse $(L + W)\,x = b$ mit der Laplace-Matrix $L$, den Pad-Gewichten $W = \mathrm{diag}(w\mathbf{1})$ und $b_i = \sum_j w_{ij} a_j$; ohne Pads fallen alle Bauteile auf einen Punkt.

**Pseudo-Anker.** Ist $\pi^{(t-1)}$ die legale Anordnung der Vorrunde, hängt in Runde $t$ jedes Bauteil $i$ mit dem Gewicht $\lambda_t = c \cdot g \cdot t$ ($g$ = Grundgewicht) an dem Platz $s_{\pi^{(t-1)}_i}$. Die Zielfunktion bekommt das Glied $\lambda_t \lVert x_i - s_{\pi^{(t-1)}_i} \rVert_2^2$, das System wird
$$(L + W + \lambda_t I)\,x = b + \lambda_t\, s_{\pi^{(t-1)}} .$$
Für $\lambda_t \to 0$ ist es das System von Stück 9, für $\lambda_t \to \infty$ gilt $x \to s_{\pi^{(t-1)}}$: die stetigen Orte fallen auf die Plätze der Vorrunde.

**Untere Länge, obere Kosten.** $\ell_t = \sum_{i<k} F_{ik} \lVert x_i - x_k \rVert_1 + \sum w_{ij} \lVert x_i - a_j \rVert_1$ (ohne die Pseudo-Anker) und $u_t = \mathrm{cost}(\pi^{(t)})$. Wegen $x \to s_{\pi}$ strebt $\ell_t \to u_t$ für große Gewichte: **die Lücke $(u_t - \ell_t)/u_t$ schrumpft durch das Gewicht**, nicht durch eine bessere Anordnung.
Die **echte** untere Schranke ist $\min_{x \in \mathbb{R}^{2n}} \sum F \lVert x_i - x_k \rVert_1 + \sum w \lVert x_i - a_j \rVert_1$ (ein LP je Achse); sie liegt unter den Kosten jeder Anordnung, weil die Plätze eine Teilmenge der Ebene sind.

**Rekursive Zweiteilung.** Der Block der Plätze (Zeilen × Spalten) wird entlang der längeren Seite (bei Gleichstand: der Spalten) in zwei Blöcke geteilt; die Bauteile werden nach der Koordinate in dieser Richtung sortiert (Koordinaten auf acht Stellen gerundet, Gleichstände: kleinere Nummer zuerst), die ersten so viele, wie der erste Block Plätze hat, gehen in ihn; rekursiv, bis ein Platz bleibt.

**Lücke.** $(\mathrm{cost} - U)/U$ mit dem Vergleichswert $U$ (aufgezähltes Optimum bis $n = 9$, sonst die beste von 100 steilsten Abstiegen: eine **obere** Grenze des Optimums).

**Literatur.** SimPL (Kim, Lee, Markov), Abacus (Spindler u. a.), Kraftwerk2 mit dem Bound2Bound-Netzmodell: Angaben aus der Fachliteratur übernommen, hier **nicht nachgelesen**; Selbstangaben der Autoren zur Güte werden nicht übernommen.
Die Pseudo-Anker im System, die Annäherung durch das Gewicht, die Zweiteilung und die LP-Schranke der reellen Orte sind **eigene** Herleitungen und werden durch Tests (Handrechnung, Aufzählung, `scipy`) geprüft. Die Zahlen dieser Demo sind eigene Rechnungen an eigenen, erfundenen Familien und Pads.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
