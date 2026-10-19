"""Graphiques Plotly de ScamShield : fond transparent, palette partagée, coins arrondis et titres en gras."""

import pandas as pd
import plotly.graph_objects as go

from rules import CATEGORIES, CATEGORIES_RADAR, NIVEAUX
from styles import COULEURS, couleur_niveau

# Couleurs des types d'arnaques dans le graphique en anneau.
# Nuances foncées : les étiquettes blanches des parts doivent garder un contraste d'au moins 4,5:1.
PALETTE_TYPES = ["#1D4ED8", "#6D28D9", "#B45309", "#B91C1C", "#15803D", "#475569"]

# Correspondance libellé de niveau -> code interne
CODE_PAR_NIVEAU = {libelle: code for code, libelle in NIVEAUX.items()}


def _rgba(couleur: str, alpha: float) -> str:
    """Convertit une couleur hexadécimale en rgba avec la transparence demandée."""
    rouge, vert, bleu = (int(couleur[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({rouge},{vert},{bleu},{alpha})"


def _melanger(couleur_a: str, couleur_b: str, position: float) -> str:
    """Mélange deux couleurs hexadécimales selon une position entre 0 et 1."""
    canaux = []
    for index in (1, 3, 5):
        depart, arrivee = int(couleur_a[index:index + 2], 16), int(couleur_b[index:index + 2], 16)
        canaux.append(int(round(depart + (arrivee - depart) * position)))
    return "#" + "".join(f"{canal:02X}" for canal in canaux)


def _zones_degrade(nombre: int = 24, transparence: float = 0.5) -> list[dict]:
    """Construit les zones d'une jauge en dégradé continu vert → orange → rouge."""
    zones = []
    for index in range(nombre):
        position = index / (nombre - 1)
        if position <= 0.5:
            couleur = _melanger(COULEURS["sur"], COULEURS["suspect"], position * 2)
        else:
            couleur = _melanger(COULEURS["suspect"], COULEURS["arnaque"], (position - 0.5) * 2)
        zones.append(
            {"range": [100 * index / nombre, 100 * (index + 1) / nombre], "color": _rgba(couleur, transparence)}
        )
    return zones


def _couper(texte: str, longueur: int) -> str:
    """Raccourcit un libellé trop long pour un axe de graphique."""
    return texte if len(texte) <= longueur else texte[: longueur - 1] + "…"


def _gras(texte: str) -> str:
    """Renvoie un titre en gras : Plotly affiche un sous-ensemble de balises HTML."""
    return f"<b>{texte}</b>"


def _appliquer_theme(figure: go.Figure, hauteur: int = 320, titre: str | None = None) -> go.Figure:
    """Applique le thème commun : fond transparent, police Inter, légende claire et titre en gras."""
    figure.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COULEURS["texte"]),
        margin=dict(l=16, r=16, t=58 if titre else 40, b=16),
        height=hauteur,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
            font=dict(color=COULEURS["texte_att"], size=12),
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor=COULEURS["bordure"],
            font=dict(color=COULEURS["texte"], family="Inter, sans-serif", size=12),
        ),
    )
    if titre:
        figure.update_layout(
            title=dict(
                text=_gras(titre),
                x=0.01,
                xanchor="left",
                y=0.97,
                yanchor="top",
                font=dict(size=15, color=COULEURS["texte"]),
            )
        )
    return figure


def _figure_vide(message: str, titre: str | None = None, hauteur: int = 320) -> go.Figure:
    """Crée un graphique vide soigné : icône, message centré et titre en gras."""
    figure = go.Figure()
    figure.add_annotation(
        text="📭",
        x=0.5,
        y=0.62,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=30, color=COULEURS["texte_att"]),
    )
    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.44,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=14, color=COULEURS["texte_att"]),
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return _appliquer_theme(figure, hauteur, titre)


