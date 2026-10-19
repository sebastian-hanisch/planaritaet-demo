# Planarität erkennen und belegen – Einbettung und Kuratowski-Zeuge – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-planaritaet-demo.streamlit.app/)** -->

Erstes Stück der **Planarität-und-Zeichnen-Linie** (Graphentheorie) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Es ist die Wurzel der Linie; Vorgänger gibt es nicht. Verwandt sind
[euclidean-mst-demo](https://github.com/sebastian-hanisch/euclidean-mst-demo) (Delaunay-Triangulierungen als Werkzeug, hier als planare Instanzen), [graph-coloring-demo](https://github.com/sebastian-hanisch/graph-coloring-demo) und
[treewidth-demo](https://github.com/sebastian-hanisch/treewidth-demo) (Toronto-Daten). Die Demo entscheidet, ob ein Graph **planar** ist (zeichenbar ohne Kreuzung), und **belegt** die Antwort: bei „ja“ mit einer Einbettung (Flächenliste, geprüft mit der Euler-Formel), bei „nein“ mit einer Unterteilung von K5 oder K3,3 (Satz von Kuratowski).

Vehikel: Karten aus zufälligen Standorten (Delaunay-Triangulierung), Raster, Zufallsverbindungen, neun Lehrbuch-Graphen und ein Auszug aus OpenStreetMap (Toronto, ODbL). Eigene Löser in Python, `networkx` nur als Gegenprobe in den Tests.

## Warum dieses Problem

Eine Karte, ein Schaltplan oder ein Verteilnetz soll sich ohne Überkreuzung zeichnen lassen. Ob das geht, ist eine Eigenschaft des Graphen, nicht der Zeichnung. Die Demo zeigt zwei Dinge, die den Blick auf Daten ändern: Planarität kippt in Zufallsgraphen weit unter der Kantenzahl, die ein planarer Graph haben dürfte (die Schranke 3n − 6 ist notwendig, nicht hinreichend), und eine echte Straßenkarte ist **nicht** exakt planar, aber nah dran. Kernfrage: **wie belegt man Planarität, und wie früh kippt sie?**

## Modell

Ein einfacher ungerichteter Graph. **Fragmenttest** nach Demoucron, Malgrange und Pertuiset (1964) je zweifach zusammenhängendem Block: ein Kreis wird gezeichnet, dann wird wiederholt ein Fragment (eine Brücke) in eine Fläche gelegt, an deren Rand alle seine Anschlussknoten liegen. Hat ein Fragment keine solche Fläche, ist der Graph nicht planar; sonst ist die Flächenliste die Einbettung. **Zeuge:** jede Kante wird probeweise gestrichen, bleibt der Rest nichtplanar, bleibt sie gestrichen; übrig bleibt eine Unterteilung von K5 oder K3,3, die eine unabhängige Prüfung (`verify_witness`) ohne Planaritätstest nachrechnet. Formeln und Literatur im Expander „📐 Mathematische Formulierung“ der App.

Netztypen (alle mit derselben Kantenzahl m = Dichte % von 3n − 6): **Karte** (Kanten der Delaunay-Triangulierung zufälliger Standorte, zufällig verdünnt), **Raster** (zuerst Gitterkanten, dann Diagonalen) und **Zufallsverbindungen** (beliebige Paare, auf einem Kreis gezeichnet). Dazu bis zu zehn Zusatzkanten zwischen zufälligen Paaren. Die Lage der Knoten ist nur ein Layout.

## Methodik

- **Einbetten:** Fragmenttest, ein Fragment mit nur einer zulässigen Fläche zuerst, sonst das erste; kleinste Knotennummer bei Gleichstand. Abspielen Schritt für Schritt (Kreis, Fragment, Weg, geteilte Fläche).
- **Beleg bei „nein“:** Kantenabbau (höchstens m Tests), Einordnung als K5 oder K3,3 nach Grad der Verzweigungsknoten, Wege dazwischen farbig.
- **Messreihen:** (1) Anteil planarer Zufallsverbindungen über der Dichte (n = 20 und 40, je 100 Graphen mit festen Seeds 200000 bis 200099), (2) ein dünnes planares Karten-Netz (60 % von 3n − 6 Kanten) mit k Zusatzkanten (n = 30 und 60, je 100 Graphen), (3) Aufwand des Fragmenttests auf voll triangulierten Karten (Median über 5 feste Instanzen `SWEEP_SEEDS`).
- **Toronto:** der Auszug aus `bfs-demo` (5.072 Knoten, 7.621 Kanten, ungerichtet vereinigt). Die Streckenkreuzungen der Zeichnung werden live mit einem Raster beschleunigt gezählt, der Zeuge aus `data/toronto_befund.json` wird unabhängig geprüft; schwer ist nur der Zeuge selbst (Kantenabbau in Teilmengen, 1.134 Tests) und die Prüfung, dass die Karte nach dem Streichen von 52 Kanten planar ist (`tools/toronto_befund.py`, 27 Sekunden).

## Befunde (gemessen, keine Behauptungen)

| Frage | Befund | Test |
|---|---|---|
| Wo kippt Planarität in Zufallsverbindungen? | n = 20: bei Dichte 40 % sind 90 % planar, bei 50 % noch 48 %, bei 60 % nur 8 %; n = 40: bei 30 % 96 %, bei 40 % 22 %, bei 50 % kein einziger. Der Kipppunkt (höchstens die Hälfte planar) liegt bei n = 20 bei Dichte 50 % (mittlerer Grad 2,7) und bei n = 40 bei 40 % (2,3); die Euler-Schranke erlaubt bis Dichte 100 % (mittlerer Grad 5,4 bzw. 5,7). | `test_share_table` |
| Wie schnell kippt ein planares Netz durch Zusatzkanten? | Dünnes Karten-Netz (60 %): bei n = 30 machen 1 / 2 / 3 / 5 Zusatzkanten 48 / 81 / 91 / 100 % der Graphen nichtplanar, bei n = 60 70 / 93 / 100 / 100 %; ohne Zusatz nie. | `test_plus_table` |
| Wie wächst der Aufwand des Fragmenttests? | Voll triangulierte Karten, n = 20 / 40 / 80 / 160 / 320: 1.873 / 11.891 / 78.570 / 442.477 / 2.855.431 Schritte, etwa mit n hoch 2,6 (Schritte = Besuche von Nachbarn und Prüfungen von Flächen, keine Laufzeit). | `test_cost_table` |
| Reicht die Kantenschranke 3n − 6? | Nein, sie ist notwendig und nicht hinreichend: K3,3 hat 9 von höchstens 12 Kanten und ist nichtplanar; das Preset „Eine Kante zu viel“ macht eine Karte mit 34 von höchstens 36 Kanten nichtplanar. | `test_euler_bound_is_not_sufficient` |
| Ist die Toronto-Karte planar? | **Nein.** Der nichtplanare Block hat 4.193 Knoten und 6.720 Kanten; der Zeuge ist eine Unterteilung von K3,3 mit 37 Kanten (1.134 Tests). | `test_toronto_witness_and_block` |
| Wie nah ist sie an planar? | 125 Streckenkreuzungen der Zeichnung an 163 Kanten; eine Überdeckung aus **52 Kanten** (0,7 % von 7.621) berührt alle Kreuzungen, nach ihrem Entfernen ist die Karte planar (Fragmenttest dieser Demo und `networkx`). | `test_toronto_crossings_and_cover`, `test_toronto_planar_after_cover` |
| Sind die Streckenkreuzungen echt? | Teils nicht: 31 der 125 gehen auf mindestens eine stark gekrümmte Kante zurück (Länge / Luftlinie ab 1,2), 51 haben beide Kanten nahezu gerade (unter 1,05). Länge / Luftlinie: Median 1,004, bei 7,4 % der Kanten über 1,05. | `test_toronto_curvature` |
| Sagt der Datensatz, warum? | **Nein**: er hat keine Brücken- oder Tunnelmarken, nur Längen; die Ursache der Nichtplanarität (Brücken, Tunnel, nicht verschmolzene Knoten) bleibt offen. | `test_toronto_has_no_bridge_tags` |
| Welche Lehrbuch-Graphen sind planar? | K4, Würfel, Oktaeder und K5 minus eine Kante sind planar (kreuzungsfrei gezeichnet); K5, K3,3, Petersen-Graph, Wagner-Graph und K3,3 mit zwei Unterteilungen nicht. | `test_textbook_graphs` |

## Ehrliche Grenzen

- **Kein Linearzeit-Test.** Der Fragmenttest hat Aufwand etwa n hoch 2,6 in dieser Umsetzung; der Left-Right-Test (de Fraysseix, Rosenstiehl, in der Darstellung von Brandes) arbeitet in linearer Zeit und ist nur als Einordnung genannt, nicht nachgebaut.
- **Der Kantenabbau braucht bis zu m Tests.** Ab 400 Kanten im nichtplanaren Block gibt es live keinen Zeugen; für Toronto ist er mit Kantenabbau in Teilmengen vorgerechnet. Er ist kantenminimal, aber einer von vielen möglichen.
- **Zufallsverbindungen sind kein Straßennetz.** Die Messreihen zeigen das Verhalten zufälliger Paare; echte Netze verbinden Nachbarn und liegen viel näher am Planaren.
- **Toronto: Ursache offen.** Die 52 Kanten sind eine Obergrenze (Überdeckung aller Streckenkreuzungen), kein Minimum; wiederholtes Zeugenabbauen (je Zeuge eine Kante streichen) wurde nicht weiterverfolgt, weil die Zeugen dabei größer wurden. Wer die Ursache klären will, braucht Brücken- und Tunnelmarken aus OpenStreetMap.
- **Die Zeichnung zeigt nicht die Einbettung.** Die Lage der Knoten ist ein Layout; „Layout-Kreuzungen“ sagt nichts über Planarität.

## Befunde und Korrekturen gegenüber dem Plan

- **Zeuge der Toronto-Karte:** die Vormessung im Einzelplan fand einen K3,3-Zeugen mit 29 Knoten und 32 Kanten; die Demo findet mit Kantenabbau in Teilmengen auf dem nichtplanaren Block einen anderen mit 37 Kanten (beide kantenminimal, der Zeuge ist nicht eindeutig).
- **Aufwand:** die Vormessung zählte 674.239 Schritte bei n = 320 (n hoch 2,1); die Demo zählt zusätzlich die Flächenprüfungen je Fragment und kommt auf 2.855.431 (n hoch 2,6). Die Zahlen sind nicht vergleichbar.
- **Planaritätsanteil und Zusatzkanten:** die Vormessung nutzte den mittleren Grad bzw. 60 % der Delaunay-Kanten; die Demo nutzt die Dichte in Prozent von 3n − 6 und verdünnt auf 60 % von 3n − 6. Daher andere Zahlen (n = 30, eine Zusatzkante: 48 % statt 39 %).
- **Toronto-Ursache:** die Annahme „Datenartefakt oder Brücken“ ließ sich auch hier nicht entscheiden; die Daten enthalten keine Marken.

## Verifikation

- **Kern gegen Handrechnung:** Blöcke, Kreis, Fragmente, zulässige Flächen, Fragmentwahl, Weg, Flächenteilung, Einbettung von Haus, K4, K5, K3,3, Zeuge von K5 mit Schwanz und von K3,3 mit Unterteilungen (`tests/test_algorithm.py`, 26 Tests).
- **Orakel:** `tests/test_oracle_planaritaet.py`: Urteil gegen eine Aufzählung nach der Definition (Unterteilung von K5/K3,3, ohne Planaritätstest) auf 90 kleinen Graphen und gegen `networkx` auf 520 Graphen; Blöcke gegen `networkx`; Einbettung (Euler im Block, jede Kante auf genau zwei Flächenseiten); Zeugen kantenminimal und nichtplanar; Monotonie unter Kantenentfernung; stapelweise trianguliert plus eine beliebige Kante nichtplanar; Unabhängigkeit von der Knotennummerierung; Kantenschranke.
- **Mutationsprüfung** (`tools/mutate_demo.py`, Stand vor dem ersten Commit): 242 von 251 Stellen des Kerns gesichert (gefangen oder als äquivalent festgehalten, `tests/mutation_state.json`), keine offene Lücke; 8 Mutanten ergaben Endlosschleifen (Zeitüberschreitung, zählt nicht). Die äquivalenten sind fast nur Sortierreihenfolgen und Schleifengrenzen, die das Ergebnis nicht ändern.
- **Randfälle:** leerer Graph, ein Knoten, zwei Knoten, Dreieck, Doppelkanten, isolierte Knoten, Wald, die Schranke inklusive, alle Ecken der Regler (`tests/test_edge_cases.py`).
- **Verdikte** als reine Funktionen, jede Zahl und Schwelle (`tests/test_verdicts.py`); **Claims:** jede Zahl dieser README (`tests/test_claims.py`).
- **Szenario:** Generatoren, Dichte, Raster, Hash-Seed-Unabhängigkeit, Lehrbuch-Graphen, Toronto-Daten (`tests/test_scenario.py`); Darstellung (`tests/test_visualization.py`); Presets halten, was ihre Hilfetexte sagen (`tests/test_presets.py`).
- **Werkzeug:** `ddmin` aus `tools/toronto_befund.py` liefert auf Zufallsgraphen kantenminimale nichtplanare Teilgraphen, der gespeicherte Toronto-Zeuge ist kantenminimal (`tests/test_tools.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Layout (Schnellstart in der Seitenleiste, fester Kopf, aktives Preset hervorgehoben), Footer, Laufzeit-Importe.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `plt_algorithm.py` | Kern: Blöcke, Fragmenttest, Einbettung, Zeuge und dessen Prüfung, Streckenkreuzungen |
| `plt_constants.py` | Regler-Grenzen, Rechengrenzen, Farben, Presets |
| `plt_evaluation.py` | Analyse, Messreihen, Toronto-Befund, Verdikte, deutsche Zahlenformate |
| `plt_layout.py` | Fester Kopf (Stylesheet) |
| `plt_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `plt_scenario.py` | Instanzen: Karte, Raster, Zufallsverbindungen, Lehrbuch-Graphen, Toronto |
| `plt_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `data/toronto_campus.json`, `data/LICENSE-ODbL.md` | OpenStreetMap-Auszug (ODbL) aus `bfs-demo` |
| `data/toronto_befund.json` | vorgerechnet: Zeuge, Überdeckung, Planarität nach dem Streichen |
| `tools/toronto_befund.py` | erzeugt `data/toronto_befund.json` (rund eine Minute) |
| `requirements-dev.txt` | Laufzeit plus pytest und networkx (Gegenprobe) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Handrechnung, Orakel, Randfälle, Verdikte, Claims, Szenario, Darstellung, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- Ein Linearzeit-Planaritätstest (Left-Right-Test, Boyer–Myrvold) und die Einbettung als Rotationssystem.
- Eine Zeichnung der Einbettung (kreuzungsfreie Koordinaten); die Demo zeigt die Flächenliste.
- Die Kantenzahl bis zur Planarität (Kantenabstand) exakt: sie ist NP-schwer; nur eine Obergrenze aus der Überdeckung der Streckenkreuzungen.
- Echte Brücken- und Tunnelmarken für Toronto (müssten neu aus OpenStreetMap geholt werden).

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy (Delaunay-Triangulierung der Standorte).

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
