"""Styles visuels de ScamShield : palette de couleurs, CSS personnalisé et composants HTML réutilisables."""

import html

import streamlit as st

# Palette unique, partagée par le CSS et par les graphiques Plotly
COULEURS = {
    "fond": "#0B1220",
    "carte": "#131C2E",
    "bordure": "#1E293B",
    "texte": "#F1F5F9",
    "texte_att": "#94A3B8",
    "principale": "#3B82F6",
    "sur": "#22C55E",
    "suspect": "#F59E0B",
    "arnaque": "#EF4444",
    "ia": "#A78BFA",
}

# Règles CSS statiques ; les couleurs passent par les variables --ss-* définies depuis COULEURS
CSS_BASE = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Inter', system-ui, sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 1200px; }
.ss-hero { margin-bottom: 1.2rem; }
.ss-titre { font-size: 2.3rem; font-weight: 700; color: var(--ss-texte); margin: 0; letter-spacing: -0.02em; }
.ss-titre span { color: var(--ss-principale); }
.ss-sous-titre { color: var(--ss-texte_att); font-size: 1.02rem; margin: .35rem 0 0 0; }
.ss-carte { background: var(--ss-carte); border: 1px solid var(--ss-bordure); border-radius: 14px; padding: 1.1rem 1.3rem; box-shadow: 0 6px 20px rgba(0,0,0,.25); margin-bottom: 1rem; }
.ss-badge { display: inline-block; padding: .35rem .9rem; border-radius: 999px; font-weight: 600; font-size: .9rem; border: 1px solid; }
.ss-signal { display: flex; gap: .75rem; align-items: flex-start; background: #0F1729; border-left: 3px solid var(--ss-principale); border-radius: 10px; padding: .7rem .9rem; margin: .5rem 0; }
.ss-signal-icone { font-size: 1.25rem; line-height: 1.4; }
.ss-signal-titre { font-weight: 600; color: var(--ss-texte); }
.ss-signal-detail { color: var(--ss-texte_att); font-size: .88rem; margin-top: .15rem; line-height: 1.5; }
.ss-tag { font-size: .72rem; padding: .1rem .5rem; border-radius: 999px; border: 1px solid; margin-left: .45rem; vertical-align: middle; }
.stButton > button { border-radius: 12px; border: 1px solid var(--ss-principale); transition: all .2s ease; font-weight: 600; }
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(59,130,246,.35); border-color: var(--ss-principale); }
.stButton > button[kind="primary"] { background: var(--ss-principale); color: #FFFFFF; }
[data-testid="stMetric"] { background: var(--ss-carte); border: 1px solid var(--ss-bordure); border-radius: 14px; padding: .9rem 1.1rem; box-shadow: 0 4px 14px rgba(0,0,0,.2); }
.stTabs [data-baseweb="tab"] { font-weight: 600; }
div[data-testid="stExpander"] { background: var(--ss-carte); border: 1px solid var(--ss-bordure); border-radius: 14px; }
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
    """Renvoie un badge HTML coloré selon le niveau de risque."""
    couleur = couleur_niveau(code)
    return (
        f'<span class="ss-badge" style="color:{couleur};border-color:{couleur};background:{couleur}22;">'
        f"{html.escape(libelle)}</span>"
    )


def carte_signal(icone: str, titre: str, detail: str, source: str) -> str:
    """Renvoie une carte HTML décrivant un signal suspect, avec son origine (règle ou IA)."""
    couleur_tag = COULEURS["ia"] if "IA" in source else COULEURS["principale"]
    detail_html = f'<div class="ss-signal-detail">{html.escape(detail)}</div>' if detail else ""
    return (
        '<div class="ss-signal">'
        f'<div class="ss-signal-icone">{icone}</div>'
        "<div>"
        f'<div class="ss-signal-titre">{html.escape(titre)}'
        f'<span class="ss-tag" style="color:{couleur_tag};border-color:{couleur_tag};">{html.escape(source)}</span>'
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