def graphique_jauge(score: int, titre: str = "Niveau de risque") -> go.Figure:
    """Jauge du score de risque, avec un dégradé continu du vert au rouge."""
    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": " / 100", "font": {"size": 46, "color": COULEURS["texte"]}},
            title={"text": _gras(titre), "font": {"size": 16, "color": COULEURS["texte"]}},
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickcolor": COULEURS["texte_att"],
                    "tickfont": {"size": 12, "color": COULEURS["texte_att"]},
                },
                "bar": {"color": COULEURS["texte"], "thickness": 0.22},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": _zones_degrade(),
            },
        )
    )
    return _appliquer_theme(figure, 300)


def graphique_contributions(signaux: list[dict], titre: str = "Contribution de chaque signal") -> go.Figure:
    """Barres horizontales arrondies : contribution de chaque signal, une couleur et une légende par source."""
    if not signaux:
        return _figure_vide("Aucun signal à afficher", titre)
    affiches = list(reversed(signaux[:8]))
    libelles = [_couper(signal["libelle"], 40) for signal in affiches]
    maximum = max(signal["points"] for signal in affiches)
    sources = (
        ("Moteur de règles", COULEURS["principale"], False),
        ("Intelligence artificielle", COULEURS["ia"], True),
    )
    figure = go.Figure()
    for nom, couleur, est_ia in sources:
        points = [signal["points"] if ("IA" in signal["source"]) == est_ia else None for signal in affiches]
        figure.add_trace(
            go.Bar(
                x=points,
                y=libelles,
                orientation="h",
                name=nom,
                marker=dict(color=couleur, cornerradius=6),
                text=[f"{point:g} pts" if point is not None else "" for point in points],
                textposition="outside",
                textfont=dict(color=COULEURS["texte"]),
                cliponaxis=False,
                hovertemplate=f"%{{y}}<br>{nom} : %{{x}} pts<extra></extra>",
            )
        )
    figure.update_layout(barmode="overlay", bargap=0.35)
    figure.update_xaxes(
        title="Points ajoutés au score",
        range=[0, max(10, maximum * 1.25)],
        gridcolor=COULEURS["bordure"],
        zeroline=False,
    )
    figure.update_yaxes(automargin=True, categoryorder="array", categoryarray=libelles)
    return _appliquer_theme(figure, max(260, 48 * len(affiches) + 90), titre)


def graphique_radar(scores: dict, titre: str = "Profil de risque par type") -> go.Figure:
    """Radar du profil de risque par type d'arnaque : phishing, placement, Ponzi, prêt et gain."""
    etiquettes = [CATEGORIES[code]["court"] for code in CATEGORIES_RADAR]
    valeurs = [round(scores.get(code, 0)) for code in CATEGORIES_RADAR]
    figure = go.Figure(
        go.Scatterpolar(
            r=valeurs + valeurs[:1],
            theta=etiquettes + etiquettes[:1],
            fill="toself",
            line=dict(color=COULEURS["principale"], width=2),
            fillcolor=_rgba(COULEURS["principale"], 0.3),
            hovertemplate="%{theta} : %{r}/100<extra></extra>",
        )
    )
    figure.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                range=[0, 100],
                gridcolor=COULEURS["bordure"],
                linecolor=COULEURS["bordure"],
                tickfont=dict(size=10, color=COULEURS["texte_att"]),
            ),
            angularaxis=dict(
                gridcolor=COULEURS["bordure"],
                linecolor=COULEURS["bordure"],
                tickfont=dict(size=12, color=COULEURS["texte"]),
            ),
        )
    )
    return _appliquer_theme(figure, 340, titre)


