"""Graphiques Plotly de ScamShield : thème sombre unique, fond transparent et couleurs partagées."""

import pandas as pd
import plotly.graph_objects as go

from rules import CATEGORIES, CATEGORIES_RADAR, NIVEAUX
from styles import COULEURS, couleur_niveau

# Couleurs des types d'arnaques dans le graphique en anneau
PALETTE_TYPES = ["#3B82F6", "#A78BFA", "#F59E0B", "#EF4444", "#22C55E", "#64748B"]

# Correspondance libellé de niveau -> code interne
CODE_PAR_NIVEAU = {libelle: code for code, libelle in NIVEAUX.items()}


def _rgba(couleur: str, alpha: float) -> str:
    """Convertit une couleur hexadécimale en rgba avec la transparence demandée."""
    rouge, vert, bleu = (int(couleur[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({rouge},{vert},{bleu},{alpha})"


def _couper(texte: str, longueur: int) -> str:
    """Raccourcit un libellé trop long pour un axe de graphique."""
    return texte if len(texte) <= longueur else texte[: longueur - 1] + "…"


def _appliquer_theme(figure: go.Figure, hauteur: int = 320) -> go.Figure:
    """Applique le thème sombre commun à tous les graphiques : fond transparent, police et marges."""
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COULEURS["texte"]),
        margin=dict(l=16, r=16, t=48, b=16),
        height=hauteur,
    )
    return figure


def _figure_vide(message: str, hauteur: int = 320) -> go.Figure:
    """Crée un graphique vide qui affiche un message d'invitation."""
    figure = go.Figure()
    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=15, color=COULEURS["texte_att"]),
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return _appliquer_theme(figure, hauteur)


def graphique_jauge(score: int, niveau_code: str) -> go.Figure:
    """Jauge du score de risque avec trois zones colorées : Sûr, Suspect et Arnaque probable."""
    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": " / 100", "font": {"size": 44, "color": COULEURS["texte"]}},
            title={"text": "Niveau de risque", "font": {"size": 18, "color": COULEURS["texte"]}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": COULEURS["texte_att"]},
                "bar": {"color": couleur_niveau(niveau_code), "thickness": 0.28},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 30], "color": _rgba(COULEURS["sur"], 0.25)},
                    {"range": [30, 65], "color": _rgba(COULEURS["suspect"], 0.25)},
                    {"range": [65, 100], "color": _rgba(COULEURS["arnaque"], 0.25)},
                ],
            },
        )
    )
    return _appliquer_theme(figure, 300)


def graphique_contributions(signaux: list[dict]) -> go.Figure:
    """Barres horizontales : contribution de chaque signal au score final."""
    if not signaux:
        return _figure_vide("Aucun signal à afficher")
    affiches = list(reversed(signaux[:8]))
    couleurs = [COULEURS["ia"] if "IA" in signal["source"] else COULEURS["principale"] for signal in affiches]
    maximum = max(signal["points"] for signal in affiches)
    figure = go.Figure(
        go.Bar(
            x=[signal["points"] for signal in affiches],
            y=[_couper(signal["libelle"], 40) for signal in affiches],
            orientation="h",
            marker=dict(color=couleurs),
            text=[f"{signal['points']:g} pts" for signal in affiches],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}<br>Contribution : %{x} pts<extra></extra>",
        )
    )
    figure.update_xaxes(title="Points ajoutés au score", range=[0, max(10, maximum * 1.25)], gridcolor=COULEURS["bordure"])
    figure.update_yaxes(automargin=True)
    return _appliquer_theme(figure, max(260, 46 * len(affiches) + 80))


def graphique_radar(scores: dict) -> go.Figure:
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
            angularaxis=dict(gridcolor=COULEURS["bordure"], linecolor=COULEURS["bordure"]),
        )
    )
    return _appliquer_theme(figure, 340)


def graphique_repartition_types(df: pd.DataFrame) -> go.Figure:
    """Camembert en anneau : répartition des types d'arnaques détectés, hors « sûr »."""
    if df.empty:
        return _figure_vide("Pas encore de données")
    detectes = df.loc[df["type"] != "sur", "type"].value_counts()
    if detectes.empty:
        return _figure_vide("Aucune arnaque détectée pour l'instant")
    etiquettes = [CATEGORIES.get(code, CATEGORIES["autre"])["court"] for code in detectes.index]
    figure = go.Figure(
        go.Pie(
            labels=etiquettes,
            values=detectes.values,
            hole=0.55,
            sort=False,
            marker=dict(colors=PALETTE_TYPES, line=dict(color=COULEURS["fond"], width=2)),
            textinfo="percent",
            hovertemplate="%{label} : %{value} analyse(s)<extra></extra>",
        )
    )
    figure.update_layout(
        showlegend=True,
        legend=dict(orientation="h", y=-0.1),
        annotations=[
            dict(
                text=f"<b>{int(detectes.sum())}</b><br>détection(s)",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14),
            )
        ],
    )
    return _appliquer_theme(figure, 340)


def graphique_distribution(df: pd.DataFrame) -> go.Figure:
    """Histogramme de la distribution des scores, avec les zones Sûr, Suspect et Arnaque en fond."""
    if df.empty:
        return _figure_vide("Pas encore de données")
    figure = go.Figure(
        go.Histogram(
            x=df["score"],
            xbins=dict(start=0, end=100, size=10),
            marker=dict(color=COULEURS["principale"], line=dict(color=COULEURS["fond"], width=1)),
            hovertemplate="Score %{x}<br>%{y} analyse(s)<extra></extra>",
        )
    )
    figure.add_vrect(x0=0, x1=30, fillcolor=COULEURS["sur"], opacity=0.08, line_width=0)
    figure.add_vrect(x0=30, x1=65, fillcolor=COULEURS["suspect"], opacity=0.08, line_width=0)
    figure.add_vrect(x0=65, x1=100, fillcolor=COULEURS["arnaque"], opacity=0.08, line_width=0)
    figure.update_xaxes(title="Score de risque", range=[0, 100], gridcolor=COULEURS["bordure"])
    figure.update_yaxes(title="Nombre d'analyses", gridcolor=COULEURS["bordure"])
    figure.update_layout(bargap=0.08)
    return _appliquer_theme(figure, 340)


def graphique_evolution(df: pd.DataFrame) -> go.Figure:
    """Courbe de l'évolution du score dans le temps, avec les points colorés selon le niveau."""
    if df.empty:
        return _figure_vide("Pas encore de données")
    dates = pd.to_datetime(df["date"], errors="coerce")
    couleurs = [couleur_niveau(CODE_PAR_NIVEAU.get(niveau, "suspect")) for niveau in df["niveau"]]
    libelles = [CATEGORIES.get(code, CATEGORIES["autre"])["court"] for code in df["type"]]
    figure = go.Figure(
        go.Scatter(
            x=dates,
            y=df["score"],
            mode="lines+markers",
            line=dict(color=COULEURS["principale"], width=2),
            marker=dict(size=10, color=couleurs, line=dict(color=COULEURS["fond"], width=1)),
            text=libelles,
            hovertemplate="%{x|%d/%m/%Y %H:%M}<br>Score : %{y}/100<br>%{text}<extra></extra>",
        )
    )
    figure.add_hline(y=30, line=dict(color=COULEURS["sur"], dash="dot"))
    figure.add_hline(y=65, line=dict(color=COULEURS["arnaque"], dash="dot"))
    figure.update_xaxes(title="Date", gridcolor=COULEURS["bordure"])
    figure.update_yaxes(title="Score", range=[0, 100], gridcolor=COULEURS["bordure"])
    return _appliquer_theme(figure, 320)
