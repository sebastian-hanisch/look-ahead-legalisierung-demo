# Look-ahead-Legalisierung – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-look-ahead-legalisierung-demo.streamlit.app/)** -->

Stück 10 von 15 der **Konzepte-Reihe „Anordnen: relaxieren und runden“** für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (die Konzepte-Seite der Reihe gibt es noch nicht). [Stück 9, Quadratische Platzierung](https://github.com/sebastian-hanisch/quadratische-platzierung-demo), hat die Bauteile an beliebigen Punkten platziert und **einmal** auf die Plätze gerundet. Dieses Stück bindet die Rundung **in einer Schleife** an die Platzierung zurück (Kante der Reihe: *fix*, in der Art von SimPL): Runde für Runde legalisiert eine Zuordnung oder eine rekursive Zweiteilung die Bauteile auf Plätze, und die nächste Platzierung hängt jedes Bauteil mit **wachsendem Gewicht** an seinen Platz. Gefragt ist: wie weit liegen die **untere Länge** der stetigen Platzierung und die **oberen Kosten** der legalen Anordnung auseinander, und bringt die Schleife etwas?

## Warum dieses Problem

Eine Platzierung ohne Legalität (alle Bauteile an beliebigen Punkten) ist billig zu rechnen und liefert eine **untere Länge**; die legale Anordnung auf den Plätzen liefert **obere Kosten**. Wenn die Schleife beides gegeneinander laufen lässt, schrumpft die Lücke dazwischen: das sieht aus wie Konvergenz zum Optimum. Die Kernfrage: **was sagt diese Lücke, und wird die Anordnung durch die Schleife besser?**

Die Antwort dieser Messung: Die untere Länge steigt in jeder Runde und nähert sich den oberen Kosten, aber **vor allem, weil das Ankergewicht wächst** und die Bauteile an ihre Plätze zieht (Lücke im Median 60 % in Runde 0, 12 % nach 120 Runden); die Anordnung ändert sich dabei im Median **nie**. Die Schleife verbessert die Anordnung in einem Teil der Instanzen (bei zwei Pads in 42 von 120, die Lücke zum Optimum sinkt im Median von 14,5 auf 10,8 %), **wenn die Umgewichtung mitläuft**, und wird bei `n = 8` in keiner Instanz schlechter als die einmalige Rundung (Zuordnung; bei `n = 12` in einer von 90). Die **echte** untere Schranke (das Minimum der linearen Länge über alle reellen Orte) liegt weit unter dem Optimum (Lücke 67 / 59 / 33 %). Das sind **Befunde an sechs erfundenen Familien, erfundenen Pads und einfachen Eigenfassungen**, keine Sätze.

## Modell

- **Aufgabe** (wie in Stück 9): `n` Bauteile auf `n` Plätze eines Rasters (Manhattan-Abstand), dazu `p` **feste Pads** auf einem Ring um das Raster; jedes Pad hängt mit dem Grundgewicht (Median der positiven Flüsse, mindestens 1) an zwei zufälligen Bauteilen. `cost(p) = Σ_{i<k} F[i,k] · |p_i − p_k|₁ + Σ_{i,Pad} w · |p_i − Pad|₁`. Kern (Kosten, Aufzählung, Zufall, sechs Familien der Flussmatrix, Ungarische Methode, Pads, lineares System, Umgewichtung, Rundung, Abstieg) als Kopie aus Stück 9 (`lal_place.py`, `lal_cost.py`, `lal_landscape.py`, `lal_rng.py`, `lal_instance.py`, `lal_assignment.py`; Tests vergleichen die Instanzen mit den Schwester-Repos, wenn sie nebenan liegen). Die Familien und die Pads sind **eigene, einfache Erfindungen**, keine echten Platinen und keine QAPLIB-Instanzen.
- **Pseudo-Anker** (`lal_loop.py`): in Runde `t ≥ 1` hängt jedes Bauteil mit dem Gewicht `λ_t = c · Grundgewicht · t` an dem Platz, auf den die Legalisierung der Vorrunde es gesetzt hat; das System wird `(L + diag(W) + λ_t I) x = b + λ_t · Platz` je Achse neu gelöst (Umgewichtung der echten Verbindungen je Runde: 0 oder 2 Schritte, „Bound2Bound-artig“ aus Stück 9). Runde 0 ist die Platzierung ohne Pseudo-Anker (Stück 9).
- **Legalisierer:** die **Zuordnung** (kleinste Summe der Abstandsquadrate, Ungarische Methode) und die **rekursive Zweiteilung** (eigene Fassung der Look-ahead-Idee: den Block der Plätze entlang der längeren Seite teilen, die Bauteile nach der Koordinate sortieren, den ersten Teil dem ersten Block geben, bis ein Platz bleibt). Koordinaten und Abstandsquadrate werden vor dem Sortieren bzw. der Zuordnung auf acht Stellen gerundet (`tie_quantized`), damit Gleichstände auf jedem Rechner gleich entschieden werden. Das ist **nicht** die nichtlineare Skalierung von SimPL und nicht Abacus.
- **Untere Länge, obere Kosten:** untere Länge = lineare Länge der angekerten stetigen Lösung (ohne die Pseudo-Anker); obere Kosten = Kosten der legalen Anordnung. Beide sind **Näherungen**. Die **echte** untere Schranke ist das Minimum der linearen Länge über alle reellen Orte (ein LP je Achse, in den Tests mit `scipy.optimize.linprog` gerechnet, nicht zur Laufzeit).
- **Lücke und Vergleichswert:** `(Kosten − Vergleichswert) / Vergleichswert`; bis `n = 9` ist der Vergleichswert das aufgezählte Optimum (mit den Pads der Instanz), ab `n = 12` die beste von 100 steilsten Abstiegen (obere Grenze der Lücke). Die **Lücke zwischen oberen Kosten und unterer Länge** ist `(obere Kosten − untere Länge) / obere Kosten`.
- **Experimente:** (1) eine Runde mit Pseudo-Ankern (Orte, Plätze, Handbeispiele); (2) die Schleife: untere Länge und obere Kosten je Runde; (3) die Legalisierer und der Vergleich über feste Instanzen; (4) Ankergewicht und Umgewichtung; (5) Konvergenz über 120 Runden und jenseits der Aufzählung (`n = 12`). Formeln im 📐-Expander der App.

## Methodik

Experiment 1, 2 und 4 rechnen **eine** Instanz (Pads, Legalisierer, Ankergewicht `c`, Zahl der Runden und Umgewichtungen sind Regler; `n` = 6, 8, 9 mit Aufzählung als Vergleichswert, `n` = 12, 16 mit der besten von 100 Abstiegen). Standard: Zwei Cluster, `n = 8`, Seed 38, vier Pads, Zuordnung, 15 Runden, `c = 0,2`, zwei Umgewichtungen je Runde. Der Vergleich in Experiment 3 rechnet auf Knopfdruck je Familie 20 Instanzen bei `n = 8` (Seeds 100000 bis 100019) mit 2, 4 und 8 Pads und vier Schleifen (Zuordnung und Zweiteilung, je mit und ohne Umgewichtung); Experiment 5 rechnet je Familie zehn Instanzen über 120 Runden (vier Pads) und je fünf Instanzen bei `n = 12`. Der Vergleichswert hängt von den Pads ab und wird für jede Zahl von Pads neu bestimmt. Alle Aussagen laufen über feste Seeds, nie über einen einzelnen. Zeiten stehen nirgends als Zahl in Tests oder in dieser README.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` und `tests/test_oracle_loop.py` (Prozentwerte auf eine Stelle, die Werte je Familie auf ganze Prozent gerundet, Zählungen exakt). Reihenfolge der Familien: Netzliste, gleichverteilt, dünn besetzt, zwei Cluster, Stern, wenige starke Flüsse. **In keinem der 360 Fälle (n = 8) liefert eine der vier Schleifen in irgendeiner Runde Kosten unter dem aufgezählten Optimum.**

| Frage | Befund |
|---|---|
| Handbeispiele | **Pseudo-Anker:** drei Bauteile auf einer Zeile (Plätze bei 0, 1, 2; Fluss A–B 5, B–C 1; Pads bei −1 an A und 3 an C, Gewicht 2), dazu ein Pseudo-Anker mit Gewicht 1 je Bauteil am Platz 0, 1, 2: `8·x_A − 5·x_B = −2`, `7·x_B − 5·x_A − x_C = 1`, `4·x_C − x_B = 8` ergeben **x_A = 3/58, x_B = 14/29, x_C = 123/58** (ohne die Anker lag x_B bei 3/11). **Zweiteilung:** vier Bauteile auf dem 2×2-Raster an den Orten (0,2 \| 0,1), (0,1 \| 0,9), (0,9 \| 0,2), (0,8 \| 0,8) (A bis D): Teilung nach x, dann nach y: A auf (0, 0), B auf (0, 1), C auf (1, 0), D auf (1, 1) (Spalte, Zeile) |
| Standardinstanz (Zwei Cluster, n = 8, Seed 38, 4 Pads) | Optimum **226**; mittlere Kosten aller Anordnungen 36,3 % darüber. **Zuordnung:** Runde 0 Kosten 265 (Lücke 17,3 %), die Anordnung bleibt bis Runde 11 gleich und ändert sich **einmal in Runde 12**: Kosten 240 (Lücke 6,2 %). **Zweiteilung:** Kosten 240 schon in Runde 0, keine Änderung. Untere Länge 52,1 → 67,0, Lücke zwischen oberen Kosten und unterer Länge 80,3 % → 72,1 % (Zuordnung) |
| Ankergewicht (Standardinstanz, Zuordnung) | `c` = 0,02 / 0,2 / 1: Lücke zum Optimum 17,3 → 17,3 / 17,3 → 6,2 / 17,3 → 6,2 %, Änderungen der Anordnung 0 / 1 / 1; Lücke oben/unten am Ende 79,8 / 72,1 / **53,1 %** (Runde 0: 80,3 %): starke Anker nähern die Werte schnell an, schwache kaum |
| Umgewichtung (Standardinstanz) | ohne Umgewichtung Lücke 28,8 % → 28,8 % (die Anordnung bleibt), mit zwei Umgewichtungen je Runde 17,3 % → 6,2 %. **Eine Instanz, kein Befund über die Familie** |
| Annäherung ist Ankergewicht (Standardinstanz, 120 Runden) | Lücke oben/unten nach 0 / 5 / 15 / 30 / 60 / 120 Runden: 80,3 / 78,7 / 72,1 / 65,3 / 56,6 / **42,5 %**; die Anordnung ändert sich einmal (Runde 12), Lücke zum Optimum 6,2 % |
| Einmalige Rundung, n = 8 (Median, 120 Instanzen je Pad-Zahl: 2 / 4 / 8 Pads) | Zuordnung (zwei Umgewichtungen) 14,5 / 8,8 / 4,4 %, Zuordnung ohne Umgewichtung 14,1 / 9,3 / 6,2 %, Zweiteilung 11,6 / 9,1 / 4,3 % (mit) und 11,7 / 9,7 / 6,3 % (ohne); Zufall (mittlere Kosten) 38,1 / 34,5 / 26,1 % |
| **Schleife mit Umgewichtung**, Zuordnung, n = 8, Runde 0 → Runde 15 (2 / 4 / 8 Pads) | Lücke zum Optimum **14,5 → 10,8 / 8,8 → 6,3 / 4,4 → 3,6 %**; die Anordnung ändert sich in 44 / 23 / 10 von 120 Instanzen; besser in 42 / 22 / 10, **schlechter in 0 / 0 / 0**; die Anordnung der Runde 0 bleibt in 76 / 97 / 110 von 120 Instanzen bis Runde 15 gleich |
| Schleife ohne Umgewichtung, Zuordnung | 14,1 → 10,4 / 9,3 → 9,2 / 6,2 → 5,9 %; Änderung der Anordnung in 31 / 5 / 2 von 120 (besser 31 / 4 / 2, schlechter 0 / 1 / 0): **die Anker halten die erste Rundung fest** |
| Rekursive Zweiteilung, n = 8 | mit Umgewichtung 11,6 → 9,7 / 9,1 → 6,2 / 4,3 → 3,5 %, Änderung in 33 / 28 / 15 von 120, besser 32 / 23 / 13, schlechter **0 / 5 / 2**; ohne Umgewichtung 11,7 → 10,3 / 9,7 → 9,1 / 6,3 → 6,3 % |
| Lücke oben/unten nach 15 Runden, n = 8 (Zuordnung, Umgewichtung, Median) | 2 Pads: 68,4 → 52,7 %; 4 Pads: 59,5 → 47,3 %; 8 Pads: 33,5 → 25,5 % |
| Je Familie, n = 8, Zuordnung mit Umgewichtung, Runde 0 → 15 (%) | 2 Pads: 14 → 12 / 9 → 9 / 19 → 16 / 15 → 2 / 11 → 11 / 29 → 14; 4 Pads: 11 → 11 / 6 → 6 / 10 → 9 / 6 → 4 / 7 → 7 / 11 → 9; 8 Pads: 6 → 6 / 3 → 3 / 2 → 2 / 1 → 0 / 6 → 4 / 6 → 6 |
| Konvergenz über 120 Runden (n = 8, 4 Pads, 60 Instanzen, Zuordnung, Umgewichtung, `c` = 0,2) | Lücke oben/unten im Median nach 0 / 5 / 15 / 30 / 60 / 120 Runden: **60 / 56 / 48 / 36 / 22 / 12 %**; die Anordnung ändert sich im Median **in keiner** Runde (höchstens 3 Änderungen, die letzte spätestens in Runde 5); Lücke zum Optimum am Ende 5,5 %; die untere Länge steigt in 59 von 60 Instanzen in jeder Runde |
| **Echte untere Schranke** (LP je Achse, n = 8, 120 Instanzen je Pad-Zahl) | Lücke zum Optimum im Median **67,2 / 58,8 / 32,8 %** (2 / 4 / 8 Pads); nie über dem Optimum; die Länge der Umgewichtung (30 Schritte) im Verhältnis zur Schranke 1,083 / 1,067 / 1,034, nie darunter |
| Jenseits der Aufzählung, n = 12 (5 Instanzen je Familie, 30 je Pad-Zahl, Vergleichswert: beste von 100 Abstiegen) | Zuordnung mit Umgewichtung, Runde 0 → 15: 26,3 → 10,6 / 11,8 → 10,6 / 7,0 → 5,9 % (2 / 4 / 8 Pads), Änderung in 22 / 7 / 9 von 30, schlechter in 1 / 0 / 0; ohne Umgewichtung 21,4 → 16,6 / 10,4 → 10,4 / 8,8 → 8,4 %; Zweiteilung mit Umgewichtung 24,5 → 14,0 / 14,4 → 11,0 / 6,4 → 6,2 % (schlechter in 0 / 2 / 4); obere Grenzen der Lücke |
| Orakel | Das angekerte System gleich `numpy.linalg.lstsq`; die Zuordnung der Legalisierung gleich `scipy.optimize.linear_sum_assignment` und der Aufzählung aller Zuordnungen (die Zweiteilung ist für die Abstandsquadrate nie besser); die echte untere Schranke (`linprog`) von Hand an einem Beispiel (Wert 4) und nie über dem aufgezählten Optimum; keine Runde liegt unter dem Optimum |

**Was die Zahlen nicht sagen:** Die Familien und die **Pads** (Zahl, Ort, Gewicht, Verbindungen) sind erfunden; eine andere Ankeranordnung kann die Zahlen ändern. Die Pseudo-Anker sind eine **eigene einfache Fassung** (Gewicht `c · Grundgewicht · t`, Anker am legalen Platz); SimPL setzt die Anker an gestreckte Orte und wählt das Gewicht anders. Die Zweiteilung ist nicht die nichtlineare Skalierung von SimPL. Es gibt keine Detailplatzierung. Ab `n = 12` sind die Lücken obere Grenzen; bei Experiment 5 sind es zehn Instanzen je Familie, bei `n = 12` fünf.

## Ehrliche Grenzen

- **Erfundene Pads und Familien:** Befunde gelten für diese Anker und diese Familien.
- **Eigene Schleife, nicht SimPL:** Pseudo-Anker am legalen Platz, Gewicht `c · Grundgewicht · t`; die Aussage „die Anker halten die erste Rundung fest“ gilt für diese Fassung.
- **Konvergenz ist kein Gütemaß:** die Lücke oben/unten schrumpft durch das Ankergewicht, auch wenn sich die Anordnung nicht ändert; große Gewichte setzen die Bauteile fest auf ihre Plätze.
- **Näherungen, keine Schranken:** untere Länge und obere Kosten sind keine Schranken; die echte untere Schranke wird nur in den Tests gerechnet und ist schwach.
- **Rekursive Zweiteilung:** eigene einfache Fassung; weder die Skalierung von SimPL noch Abacus.
- **Keine Detailplatzierung:** nach der Schleife wird nicht getauscht (Stück 12).
- **Wenige Instanzen:** n = 8: 20 je Familie (Konvergenz: 10), n = 12: 5.
- **Rechnerabhängige Gleichstände:** Sortieren und Zuordnung entscheiden Gleichstände nach acht Stellen Rundung; Änderungen dieser Festlegung ändern einzelne Zählungen („Anordnung ändert sich in …“).
- **Quellen:** SimPL (Kim, Lee, Markov), Abacus (Spindler u. a.) und Kraftwerk2 mit dem Bound2Bound-Netzmodell sind aus der Fachliteratur übernommen und **nicht nachgelesen**; die Pseudo-Anker im System, die Annäherung durch das Gewicht, die Zweiteilung und die LP-Schranke der reellen Orte sind eigene Herleitungen und werden durch Tests (Handrechnung, Aufzählung, `scipy`) geprüft.

## Verifikation

- **Tests** (`pytest tests/`): **205 Tests**, rund zwei Minuten (Windows, Python 3.14). Handwerte (die Pseudo-Anker von Hand: `x = (3/58, 14/29, 123/58)`; die Zweiteilung von Hand am 2×2- und 2×3-Raster; Pads, Kosten, Platzierung aus Stück 9), Eigenschaften (das angekerte System hat den Gradienten null; für `λ → 0` ist es Stück 9, für `λ → ∞` fallen die Bauteile auf ihre Plätze; beide Legalisierer liefern Anordnungen; die untere Länge steigt; die Runden tragen die Gewichte `c · Grundgewicht · t`; die ganze Schleife ändert sich bei Rechenrauschen von 1e-13 nicht), Orakel (`lstsq`, `linear_sum_assignment`, Aufzählung, `linprog` für die echte untere Schranke; nur mit `requirements-dev.txt`), Randfälle (null Runden, null Pads, Nullfluss), Verdikte an handgesetzten Werten, Abbildungen, PDF, Rauchtest und Pfade der App (jede Familie, jede Einstellung, `n` = 9, 12, 16, alle Rechenknöpfe), Layout, Footer und Laufzeit-Importe. `test_claims.py` und `test_oracle_loop.py` rechnen jede Zahl dieser README nach.
- **Kopie:** Tests vergleichen die Familien mit denen von Stück 1 bis 9, sofern die Schwester-Repos nebenan liegen.
- **Nicht getestet:** Zeiten; kein Mutationstest; Linux-CI: noch nicht gelaufen (Repo noch nicht veröffentlicht).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: fünf Experimente, Vergleiche über feste Instanzen, Grenzen, Formulierung |
| `lal_rng.py` | SplitMix64 (Kopie aus Stück 1) |
| `lal_instance.py` | Instanzen: sechs Familien der Flussmatrix, Raster, Handbeispiele |
| `lal_cost.py` | Kosten, Tausch-`Δ` (Kopie aus Stück 2) |
| `lal_landscape.py` | Aufzählung für das Optimum (Kopie aus Stück 2) |
| `lal_assignment.py` | Ungarische Methode (Kopie aus Stück 8) |
| `lal_place.py` | Pads, lineares System, Umgewichtung, Rundung, Kosten mit linearem Term, Abstieg (Kopie aus Stück 9) |
| `lal_loop.py` | Pseudo-Anker im System, Legalisierer (Zuordnung, Zweiteilung), die Schleife |
| `lal_evaluation.py` | Zeilen für die Vergleiche, Kurven, Zusammenfassungen, Verdikte |
| `lal_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `lal_pdf_export.py` | PDF-Export des Ergebnisses |
| `lal_constants.py` | Größen, Familien, feste Reihen, Farben, Presets |
| `lal_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Button |
| `lal_layout.py` | Fester Kopf (Stylesheet) |
| `requirements-dev.txt` | Laufzeit plus pytest und scipy |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt; kein `scipy` zur Laufzeit) |
| `tests/` | Schleife, Platzierung, Zuordnung, Kosten, Instanzen, Landschaft, Auswertung, Verdikte, Abbildungen, Presets, Layout, AppTest, Orakel, Zahlen der README, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **SimPL im Original (Anker an gestreckten Orten, nichtlineare Skalierung, Bound2Bound-Netzmodell) und Abacus:** nur die Grundidee der Rückbindung.
- **Nichtlineare Dichte (Stück 11), Detailplatzierung (Stück 12):** nur als Hinweis.
- **Ein eigener LP-Löser für die echte untere Schranke:** sie wird in den Tests mit `scipy` gerechnet, nicht zur Laufzeit.
- **Pads mit Größe, Routing, Zeitoptimierung.**
- **Asymmetrische Flüsse und Abstände.**

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Streamlit Cloud: Python-Version in den App-Einstellungen prüfen (lokal Python 3.14, CI Python 3.12); der Code verwendet nur Merkmale, die in Python 3.12 laufen. <!-- lint-ok: dezimalpunkt -->

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy, pandas und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
