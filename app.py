"""Planarität erkennen und belegen – Einbettung und Kuratowski-Zeuge - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import plt_algorithm as A
import plt_constants as C
import plt_evaluation as ev
import plt_scenario as S
from plt_layout import dunkles_design, kopf_css
from plt_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from plt_visualization import (
    build_cost,
    build_graph,
    build_playback,
    build_plus,
    build_share,
    build_toronto,
    build_witness,
)

st.set_page_config(page_title="Planarität erkennen und belegen – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _hand(name):
    return ev.analyse_instance(S.hand_graph(name))


@st.cache_data(show_spinner=False)
def _cost_rows():
    return ev.cost_table()


@st.cache_data(show_spinner=False)
def _measure_rows():
    return ev.share_table(), ev.plus_table()


@st.cache_data(show_spinner=False)
def _toronto():
    return ev.toronto_stats()


def _event_text(block, step):
    """Ein Satz zum Schritt `step` (1 = Anfangskreis)."""
    ev_ = block.events[step - 1]
    if ev_.kind == "cycle":
        return f"Schritt 1: ein Kreis mit {len(ev_.path)} Knoten teilt die Ebene in zwei Flächen."
    if ev_.kind == "fail":
        frag = ev_.fragment
        return (
            f"Schritt {step}: Das Fragment mit den Anschlussknoten {', '.join(map(str, frag.attach))} liegt in **keiner** Fläche, die alle diese Knoten am Rand hat. "
            f"Der Graph ist nicht planar."
        )
    frag = ev_.fragment
    what = "eine Kante" if not frag.interior else f"ein Stück mit {len(frag.interior)} inneren Knoten"
    forced = " Die Wahl war erzwungen (nur eine zulässige Fläche)." if ev_.admissible == 1 else ""
    return (
        f"Schritt {step}: Von {ev_.fragments} Fragmenten wird {what} mit den Anschlussknoten {', '.join(map(str, frag.attach))} gewählt; "
        f"{ev_.admissible} Flächen sind zulässig. Der Weg {' – '.join(map(str, ev_.path))} teilt eine Fläche; jetzt {ev_.faces} Flächen.{forced}"
    )


def _show_playback(inst, emb, key_prefix):
    """Block wählen, Schritt wählen, Bild und Satz zum Schritt; bei planaren Graphen die Flächenliste."""
    candidates = [i for i, b in enumerate(emb.blocks) if len(b.nodes) >= 3]
    if not candidates:
        st.info("Der Graph hat keinen Kreis (ein Wald): er ist planar, es gibt nichts einzubetten.")
        return
    candidates.sort(key=lambda i: (emb.failed_block != i, -len(emb.blocks[i].nodes), i))
    labels = {i: f"Block {k + 1}: {len(emb.blocks[i].nodes)} Knoten, {len(emb.blocks[i].edges)} Kanten" + (" (nicht planar)" if not emb.blocks[i].planar else "") for k, i in enumerate(candidates)}
    if len(candidates) > 1:
        choice = st.selectbox("Block", candidates, format_func=lambda i: labels[i], key=f"{key_prefix}_block")
    else:
        choice = candidates[0]
    block = emb.blocks[choice]
    total = len(block.events)
    step = st.slider("Schritt", 0, total, total, key=f"{key_prefix}_step_{choice}_{total}", help="0 = vor dem ersten Schritt; der letzte Schritt zeigt das Ergebnis.")
    st.plotly_chart(build_playback(inst, block, step), width="stretch", key=f"{key_prefix}_play_{choice}_{step}")
    if step:
        st.markdown(_event_text(block, step))
    else:
        st.caption("Vor dem ersten Schritt: noch nichts eingebettet. Mit dem Regler Schritt für Schritt vorwärts.")
    if block.planar and block.faces:
        with st.expander("Flächen der Einbettung"):
            rows = [{"Fläche": i + 1, "Knoten": len(f), "Rand (zyklisch)": " – ".join(map(str, f))} for i, f in enumerate(sorted(block.faces, key=lambda f: (-len(f), f)))]
            st.dataframe(rows, hide_index=True, width="stretch")
            st.caption(
                f"Prüfung: {len(block.nodes)} Knoten − {len(block.edges)} Kanten + {len(block.faces)} Flächen = {len(block.nodes) - len(block.edges) + len(block.faces)} (Euler-Formel für einen Block: 2); "
                f"jede Kante liegt auf genau zwei Flächenseiten: {'ja' if A.euler_ok(block) else 'NEIN'}."
            )


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in plt_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🗺️ Planarität erkennen und belegen – Einbettung und Kuratowski-Zeuge")
st.markdown(
    """
