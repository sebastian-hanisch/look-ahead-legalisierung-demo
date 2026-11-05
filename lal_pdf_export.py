"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import lal_constants as C
from lal_evaluation import Settings, anchor_text, lu_gap, num, pct, rel

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "Δ": "Delta", "↔": "<->", "„": '"', "“": '"', "²": "2", "³": "3", "⁻": "-", "¹": "1", "½": "1/2", "⁴": "4", "λ": "lambda"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, v: dict) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Look-ahead-Legalisierung: Schleife mit Pseudo-Ankern"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    inst = v["inst"]
    how = "alle Anordnungen aufgezählt" if v["exact"] else "nicht aufgezählt, beste von 100 Abstiegen als Vergleich (obere Grenze)"
    pdf.multi_cell(0, 5, _s(f"Familie {C.FAMILY_NAMES[s.family]}, {s.n} Bauteile, {inst.rows}x{inst.cols}-Raster, Seed {s.seed}; {s.pads} Pads; Legalisierer {C.LEGALIZER_NAMES[s.legalizer]}; {s.rounds} Runden; c = {anchor_text(s.anchor)}; "
                            f"{s.reweights} Umgewichtungen je Runde; {how}. Eine Instanz, kein Befund über die Familie. Erfundene Pads, einfache Fassungen. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    lp = v["loop"]
    pdf.set_font("Helvetica", "B", 9)
    for w, h in ((22, "Runde"), (35, "Anker-Gewicht"), (35, "Untere Länge"), (35, "Obere Kosten"), (30, "Lücke zum Wert"), (30, "Lücke oben/unten")):
        pdf.cell(w, 6, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    idx = sorted({0, 1, 2, 5, 10, len(lp.rounds) - 1} & set(range(len(lp.rounds))))
    for i in idx:
        r = lp.rounds[i]
        pdf.cell(22, 5.5, str(r.t), border=1)
        pdf.cell(35, 5.5, _s(num(r.lam)), border=1)
        pdf.cell(35, 5.5, _s(num(r.lower)), border=1)
        pdf.cell(35, 5.5, _s(num(r.upper)), border=1)
        pdf.cell(30, 5.5, _s(pct(rel(r.upper, v["ref"]), 1)), border=1)
        pdf.cell(30, 5.5, _s(pct(lu_gap(r.upper, r.lower))), border=1)
        pdf.ln()
    pdf.ln(3)
    ref_name = "Optimum (aufgezählt)" if v["exact"] else "Beste gefundene Lösung (obere Grenze)"
    pdf.multi_cell(0, 5, _s(f"{ref_name}: {num(v['ref'])}. Die Anordnung ändert sich in {lp.changes} Runden (zuletzt in Runde {lp.last_change}). Untere Länge und obere Kosten sind Näherungen, keine Schranken."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Quelle: look-ahead-legalisierung-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
