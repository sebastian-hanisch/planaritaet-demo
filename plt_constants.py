"""Konstanten: Regler-Grenzen, Rechengrenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 6, 60, 14                     # Knoten; Aufwand des Fragmenttests ~ O(n^2) (gemessen etwa n^2,1), bei n = 60 wenige Millisekunden
DENSITY_MIN, DENSITY_MAX, DEFAULT_DENSITY = 5, 100, 100  # Kanten in Prozent der Höchstzahl 3n − 6 planarer Graphen (Euler-Schranke)
EXTRA_MIN, EXTRA_MAX, DEFAULT_EXTRA = 0, 10, 0          # Zusatzkanten zwischen zufälligen Paaren, zusätzlich zum gewählten Netz
SEED_MAX, DEFAULT_SEED = 999999, 5
SWEEP_SEEDS = tuple(range(100000, 100005))              # feste Instanzen für alle Vergleiche: nie ein einzelner Seed als Befund

# Netztypen: welche Kanten die Dichte bestimmt (die Anzahl m = Dichte % von 3n − 6 ist für alle gleich)
NET_TYPES = {
    "delaunay": "Karte (Delaunay-Netz aus Standorten)",
    "grid": "Raster (Gitter mit Diagonalen)",
    "gnc": "Zufallsverbindungen (beliebige Paare)",
}
DEFAULT_NET = "delaunay"
NET_HELP = (
    "Alle drei Netztypen haben bei gleicher Dichte gleich viele Kanten m = Dichte % von 3n − 6, der Höchstzahl, die ein planarer Graph haben darf. "
    "Karte: zufällige Standorte, die Kanten sind Kanten ihrer Delaunay-Triangulierung (planar, solange keine Zusatzkanten dazukommen). "
    "Raster: ein Gitter mit Diagonalen in den Zellen, zuerst die Gitterkanten, dann die Diagonalen (planar). "
    "Zufallsverbindungen: m zufällig gewählte Paare, ohne Rücksicht auf die Lage. Hat ein Typ weniger Kanten, als die Dichte verlangt, bekommt er alle, die er hat."
)
DENSITY_LABEL = "Dichte (% von 3n − 6 Kanten)"

# Rechengrenzen (Schritte = Besuche von Nachbarn und Prüfungen von Flächen im Fragmenttest)
WITNESS_MAX_EDGES = 400      # größte Kantenzahl des Blocks, bei der der Zeuge durch Kantenabbau gesucht wird (m Tests)
TORONTO_CROSS_CELL = 120.0   # Zellgröße (Meter) des Rasters, das die Streckenkreuzungen der Karte beschleunigt

# Lehrbuch-Graphen
HAND_GRAPHS = ("K4", "Würfel", "Oktaeder", "K5 minus eine Kante", "K5", "K3,3", "Petersen-Graph", "Wagner-Graph", "K3,3 mit Unterteilungen")
DEFAULT_HAND = "K5"

# Experimente
SHARE_NS = (20, 40)
SHARE_DENSITIES = (10, 20, 30, 40, 50, 60, 80, 100)
SHARE_SAMPLES = 100
PLUS_NS = (30, 60)
PLUS_KS = (0, 1, 2, 3, 5)
PLUS_DENSITY = 60            # Anteil der Delaunay-Kanten (in Prozent von 3n − 6), auf den das planare Netz verdünnt wird
PLUS_SAMPLES = 100
COST_NS = (20, 40, 80, 160, 320)
COST_SAMPLES = 5             # Instanzen je Größe (Median)

# Farben
COLOR_BASE = "#2F6B65"       # bereits eingebettet
COLOR_PATH = "#c0504d"       # der Weg, der gerade eingefügt wird
COLOR_FRAGMENT = "#e0a030"   # das gewählte Fragment (Brücke)
COLOR_WAIT = "#9fb3c8"       # noch nicht eingebettet
COLOR_BAD = "#8b1a1a"        # Fragment ohne zulässige Fläche
COLOR_EDGE = "rgba(150,150,150,0.45)"
COLOR_PALETTE = ("#4c78a8", "#e0a030", "#c0504d", "#8c6bb1", "#2F6B65", "#6baed6", "#8c564b", "#7f7f7f", "#bcbd22", "#17becf")

PRESETS = {
    "Lehrbeispiel: eine Karte": {"net": "delaunay", "n": 14, "density": 100, "extra": 0, "seed": 5},
    "Eine Kante zu viel": {"net": "delaunay", "n": 14, "density": 100, "extra": 1, "seed": 5},
    "Raster mit Fernkante": {"net": "grid", "n": 25, "density": 58, "extra": 1, "seed": 25},
    "Zufall: knapp planar": {"net": "gnc", "n": 20, "density": 40, "extra": 0, "seed": 2},
    "Zufall: schon nichtplanar": {"net": "gnc", "n": 20, "density": 50, "extra": 0, "seed": 1},
}
PRESET_HELP = {
    "Lehrbeispiel: eine Karte": "14 Standorte mit allen Kanten ihrer Delaunay-Triangulierung (an der äußeren Hülle fehlen gegenüber 3n − 6 einige Kanten): planar. Der Fragmenttest bettet den Graphen Weg für Weg ein.",
    "Eine Kante zu viel": "Dieselbe Karte mit einer einzigen Zusatzkante zwischen zwei zufälligen Standorten. Sie macht den Graphen nichtplanar, obwohl er die Schranke 3n − 6 noch nicht erreicht: der Test scheitert, und der Kantenabbau liefert einen Zeugen.",
    "Raster mit Fernkante": "Ein Raster ohne Diagonalen, dazu eine Kante zwischen zwei nicht benachbarten Knoten. Der Test scheitert und der Kantenabbau liefert einen Zeugen, obwohl die Zeichnung nur wenige Kreuzungen zeigt.",
    "Zufall: knapp planar": "Zufällig gewählte Verbindungen bei 40 % der Höchstkantenzahl: In der Kreis-Zeichnung kreuzen sich viele Kanten, trotzdem ist der Graph planar. Nicht die Zeichnung, die Flächenliste belegt es.",
    "Zufall: schon nichtplanar": "Zufällige Verbindungen bei 50 % der Höchstkantenzahl, weit unter der Euler-Schranke 3n − 6: der Graph ist schon nichtplanar, und der Zeuge zeigt warum.",
}
