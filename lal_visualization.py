"""Plotly-Abbildungen. Alle 2D-Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import lal_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380, legend_below=True):
    legend = dict(orientation="h", yanchor="top", y=-0.22, x=0) if legend_below else dict(orientation="h", yanchor="bottom", y=1.02, x=0)
    fig.update_layout(height=height + (40 if legend_below else 0), margin=dict(l=10, r=10, t=50, b=10), legend=legend, plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _extent(inst, pads, X):
    xs = [float(x) for x in inst.xy[:, 0]] + [float(x) for x in pads.pos[:, 0]] + [float(x) for x in X[:, 0]]
    ys = [-float(y) for y in inst.xy[:, 1]] + [-float(y) for y in pads.pos[:, 1]] + [-float(y) for y in X[:, 1]]
    return min(xs) - 0.6, max(xs) + 0.6, min(ys) - 0.6, max(ys) + 0.6


def build_positions(inst, pads, X, perm, title: str) -> go.Figure:
    """Plätze (graue Quadrate), Pads (Rauten) mit ihren Verbindungen, die stetigen Orte der Bauteile (Kreise) und, gestrichelt, der Platz, auf den die Rundung jedes Bauteil setzt."""
    fig = go.Figure()
    sx, sy = inst.xy[:, 0].astype(float), -inst.xy[:, 1].astype(float)
    fig.add_trace(go.Scatter(x=sx, y=sy, mode="markers", marker=dict(symbol="square", size=36, color="rgba(150,150,150,0.18)", line=dict(width=1, color="rgba(150,150,150,0.5)")), hoverinfo="skip", name="Plätze"))
    if pads.count:
        lx, ly = [], []
        for j in range(pads.count):
            for i in range(inst.n):
                if pads.w[i, j] > 0:
                    lx += [float(pads.pos[j, 0]), float(X[i, 0]), None]
                    ly += [-float(pads.pos[j, 1]), -float(X[i, 1]), None]
        fig.add_trace(go.Scatter(x=lx, y=ly, mode="lines", line=dict(width=1.2, color="rgba(176,138,46,0.5)"), hoverinfo="skip", name="Verbindung zum Pad"))
        fig.add_trace(go.Scatter(x=pads.pos[:, 0].astype(float), y=-pads.pos[:, 1].astype(float), mode="markers", marker=dict(symbol="diamond", size=14, color=C.COLORS["pad"]), name="Pads (fest)", hovertemplate="Pad<extra></extra>"))
    dx, dy = [], []
    for i in range(inst.n):
        dx += [float(X[i, 0]), float(sx[perm[i]]), None]
        dy += [-float(X[i, 1]), float(sy[perm[i]]), None]
    fig.add_trace(go.Scatter(x=dx, y=dy, mode="lines", line=dict(width=1, dash="dot", color="rgba(192,80,77,0.6)"), hoverinfo="skip", name="Rundung auf den Platz"))
    fig.add_trace(go.Scatter(x=X[:, 0].astype(float), y=-X[:, 1].astype(float), mode="markers+text", text=list(inst.names), textposition="top center", marker=dict(size=14, color=C.COLORS["cont"], line=dict(width=1, color="white")),
                             name="stetige Orte", hovertemplate="%{text}<extra></extra>"))
    x0, x1, y0, y1 = _extent(inst, pads, X)
    fig.update_layout(title=title)
    fig.update_xaxes(visible=False, range=[x0, x1], scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, range=[y0, y1])
    return _base(fig, height=360)


def build_arrangement(inst, perm, title: str) -> go.Figure:
    """Die gerundete Anordnung: Bauteile auf den Plätzen, Verbindungen mit Fluss als Linien."""
    fig = go.Figure()
    xs, ys = inst.xy[:, 0].astype(float), -inst.xy[:, 1].astype(float)
    pos = [(xs[int(perm[i])], ys[int(perm[i])]) for i in range(inst.n)]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", marker=dict(symbol="square", size=36, color="rgba(150,150,150,0.18)", line=dict(width=1, color="rgba(150,150,150,0.5)")), hoverinfo="skip", showlegend=False))
    fmax = max(1, int(inst.F.max()))
    lx, ly = [], []
    for a in range(inst.n):
        for b in range(a + 1, inst.n):
            if inst.F[a, b]:
                lx += [pos[a][0], pos[b][0], None]
                ly += [pos[a][1], pos[b][1], None]
    fig.add_trace(go.Scatter(x=lx, y=ly, mode="lines", line=dict(width=1.5, color="rgba(76,120,168,0.35)"), hoverinfo="skip", name="Fluss"))
    fig.add_trace(go.Scatter(x=[q[0] for q in pos], y=[q[1] for q in pos], mode="markers+text", text=list(inst.names), textposition="middle center", showlegend=False, marker=dict(size=26, color=C.COLORS["best"]), textfont=dict(color="white", size=10)))
    fig.update_layout(title=title)
    fig.update_xaxes(visible=False, range=[xs.min() - 0.7, xs.max() + 0.7], scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, range=[ys.min() - 0.7, ys.max() + 0.7])
    return _base(fig, height=300)


# ----------------------------------------------------------------------------- Kurven der Schleife

def build_loop_curve(loop, ref: float, title: str = "Obere Kosten und untere Länge je Runde") -> go.Figure:
    """Obere Kosten der legalen Anordnung (Treppe) und untere Länge der stetigen Lösung je Runde, dazu der Vergleichswert."""
    ts = [r.t for r in loop.rounds]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts, y=loop.uppers, mode="lines+markers", name="obere Kosten (legale Anordnung)", line=dict(color=C.COLORS["cont"], width=3, shape="hv"), marker=dict(size=5)))
    fig.add_trace(go.Scatter(x=ts, y=loop.lowers, mode="lines+markers", name="untere Länge (stetige Lösung)", line=dict(color="#4c78a8", width=3), marker=dict(size=5)))
    fig.add_trace(go.Scatter(x=[ts[0], ts[-1]], y=[ref, ref], mode="lines", name="Vergleichswert", line=dict(color=C.COLORS["best"], dash="dot", width=2)))
    fig.update_xaxes(title="Runde")
    fig.update_yaxes(title="Kosten bzw. Länge")
    fig.update_layout(title=title)
    return _base(fig, height=360)


def build_gap_curve(loops: dict, ref: float, names: dict) -> go.Figure:
    """Lücke zum Vergleichswert je Runde für jeden Legalisierer."""
    fig = go.Figure()
    colors = {"assign": "#2F6B65", "bisect": "#b08a2e"}
    for leg, lp in loops.items():
        fig.add_trace(go.Scatter(x=[r.t for r in lp.rounds], y=[100 * (u - ref) / ref for u in lp.uppers], mode="lines+markers", name=names[leg], line=dict(color=colors.get(leg, "#8e6bb0"), width=3, shape="hv"), marker=dict(size=5)))
    fig.update_xaxes(title="Runde")
    fig.update_yaxes(title="Lücke zum Vergleichswert (%)")
    fig.update_layout(title="Zuordnung und rekursive Zweiteilung")
    return _base(fig, height=340)


def build_anchor_bars(curve: list) -> go.Figure:
    """Lücke (oben − unten) / oben in Runde 0 und am Ende, je Ankergewicht c."""
    xs = [f"c = {c['anchor']:g}" for c in curve]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[100 * c["lu0"] for c in curve], name="Runde 0", marker_color="rgba(150,150,150,0.7)"))
    fig.add_trace(go.Bar(x=xs, y=[100 * c["luT"] for c in curve], name="letzte Runde", marker_color="#4c78a8"))
    fig.update_yaxes(title="Lücke oben/unten (%)")
    fig.update_layout(title="Ankergewicht und Annäherung", barmode="group")
    return _base(fig, height=320)


def build_sweep_bars(rows: list, median_of, summary, title: str) -> go.Figure:
    """Median der Lücke zum Optimum je Zahl der Pads: Runde 0 (einmalige Rundung) und letzte Runde der Schleife, Zuordnung und Zweiteilung, mit und ohne Umgewichtung."""
    ps = sorted({r["p"] for r in rows})
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[f"{p} Pads" for p in ps], y=[100 * summary(rows, p, "assign", 2)["g0"] for p in ps], name="Runde 0 (Zuordnung)", marker_color="rgba(150,150,150,0.7)"))
    for (leg, rw), col, name in ((("assign", 2), "#2F6B65", "Zuordnung, 2 Umgewichtungen"), (("assign", 0), "#9aa0a6", "Zuordnung, ohne Umgewichtung"), (("bisect", 2), "#b08a2e", "Zweiteilung, 2 Umgewichtungen")):
        fig.add_trace(go.Bar(x=[f"{p} Pads" for p in ps], y=[100 * summary(rows, p, leg, rw)["gT"] for p in ps], name=name, marker_color=col))
    fig.update_yaxes(title="Lücke nach der Rundung (%, Median)")
    fig.update_layout(title=title, barmode="group")
    return _base(fig, height=380)


def build_long_curve(rows: list, checkpoints, title: str) -> go.Figure:
    """Median der Lücke (oben − unten) / oben an den Prüfpunkten."""
    import numpy as np

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[str(k) for k in checkpoints], y=[100 * float(np.median([r["lu"][k] for r in rows])) for k in checkpoints], mode="lines+markers", name="Median", line=dict(color="#4c78a8", width=3)))
    fig.add_trace(go.Scatter(x=[str(k) for k in checkpoints], y=[100 * float(np.max([r["lu"][k] for r in rows])) for k in checkpoints], mode="lines", name="größte Instanz", line=dict(color="rgba(150,150,150,0.8)", dash="dot")))
    fig.update_xaxes(title="Runde")
    fig.update_yaxes(title="Lücke oben/unten (%)")
    fig.update_layout(title=title)
    return _base(fig, height=340)
