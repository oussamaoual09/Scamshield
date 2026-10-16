"""Styles visuels de ScamShield : palette de couleurs, CSS personnalisé et composants HTML réutilisables."""

import html

import streamlit as st

# Palette unique, partagée par le CSS et par les graphiques Plotly.
# Thème forcé en clair : chaque texte a une couleur explicite selon le fond sur lequel il se trouve.
COULEURS = {
    "fond": "#FFFFFF",
    "bordure": "#E2E8F0",
    "texte": "#0F172A",
    "texte_att": "#475569",
    "principale": "#3B82F6",
    "principale_texte": "#1D4ED8",
    "sur": "#22C55E",
    "suspect": "#F59E0B",
    "arnaque": "#EF4444",
    "ia": "#A78BFA",
    # Cartes et signaux à fond sombre fixe : leurs textes sont clairs
    "carte": "#131C2E",
    "carte_bordure": "#1E293B",
    "signal": "#0F1729",
    "texte_carte": "#F1F5F9",
    "texte_carte_att": "#CBD5E1",
}

# Couleurs de texte des badges et des étiquettes, éclaircies pour rester lisibles sur fond sombre
TEXTE_BADGE = {"sur": "#4ADE80", "suspect": "#FBBF24", "arnaque": "#F87171"}
TEXTE_TAG = {"regle": "#93C5FD", "ia": "#C4B5FD"}

# Règles CSS statiques ; les couleurs passent par les variables --ss-* définies depuis COULEURS
CSS_BASE = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Inter', system-ui, sans-serif; }
.stApp { background: linear-gradient(180deg, #FFFFFF 0%, #EFF6FF 100%) !important; background-attachment: fixed; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: var(--ss-texte_att) !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 1200px; }
.ss-hero { margin-bottom: 1.2rem; }
.ss-titre { font-size: 2.3rem; font-weight: 700; color: var(--ss-texte); margin: 0; letter-spacing: -0.02em; }
.ss-titre span { color: var(--ss-principale_texte); }
.ss-sous-titre { color: var(--ss-texte_att); font-size: 1.02rem; margin: .35rem 0 0 0; }
.ss-carte { background: var(--ss-carte); border: 1px solid var(--ss-carte_bordure); border-radius: 14px; padding: 1.1rem 1.3rem; box-shadow: 0 6px 20px rgba(15,23,42,.18); margin-bottom: 1rem; }
.ss-carte, .ss-carte p, .ss-carte h1, .ss-carte h2, .ss-carte h3, .ss-carte h4 { color: var(--ss-texte_carte) !important; }
.ss-carte .ss-sous-titre { color: var(--ss-texte_carte_att) !important; }
.ss-badge { display: inline-block; padding: .35rem .9rem; border-radius: 999px; font-weight: 600; font-size: .9rem; border: 1px solid; }
.ss-signal { display: flex; gap: .75rem; align-items: flex-start; background: var(--ss-signal) !important; border-left: 3px solid var(--ss-principale); border-radius: 10px; padding: .7rem .9rem; margin: .5rem 0; }
.ss-signal-icone { font-size: 1.25rem; line-height: 1.4; }
.ss-signal-titre { font-weight: 600; color: var(--ss-texte_carte) !important; }
.ss-signal-detail { color: var(--ss-texte_carte_att) !important; font-size: .88rem; margin-top: .15rem; line-height: 1.5; }
.ss-tag { font-size: .72rem; padding: .1rem .5rem; border-radius: 999px; border: 1px solid; margin-left: .45rem; vertical-align: middle; }
.stButton > button { border-radius: 12px; border: 1px solid var(--ss-principale); transition: all .2s ease; font-weight: 600; }
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(59,130,246,.35); border-color: var(--ss-principale); }
.stButton > button[kind="primary"] { background: var(--ss-principale_texte); border-color: var(--ss-principale_texte); color: #FFFFFF !important; }
[data-testid="stMetric"] { background: var(--ss-carte); border: 1px solid var(--ss-carte_bordure); border-radius: 14px; padding: .9rem 1.1rem; box-shadow: 0 4px 14px rgba(15,23,42,.15); }
[data-testid="stMetric"] label, [data-testid="stMetric"] [data-testid="stMetricValue"], [data-testid="stMetric"] [data-testid="stMetricLabel"] { color: var(--ss-texte_carte) !important; }
.stTabs [data-baseweb="tab"] { font-weight: 600; }
div[data-testid="stExpander"] { border: 1px solid var(--ss-bordure); border-radius: 14px; }
.stTextArea textarea { border-radius: 12px; }
@media (max-width: 768px) {
  .ss-titre { font-size: 1.7rem; }
  .block-container { padding-left: 1rem; padding-right: 1rem; }
}
"""


def couleur_niveau(code: str) -> str:
    """Renvoie la couleur associée à un niveau de risque : sur, suspect ou arnaque."""
    return COULEURS.get(code, COULEURS["principale"])


def badge_niveau(code: str, libelle: str) -> str:
    """Renvoie un badge HTML coloré selon le niveau de risque, avec un texte lisible sur fond sombre."""
    couleur = couleur_niveau(code)
    texte = TEXTE_BADGE.get(code, COULEURS["texte_carte"])
    return (
        f'<span class="ss-badge" style="color:{texte};border-color:{couleur};background:{couleur}33;">'
        f"{html.escape(libelle)}</span>"
    )


def carte_signal(icone: str, titre: str, detail: str, source: str) -> str:
    """Renvoie une carte HTML décrivant un signal suspect, avec son origine (règle ou IA)."""
    tag = TEXTE_TAG["ia"] if "IA" in source else TEXTE_TAG["regle"]
    couleur_bordure = COULEURS["ia"] if "IA" in source else COULEURS["principale"]
    detail_html = f'<div class="ss-signal-detail">{html.escape(detail)}</div>' if detail else ""
    return (
        '<div class="ss-signal">'
        f'<div class="ss-signal-icone">{icone}</div>'
        "<div>"
        f'<div class="ss-signal-titre">{html.escape(titre)}'
        f'<span class="ss-tag" style="color:{tag};border-color:{couleur_bordure};">{html.escape(source)}</span>'
        "</div>"
        f"{detail_html}"
        "</div>"
        "</div>"
    )


def _variables_css() -> str:
    """Génère les variables CSS à partir de la palette COULEURS."""
    declarations = " ".join(f"--ss-{nom}: {valeur};" for nom, valeur in COULEURS.items())
    return f":root {{ {declarations} }}"


def injecter_css() -> None:
    """Injecte le CSS personnalisé dans la page Streamlit."""
    st.markdown(f"<style>{_variables_css()}{CSS_BASE}</style>", unsafe_allow_html=True)