**Planar** heißt: Der Graph lässt sich so in die Ebene legen, dass sich keine zwei Kanten kreuzen (eine Karte ohne Brücken). Diese Demo entscheidet das und **belegt** die Antwort:
bei „ja“ mit einer **Einbettung** (die Flächen, prüfbar mit der Euler-Formel), bei „nein“ mit einem **Zeugen**, einer Unterteilung von **K5 oder K3,3** (Satz von Kuratowski).
Erstes Stück der Linie *Planarität und Zeichnen* in der Graphentheorie; die Graphen sind Karten aus Standorten, Raster und Zufallsverbindungen, dazu Lehrbuch-Graphen und eine echte Straßenkarte.

Weiter unten: die Experimente **🔬 Wo kippt Planarität?** und **🔬 Lehrbuch-Graphen**, der Befund **🔬 Straßenkarte Toronto**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert der Fragmenttest", expanded=True):
    st.markdown(
        """
1. **Ein Kreis** des Graphen wird gezeichnet; er teilt die Ebene in zwei **Flächen** (innen und außen).
2. **Fragmente** sind die Reste: eine Kante zwischen zwei schon gezeichneten Knoten oder ein Stück des Graphen, das nur über **Anschlussknoten** am Gezeichneten hängt.
3. Ein Fragment darf nur in eine Fläche, an deren Rand **alle** seine Anschlussknoten liegen (**zulässige Fläche**). Hat ein Fragment keine, ist der Graph **nicht planar**. Hat eines genau eine, muss es dorthin; es hat keine Wahl.
4. Ein Weg des Fragments zwischen zwei Anschlussknoten wird in die Fläche gelegt und teilt sie. Das wiederholt sich, bis alle Kanten gezeichnet sind: die Flächenliste ist die **Einbettung**.
5. **Zeuge bei „nein“:** jede Kante wird probeweise gestrichen; bleibt der Rest nichtplanar, bleibt sie gestrichen. Was übrig bleibt, ist eine Unterteilung von K5 oder K3,3.

**Warum das funktioniert:** Gibt es ein Fragment mit nur einer zulässigen Fläche, wird es dorthin gelegt; sonst darf jedes Fragment in jede seiner zulässigen Flächen. Dass der Test dabei nie in eine Sackgasse läuft, wenn der Graph planar ist,
ist der Satz von Demoucron, Malgrange und Pertuiset (1964); er wird hier nicht neu bewiesen, aber gegen `networkx` und eine Brute-Force-Aufzählung der Unterteilungen geprüft.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Graph**")
    net = st.selectbox("Netztyp", list(C.NET_TYPES), key="net_select", format_func=C.NET_TYPES.get, help=C.NET_HELP)
    n = st.slider("Knoten n", *bounds("n_slider"), key="n_slider", help="Zahl der Knoten (bei einem Raster Zeile für Zeile gefüllt).")
    density = st.slider(C.DENSITY_LABEL, *bounds("density_slider"), key="density_slider", help="Zahl der Kanten als Anteil der Höchstzahl 3n − 6, die ein planarer Graph haben darf. 100 % entspricht beim Karten-Netz einer vollen Triangulierung.")
    extra = st.slider("Zusatzkanten k", *bounds("extra_slider"), key="extra_slider", help="k weitere Kanten zwischen zufälligen, noch nicht verbundenen Paaren, zusätzlich zum gewählten Netz.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"net_select": net, "n_slider": int(n), "density_slider": int(density), "extra_slider": int(extra), "seed_input": int(seed)})

settings = ev.Settings(net, int(n), int(density), int(extra), int(seed))
a = _analysis(settings)
inst, emb = a.inst, a.emb

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Knoten n", f"{inst.n}")
m2.metric("Kanten m", f"{inst.m}", delta=f"von {a.bound} erlaubt", delta_color="off", help=f"Ein planarer Graph mit n = {inst.n} Knoten hat höchstens 3n − 6 = {a.bound} Kanten (Euler-Schranke).")
m3.metric("Planar?", "ja" if emb.planar else "nein", delta=f"{emb.steps} Schritte", delta_color="off")
m4.metric("Layout-Kreuzungen", f"{a.layout_crossings}", delta="nur Zeichnung", delta_color="off", help="Kreuzungen der Strecken in der gezeigten Lage. Sie sagen nichts über Planarität: ein planarer Graph kann in einer schlechten Lage Kreuzungen haben.")
kind, text = ev.verdict_planarity(a)
getattr(st, kind)(text)
kind, text = ev.verdict_euler(a)
getattr(st, kind)(text)

if a.witness is not None:
    st.plotly_chart(build_witness(inst, a.witness, title=f"Zeuge: Unterteilung von {a.witness.kind}"), width="stretch", key="main_witness")
    problems = A.verify_witness(inst.edges, a.witness)
    if problems:
        st.error("Der Zeuge besteht die unabhängige Prüfung nicht: " + "; ".join(problems))
    else:
        st.caption(
            f"Farbig: die {len(a.witness.paths)} Wege zwischen den {len(a.witness.branch)} Verzweigungsknoten (rot); graue Kanten gehören nicht zum Zeugen. "
            f"Unabhängig geprüft: jede Zeugenkante liegt auf genau einem Weg, die Verzweigungsknoten sind wie die Ecken von {a.witness.kind} verbunden."
        )
else:
    st.plotly_chart(build_graph(inst, title=f"{inst.name}: {inst.n} Knoten, {inst.m} Kanten"), width="stretch", key="main_graph")
    st.caption("Die Lage der Knoten ist nur eine Zeichnung (siehe „Layout-Kreuzungen“): Planarität ist eine Eigenschaft des Graphen. Die Flächen der Einbettung stehen unten.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie belegt man Planarität, und wie früh kippt sie?")
st.markdown("### Der Fragmenttest, Schritt für Schritt")
_show_playback(inst, emb, "main")

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wo kippt Planarität?")
st.caption(
    f"Zwei Messreihen mit je {C.SHARE_SAMPLES} Zufallsgraphen je Zelle (feste Seeds): Zufallsverbindungen bei wachsender Dichte, und ein dünnes planares Karten-Netz ({C.PLUS_DENSITY} % der Höchstkantenzahl) mit k Zusatzkanten. "
    "Beim ersten Aufruf dauert das Rechnen einen Moment."
)
with st.spinner("Rechne die Messreihen …"):
    rows_share, rows_plus = _measure_rows()
st.plotly_chart(build_share(rows_share), width="stretch", key="share_chart")
kind, text = ev.verdict_share(rows_share)
getattr(st, kind)(text)
st.plotly_chart(build_plus(rows_plus), width="stretch", key="plus_chart")
kind, text = ev.verdict_plus(rows_plus)
getattr(st, kind)(text)

st.markdown("**Aufwand des Fragmenttests**")
cost_rows = _cost_rows()
st.plotly_chart(build_cost(cost_rows), width="stretch", key="cost_chart")
kind, text = ev.verdict_cost(cost_rows)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Lehrbuch-Graphen")
st.caption("Neun bekannte kleine Graphen: dieselbe Prüfung, gleiche Ausgabe. Die planaren sind kreuzungsfrei gezeichnet, die übrigen in einer üblichen Lage.")
hand = st.selectbox("Graph", C.HAND_GRAPHS, index=C.HAND_GRAPHS.index(C.DEFAULT_HAND), key="hand_select")
ha = _hand(hand)
kind, text = ev.verdict_planarity(ha)
getattr(st, kind)(text)
if ha.witness is not None:
    st.plotly_chart(build_witness(ha.inst, ha.witness, title=f"{hand}: Zeuge, Unterteilung von {ha.witness.kind}"), width="stretch", key="hand_witness")
else:
    st.plotly_chart(build_graph(ha.inst, title=f"{hand}: {ha.inst.n} Knoten, {ha.inst.m} Kanten"), width="stretch", key="hand_graph")
_show_playback(ha.inst, ha.emb, "hand")

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Straßenkarte Toronto")
st.markdown(
    "Ein Auszug aus OpenStreetMap (Umkreis von 1 000 m um den St. George Campus, alle Wegarten, Daten unter ODbL): Knoten sind Kreuzungen und Endpunkte, Kanten Straßen- und Wegstücke. "
    "Ist so eine Karte planar? Ein Auge sagt „ja“, der Test sagt etwas anderes. Das Laden dauert einen Moment (Streckenkreuzungen der Zeichnung) und läuft nur auf Klick."
)
if st.button("🗺️ Toronto-Karte prüfen", key="run_toronto"):
    with st.spinner("Prüfe die Karte …"):
        st.session_state["toronto"] = _toronto()
t = st.session_state.get("toronto")
if t:
    inst_t = t["inst"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Knoten", f"{inst_t.n:,}".replace(",", "."))
    c2.metric("Kanten", f"{inst_t.m:,}".replace(",", "."))
    c3.metric("Streckenkreuzungen", f"{t['crossings']}", delta="in der Zeichnung", delta_color="off")
    c4.metric("Kanten bis planar (höchstens)", f"{t['cover_size']}", delta=f"{ev.num(t['cover_size'] / inst_t.m * 100, 1)} % der Kanten", delta_color="off")
    kind, text = ev.verdict_toronto(t)
    getattr(st, kind)(text)
    if t["witness_problems"] or not t["witness_nonplanar"]:
        st.error("Der gespeicherte Zeuge besteht die Prüfung nicht: " + "; ".join(t["witness_problems"] or ["Teilgraph ist planar"]))
    st.markdown("**Ganze Karte** (rot: Streckenkreuzungen, orange: an Kreuzungen beteiligte Kanten, türkis: Zeuge)")
    st.plotly_chart(build_toronto(t), width="stretch", key="toronto_all")
    st.markdown("**Der Zeuge aus der Nähe**")
    st.plotly_chart(build_toronto(t, zoom_to_witness=True), width="stretch", key="toronto_zoom")
    st.caption(
        f"Der Zeuge ist eine Unterteilung von {t['witness'].kind} mit {len(t['witness'].edges)} Kanten und wurde durch Kantenabbau in Teilmengen gefunden ({t['fixed']['witness_tests']} Tests, vorgerechnet); "
        f"die App prüft ihn unabhängig und zeigt, dass schon dieser kleine Teil nichtplanar ist. Nach dem Streichen der {t['cover_size']} Kanten der Überdeckung "
        f"{'ist die Karte planar (vorgerechnet mit dem Fragmenttest dieser Demo)' if t['fixed']['planar_after_cover'] else 'bleibt die Karte nichtplanar (vorgerechnet)'}."
    )

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Der Graph ist zweifach zusammenhängend** | Der Fragmenttest braucht das; die Demo rechnet deshalb je Block. Ein Graph ist genau dann planar, wenn jeder Block es ist. | - |
| **Die Zeichnung zeigt die Einbettung** | Nein: Zufallsverbindungen sind auf einen Kreis gelegt, Karten und Raster in ihre Lage. Die Layout-Kreuzungen sagen nichts über Planarität; die Flächenliste ist die Einbettung. | - |
| **Der Kantenabbau findet den Zeugen schnell** | Er braucht für jede Kante einen Planaritätstest. Ab 400 Kanten im nichtplanaren Block gibt es live keinen Zeugen; die Toronto-Karte wurde mit Kantenabbau in Teilmengen vorgerechnet. | - |
| **Zufallsverbindungen sind kein Straßennetz** | Echte Netze verbinden Nachbarn; sie sind viel dichter am Planaren, als zufällige Paare es wären (siehe Toronto). Die Messreihen zeigen das Verhalten zufälliger Paare, nicht das echter Netze. | - |
| **„Schritte“ sind eine Laufzeit** | Nein: gezählt werden Besuche von Nachbarn und Prüfungen von Flächen in dieser Umsetzung. Verfahren mit linearer Laufzeit (der Left-Right-Test) arbeiten anders und sind hier nicht nachgebaut. | - |
| **Die Karten-Daten sagen, warum Toronto nichtplanar ist** | Nein: sie enthalten keine Brücken- oder Tunnelmarken, nur Längen. Die Ursache bleibt offen. | - |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben** ein einfacher ungerichteter Graph $G=(V,E)$ mit $n=|V|$ Knoten und $m=|E|$ Kanten und $c$ Zusammenhangskomponenten. **Gesucht:** ob $G$ planar ist, und ein Beleg.

| Symbol | Bedeutung |
|---|---|
| $n$, $m$, $c$ | Zahl der Knoten, Kanten, Zusammenhangskomponenten |
| $f$ | Zahl der Flächen einer Einbettung (die äußere mitgezählt) |
| Block | zweifach zusammenhängender Teil; eine Brücke ist ein Block mit einer Kante |
| Fragment | Kante zwischen zwei eingebetteten Knoten oder Komponente der übrigen Knoten samt Anschlusskanten |
| Anschlussknoten | eingebettete Knoten, mit denen ein Fragment verbunden ist |
| zulässige Fläche | Fläche, an deren Rand alle Anschlussknoten eines Fragments liegen |

**Euler-Formel.** Für eine planare Einbettung gilt $n - m + f = 1 + c$. Jede Fläche hat mindestens drei Kanten am Rand und jede Kante liegt an höchstens zwei Flächenseiten, also $3f \le 2m$; daraus folgt für $n\ge 3$
$$m \le 3n-6 .$$
Ohne Dreiecke (z. B. bipartit) gilt $m \le 2n-4$. Die Schranke ist **notwendig, nicht hinreichend**: $K_{3,3}$ hat $m = 9 \le 12$ und ist nicht planar.

**Satz von Kuratowski (1930).** $G$ ist genau dann planar, wenn $G$ keinen Teilgraphen enthält, der eine Unterteilung von $K_5$ oder $K_{3,3}$ ist.

**Fragmenttest (Demoucron, Malgrange, Pertuiset 1964)** für einen Block: Wähle einen Kreis $C$; $H := C$ mit zwei Flächen. Solange Kanten fehlen: bestimme die Fragmente von $H$ in $G$; für jedes Fragment $B$ die Menge $F(B)$ der zulässigen Flächen. Ist $F(B)=\emptyset$ für ein $B$, ist $G$ nicht planar. Sonst wähle ein $B$ mit $|F(B)|$ minimal, einen Weg $P$ in $B$ zwischen zwei Anschlussknoten und eine Fläche aus $F(B)$; $P$ teilt sie in zwei. Am Ende ist die Flächenliste eine Einbettung.

**Zeuge durch Kantenabbau.** Ist $G$ nichtplanar, streicht man nacheinander jede Kante und lässt sie weg, wenn der Rest nichtplanar bleibt. Das Ergebnis ist ein kantenminimaler nichtplanarer Graph; nach dem Satz von Kuratowski ist er eine Unterteilung von $K_5$ (fünf Knoten vom Grad 4) oder $K_{3,3}$ (sechs Knoten vom Grad 3), alle übrigen Knoten haben Grad 2. Das kostet höchstens $m$ Planaritätstests.

**Literatur.** K. Kuratowski, *Sur le problème des courbes gauches en topologie*, Fundamenta Mathematicae 15 (1930), 271–283. G. Demoucron, Y. Malgrange, R. Pertuiset, *Graphes planaires : reconnaissance et construction de représentations planaires topologiques*, Revue française de recherche opérationnelle 8 (1964), 33–47 (die Bandangabe wird in Quellen teils abweichend genannt). Linearzeit-Verfahren: der Left-Right-Test nach de Fraysseix und Rosenstiehl in der Darstellung von Brandes; er liefert bei Nichtplanarität ebenfalls einen Teilgraphen vom Typ Kuratowski. Beide Angaben wurden per Suche gegen Bibliografie-Einträge geprüft, die Originalarbeiten nicht gelesen.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