def graphique_repartition_types(df: pd.DataFrame, titre: str = "Types d'arnaques détectés") -> go.Figure:
    """Camembert en anneau : répartition des types d'arnaques détectés, hors « sûr »."""
    if df.empty:
        return _figure_vide("Aucune donnée pour l'instant", titre, 340)
    detectes = df.loc[df["type"] != "sur", "type"].value_counts()
    if detectes.empty:
        return _figure_vide("Aucune arnaque détectée pour l'instant", titre, 340)
    etiquettes = [CATEGORIES.get(code, CATEGORIES["autre"])["court"] for code in detectes.index]
    figure = go.Figure(
        go.Pie(
            labels=etiquettes,
            values=detectes.values,
            hole=0.55,
            sort=False,
            marker=dict(colors=PALETTE_TYPES, line=dict(color=COULEURS["fond"], width=2)),
            textinfo="percent",
            textfont=dict(color="#FFFFFF"),
            hovertemplate="%{label} : %{value} analyse(s)<extra></extra>",
        )
    )
    figure.update_layout(
        showlegend=True,
        annotations=[
            dict(
                text=f"<b>{int(detectes.sum())}</b><br>détection(s)",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14, color=COULEURS["texte"]),
            )
        ],
    )
    return _appliquer_theme(figure, 340, titre)


def graphique_distribution(df: pd.DataFrame, titre: str = "Distribution des scores") -> go.Figure:
    """Histogramme arrondi de la distribution des scores, avec les zones Sûr, Suspect et Arnaque en fond."""
    if df.empty:
        return _figure_vide("Aucune donnée pour l'instant", titre, 340)
    figure = go.Figure(
        go.Histogram(
            x=df["score"],
            xbins=dict(start=0, end=100, size=10),
            marker=dict(color=COULEURS["principale"], cornerradius=6, line=dict(color=COULEURS["fond"], width=1)),
            hovertemplate="Score %{x}<br>%{y} analyse(s)<extra></extra>",
        )
    )
    figure.add_vrect(x0=0, x1=30, fillcolor=COULEURS["sur"], opacity=0.08, line_width=0)
    figure.add_vrect(x0=30, x1=65, fillcolor=COULEURS["suspect"], opacity=0.08, line_width=0)
    figure.add_vrect(x0=65, x1=100, fillcolor=COULEURS["arnaque"], opacity=0.08, line_width=0)
    figure.update_xaxes(title="<b>Score de risque</b>", range=[0, 100], gridcolor=COULEURS["bordure"], zeroline=False)
    figure.update_yaxes(title="<b>Nombre d'analyses</b>", gridcolor=COULEURS["bordure"], zeroline=False)
    figure.update_layout(bargap=0.12)
    return _appliquer_theme(figure, 340, titre)


def graphique_evolution(df: pd.DataFrame, titre: str = "Évolution du score dans le temps") -> go.Figure:
    """Courbe de l'évolution du score dans le temps, avec les points colorés selon le niveau."""
    if df.empty:
        return _figure_vide("Aucune donnée pour l'instant", titre)
    dates = pd.to_datetime(df["date"], errors="coerce")
    couleurs = [couleur_niveau(CODE_PAR_NIVEAU.get(niveau, "suspect")) for niveau in df["niveau"]]
    libelles = [CATEGORIES.get(code, CATEGORIES["autre"])["court"] for code in df["type"]]
    figure = go.Figure(
        go.Scatter(
            x=dates,
            y=df["score"],
            mode="lines+markers",
            name="Score de risque",
            line=dict(color=COULEURS["principale"], width=2, shape="spline"),
            marker=dict(size=10, color=couleurs, line=dict(color=COULEURS["fond"], width=1)),
            text=libelles,
            hovertemplate="%{x|%d/%m/%Y %H:%M}<br>Score : %{y}/100<br>%{text}<extra></extra>",
        )
    )
    figure.add_hline(y=30, line=dict(color=COULEURS["sur"], dash="dot"))
    figure.add_hline(y=65, line=dict(color=COULEURS["arnaque"], dash="dot"))
    figure.update_xaxes(title="<b>Date</b>", gridcolor=COULEURS["bordure"])
    figure.update_yaxes(title="<b>Score</b>", range=[0, 100], gridcolor=COULEURS["bordure"])
    return _appliquer_theme(figure, 320, titre)
