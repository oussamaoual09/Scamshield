"""Design system de ScamShield : palette unique, variables CSS, espacements et composants HTML réutilisables."""

import html
import re

import streamlit as st

# ---------------------------------------------------------------------------
# Palette unique (style SaaS fintech) : un seul bleu principal, des accents
# sémantiques (vert, orange, rouge) et une gamme de gris.
# ---------------------------------------------------------------------------
COULEURS = {
    "fond": "#FFFFFF",
    "fond_degrade": "#EFF6FF",
    "surface": "#FFFFFF",
    "surface_alt": "#F8FAFC",
    "bordure": "#E2E8F0",
    "bordure_forte": "#CBD5E1",
    "texte": "#0F172A",
    "texte_att": "#475569",
    "texte_discret": "#64748B",
    "principale": "#2563EB",
    "principale_foncee": "#1D4ED8",
    "principale_texte": "#1D4ED8",
    "principale_claire": "#EFF6FF",
    "principale_moyenne": "#DBEAFE",
    "ia": "#7C3AED",
    "sur": "#16A34A",
    "suspect": "#D97706",
    "arnaque": "#DC2626",
    "gris": "#64748B",
    # Alias conservés pour les graphiques et les cartes déjà en place
    "carte": "#FFFFFF",
    "carte_bordure": "#E2E8F0",
    "signal": "#F8FAFC",
    "texte_carte": "#0F172A",
    "texte_carte_att": "#475569",
}

# Textes des badges et des étiquettes, assombris pour rester lisibles sur fond teinté
TEXTE_BADGE = {"sur": "#166534", "suspect": "#92400E", "arnaque": "#991B1B"}
TEXTE_TAG = {"regle": "#1D4ED8", "ia": "#6D28D9"}

# Verdict affiché pour chaque niveau de risque : libellé, icône et couleurs
VERDICTS = {
    "sur": {"libelle": "Sûr", "icone": "✅", "couleur": COULEURS["sur"], "texte": TEXTE_BADGE["sur"]},
    "suspect": {"libelle": "Prudence", "icone": "⚠️", "couleur": COULEURS["suspect"], "texte": TEXTE_BADGE["suspect"]},
    "arnaque": {"libelle": "Arnaque probable", "icone": "⛔", "couleur": COULEURS["arnaque"], "texte": TEXTE_BADGE["arnaque"]},
}

# Couleur de l'icône de chaque type d'arnaque, prise dans la palette
CATEGORIE_COULEUR = {
    "phishing": COULEURS["principale"],
    "faux_placement": COULEURS["ia"],
    "ponzi": COULEURS["suspect"],
    "faux_pret": COULEURS["arnaque"],
    "faux_gain": COULEURS["gris"],
    "autre": COULEURS["texte_discret"],
    "sur": COULEURS["sur"],
}

# Variantes accentuées d'une lettre : permet de retrouver un mot normalisé dans le texte d'origine
VARIANTES = {
    "a": "aàâä",
    "c": "cç",
    "e": "eéèêë",
    "i": "iîïí",
    "o": "oôö",
    "u": "uûüù",
    "y": "yÿ",
    "ا": "اأإآ",
    "ي": "يىئ",
    "و": "وؤ",
}

# Règles CSS statiques ; les couleurs et les espacements passent par les variables --ss-*
CSS_BASE = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
/* Police Inter limitée aux éléments de texte : les icônes Material gardent leur police de ligatures */
html, body, .stApp,
.stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
.stApp label, .stApp button, .stApp input, .stApp textarea, .stApp select, .stApp li,
.stApp [class*="ss-"],
.stApp [data-testid="stMetricValue"], .stApp [data-testid="stMetricLabel"], .stApp [data-testid="stMetricDelta"],
.stApp [data-testid="stTooltipContent"], .stApp [data-testid="stToast"]
{ font-family: 'Inter', system-ui, sans-serif !important; }
/* Icônes Material Symbols : police des ligatures, à ne jamais remplacer par Inter */
[data-testid="stIconMaterial"], .material-symbols-rounded, [class*="material-symbols"] { font-family: "Material Symbols Rounded" !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: var(--ss-espace-6); padding-bottom: var(--ss-espace-7); max-width: 1180px; }
.stApp { background: linear-gradient(180deg, var(--ss-fond) 0%, var(--ss-fond_degrade) 100%) !important; background-attachment: fixed; }
[data-testid="stHeader"] { background: transparent; }
h1, h2, h3, h4 { color: var(--ss-texte); }
p, li, label, .stMarkdown { color: var(--ss-texte); }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: var(--ss-texte_att) !important; }
hr { border-color: var(--ss-bordure); }

/* --- Hero --- */
.ss-hero { position: relative; overflow: hidden; border-radius: var(--ss-rayon); border: 1px solid var(--ss-principale_moyenne); background: linear-gradient(135deg, var(--ss-fond_degrade) 0%, var(--ss-principale_moyenne) 52%, var(--ss-surface) 100%); box-shadow: var(--ss-ombre-hero); padding: var(--ss-espace-6) var(--ss-espace-6); margin-bottom: var(--ss-espace-6); }
.ss-hero::before, .ss-hero::after { content: ""; position: absolute; border-radius: 50%; }
.ss-hero::before { width: 320px; height: 320px; top: -160px; right: -80px; background: radial-gradient(circle, rgba(37,99,235,.18) 0%, rgba(37,99,235,0) 70%); }
.ss-hero::after { width: 240px; height: 240px; bottom: -140px; right: 220px; background: radial-gradient(circle, rgba(37,99,235,.12) 0%, rgba(37,99,235,0) 70%); }
.ss-hero-contenu { position: relative; z-index: 1; max-width: 720px; }
.ss-hero-bouclier { font-size: 2.1rem; line-height: 1; margin-bottom: var(--ss-espace-2); }
.ss-hero-titre { font-size: 2.5rem !important; font-weight: 700 !important; letter-spacing: -0.02em; color: var(--ss-texte); margin: 0; }
.ss-hero-titre span { color: var(--ss-principale_foncee); }
.ss-hero-accroche { color: var(--ss-texte_att); font-size: 1.05rem !important; line-height: 1.65; margin: var(--ss-espace-3) 0 0 0; }
.ss-pastilles { display: flex; flex-wrap: wrap; gap: var(--ss-espace-2); margin-top: var(--ss-espace-5); }
.ss-pastille { background: rgba(255,255,255,.88); border: 1px solid var(--ss-principale_moyenne); border-radius: var(--ss-rayon-pilule); padding: var(--ss-espace-2) var(--ss-espace-4); color: var(--ss-texte); font-size: .86rem; font-weight: 500; }

/* --- Titres de section --- */
.ss-section { margin: 0 0 var(--ss-espace-5) 0; }
.ss-section-titre { font-size: 1.5rem !important; font-weight: 700 !important; letter-spacing: -0.01em; color: var(--ss-texte); margin: 0; }
.ss-section-sous { color: var(--ss-texte_att); font-size: .98rem !important; margin: var(--ss-espace-1) 0 0 0; }

/* --- Cartes et signaux --- */
.ss-carte { background: var(--ss-surface); border: 1px solid var(--ss-bordure); border-radius: var(--ss-rayon); box-shadow: var(--ss-ombre); padding: var(--ss-espace-5); margin-bottom: var(--ss-espace-4); }
.ss-carte, .ss-carte p, .ss-carte h1, .ss-carte h2, .ss-carte h3, .ss-carte h4 { color: var(--ss-texte) !important; }
.ss-carte .ss-sous-titre { color: var(--ss-texte_att) !important; }
.ss-sous-titre { color: var(--ss-texte_att); font-size: .95rem !important; margin: 0; }
.ss-signal { display: flex; gap: var(--ss-espace-4); align-items: flex-start; background: var(--ss-signal); border: 1px solid var(--ss-bordure); border-left: 3px solid var(--ss-principale); border-radius: var(--ss-rayon); padding: var(--ss-espace-4); margin: var(--ss-espace-2) 0; }
.ss-signal-icone { width: 34px; height: 34px; border-radius: var(--ss-rayon-pilule); display: flex; align-items: center; justify-content: center; font-size: 1rem; flex-shrink: 0; }
.ss-signal-titre { font-weight: 600; color: var(--ss-texte); }
.ss-signal-detail { color: var(--ss-texte_att); font-size: .88rem; margin-top: var(--ss-espace-1); line-height: 1.55; }
.ss-tag { font-size: .72rem; padding: 2px var(--ss-espace-2); border-radius: var(--ss-rayon-pilule); border: 1px solid; margin-left: var(--ss-espace-2); vertical-align: middle; }

/* --- Barre latérale --- */
[data-testid="stSidebar"] { background: var(--ss-surface); border-right: 1px solid var(--ss-bordure); }
[data-testid="stSidebarUserContent"] { padding: var(--ss-espace-5) var(--ss-espace-4); }
.ss-logo { display: flex; gap: var(--ss-espace-3); align-items: center; margin-bottom: var(--ss-espace-5); }
.ss-logo-icone { width: 40px; height: 40px; border-radius: var(--ss-rayon-pilule); background: var(--ss-principale_claire); border: 1px solid var(--ss-principale_moyenne); display: flex; align-items: center; justify-content: center; font-size: 1.15rem; }
.ss-logo-nom { font-weight: 700; font-size: 1.1rem; line-height: 1.2; color: var(--ss-texte); }
.ss-logo-nom span { color: var(--ss-principale_foncee); }
.ss-logo-slogan { color: var(--ss-texte_att); font-size: .78rem; }
.ss-carte-side { background: var(--ss-surface_alt); border: 1px solid var(--ss-bordure); border-radius: var(--ss-rayon); padding: var(--ss-espace-4); margin: var(--ss-espace-5) 0; }
.ss-carte-side-titre { font-weight: 600; color: var(--ss-texte); margin-bottom: var(--ss-espace-2); font-size: .95rem; }
.ss-liste { margin: 0; padding-left: var(--ss-espace-4); color: var(--ss-texte_att); font-size: .86rem; line-height: 1.6; }
.ss-liste li { margin-bottom: var(--ss-espace-1); }
.ss-liste b { color: var(--ss-texte); }
[data-testid="stSidebar"] div[role="radiogroup"] label { display: flex; align-items: center; padding: var(--ss-espace-2) var(--ss-espace-3); border-radius: var(--ss-rayon); margin-bottom: 2px; transition: background .2s ease; }
[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: var(--ss-principale_claire); }
[data-testid="stSidebar"] div[role="radiogroup"] label[data-selected="true"] { background: var(--ss-principale_claire); }
[data-testid="stSidebar"] div[role="radiogroup"] label p { font-size: .95rem; font-weight: 500; color: var(--ss-texte); }

/* --- Comportements des composants Streamlit --- */
/* Cartes blanches : zone d'analyse et cartes de graphiques (clés préfixées par carte_) */
.stVerticalBlock.st-key-zone_analyse, .stVerticalBlock[class*="st-key-carte_"] { background: var(--ss-surface); border: 1px solid var(--ss-bordure) !important; border-radius: var(--ss-rayon) !important; box-shadow: var(--ss-ombre); padding: var(--ss-espace-5); transition: box-shadow .2s ease; }
.stVerticalBlock.st-key-zone_analyse:hover, .stVerticalBlock[class*="st-key-carte_"]:hover { box-shadow: 0 10px 28px rgba(15,23,42,.10); }
[data-testid="stMetric"] { background: var(--ss-surface); border: 1px solid var(--ss-bordure); border-radius: var(--ss-rayon); box-shadow: var(--ss-ombre); padding: var(--ss-espace-4); }
[data-testid="stMetric"] label { color: var(--ss-texte_att) !important; }
[data-testid="stMetric"] [data-testid="stMetricValue"] { color: var(--ss-texte) !important; }
div[data-testid="stExpander"] { background: var(--ss-surface); border: 1px solid var(--ss-bordure); border-radius: var(--ss-rayon); box-shadow: var(--ss-ombre); overflow: hidden; }
div[data-testid="stAlert"] { border-radius: var(--ss-rayon); }
[data-testid="stDataFrame"] { border: 1px solid var(--ss-bordure); border-radius: var(--ss-rayon); overflow: hidden; }
.stTextArea textarea, .stTextInput input, [data-testid="stSelectbox"] div[role="group"] { border-radius: var(--ss-rayon) !important; }
.stTextArea textarea, [data-testid="stSelectbox"] div[role="group"] { background: var(--ss-surface); border-color: var(--ss-bordure_forte); }
.stButton button, .stDownloadButton button { border-radius: var(--ss-rayon); font-weight: 600; transition: all .2s ease; }
.stButton button:hover, .stDownloadButton button:hover { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(37,99,235,.18); }
.stButton button[kind="primary"], .stButton button[data-testid="stBaseButton-primary"] { background: linear-gradient(135deg, var(--ss-principale) 0%, var(--ss-principale_foncee) 100%); border: none; color: #FFFFFF !important; box-shadow: 0 6px 16px rgba(37,99,235,.22); }
.stButton button[kind="secondary"], .stButton button[data-testid="stBaseButton-secondary"] { background: var(--ss-surface); border-color: var(--ss-bordure_forte); color: var(--ss-texte) !important; }
.stDownloadButton button { background: var(--ss-surface); border-color: var(--ss-bordure_forte); color: var(--ss-texte) !important; }
/* Bouton principal de la zone d'analyse : pleine largeur, plus grand, en dégradé */
.st-key-zone_analyse .stElementContainer, .st-key-zone_analyse .stButton, .st-key-zone_analyse .stButton button { width: 100%; }
.st-key-zone_analyse .stButton button { padding: var(--ss-espace-4) var(--ss-espace-5); font-size: 1.02rem; }
.st-key-zone_analyse .stButton button[kind="primary"]:hover { transform: translateY(-2px); box-shadow: 0 12px 26px rgba(37,99,235,.32); }
/* Exemples : petites pastilles cliquables */
.st-key-exemples .stButton button[kind="secondary"], .st-key-exemples .stButton button[data-testid="stBaseButton-secondary"] { width: auto; min-height: 0; padding: var(--ss-espace-2) var(--ss-espace-4); border-radius: var(--ss-rayon-pilule); background: var(--ss-principale_claire); border: 1px solid var(--ss-principale_moyenne); color: var(--ss-principale_foncee) !important; font-size: .84rem; font-weight: 500; }
.st-key-exemples .stButton button:hover { background: var(--ss-principale_moyenne); transform: translateY(-1px); box-shadow: 0 6px 14px rgba(37,99,235,.18); }

/* --- Compteurs --- */
.ss-compteur { background: var(--ss-surface); border: 1px solid var(--ss-bordure); border-radius: var(--ss-rayon); box-shadow: var(--ss-ombre); padding: var(--ss-espace-4) var(--ss-espace-5); transition: transform .2s ease, box-shadow .2s ease; }
.ss-compteur:hover { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(15,23,42,.10); }
.ss-compteur-icone { width: 36px; height: 36px; border-radius: var(--ss-rayon-pilule); display: flex; align-items: center; justify-content: center; font-size: 1.05rem; margin-bottom: var(--ss-espace-3); }
.ss-compteur-valeur { font-size: 1.9rem; font-weight: 700; color: var(--ss-texte); line-height: 1.1; }
.ss-compteur-libelle { color: var(--ss-texte_att); font-size: .85rem; margin-top: var(--ss-espace-1); }

/* --- Verdict, étapes et message analysé --- */
.ss-verdict { display: inline-flex; align-items: center; gap: var(--ss-espace-2); font-size: 1.2rem; font-weight: 700; padding: var(--ss-espace-3) var(--ss-espace-5); border-radius: var(--ss-rayon-pilule); border: 1px solid; }
.ss-etapes { display: flex; flex-direction: column; gap: var(--ss-espace-3); }
.ss-etape { display: flex; gap: var(--ss-espace-3); align-items: flex-start; background: var(--ss-surface_alt); border: 1px solid var(--ss-bordure); border-radius: var(--ss-rayon); padding: var(--ss-espace-3) var(--ss-espace-4); }
.ss-etape-num { width: 28px; height: 28px; border-radius: var(--ss-rayon-pilule); background: var(--ss-principale_foncee); color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: .85rem; flex-shrink: 0; }
.ss-etape-texte { color: var(--ss-texte); font-size: .95rem; line-height: 1.55; }
.ss-message { background: var(--ss-surface_alt); border: 1px solid var(--ss-bordure); border-radius: var(--ss-rayon); padding: var(--ss-espace-4); color: var(--ss-texte); font-size: .95rem; line-height: 1.7; white-space: pre-wrap; }
.ss-surligne { background: #FDE68A; color: var(--ss-texte); border-radius: 4px; padding: 0 3px; font-weight: 600; }

/* --- Animations douces (jamais clignotantes) --- */
@keyframes ss-apparition { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes ss-remplissage { from { clip-path: inset(0 100% 0 0 round var(--ss-rayon)); } to { clip-path: inset(0 0 0 0 round var(--ss-rayon)); } }
.ss-hero, .ss-section, .ss-compteur, .ss-carte, .ss-signal, .ss-etape, .ss-vide, .ss-pied { animation: ss-apparition .4s ease-out backwards; }
.st-key-carte_jauge .js-plotly-plot { animation: ss-remplissage 1.1s cubic-bezier(.22,.61,.36,1) backwards; }
.stHorizontalBlock > div:nth-child(2) .ss-compteur { animation-delay: .06s; }
.stHorizontalBlock > div:nth-child(3) .ss-compteur { animation-delay: .12s; }
.stHorizontalBlock > div:nth-child(4) .ss-compteur { animation-delay: .18s; }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}

/* --- État vide --- */
.ss-vide { display: flex; flex-direction: column; align-items: center; text-align: center; gap: var(--ss-espace-2); background: var(--ss-surface); border: 1px dashed var(--ss-bordure_forte); border-radius: var(--ss-rayon); padding: var(--ss-espace-6) var(--ss-espace-5); }
.ss-vide-icone { width: 48px; height: 48px; border-radius: var(--ss-rayon-pilule); background: var(--ss-principale_claire); display: flex; align-items: center; justify-content: center; font-size: 1.4rem; }
.ss-vide-titre { margin: 0; font-weight: 600; color: var(--ss-texte); }
.ss-vide-detail { margin: 0; color: var(--ss-texte_att); font-size: .9rem !important; }

/* --- Pied de page --- */
.ss-pied { margin-top: var(--ss-espace-7); padding-top: var(--ss-espace-5); border-top: 1px solid var(--ss-bordure); display: flex; flex-wrap: wrap; gap: var(--ss-espace-3); align-items: center; justify-content: space-between; color: var(--ss-texte_att); font-size: .82rem; }
.ss-pied-note { display: flex; align-items: center; gap: var(--ss-espace-2); }

/* --- Éléments cliquables --- */
button, [role="button"], [role="radio"], [role="combobox"], [role="option"], summary, [data-testid="stSidebar"] div[role="radiogroup"] label { cursor: pointer; }
.stTextArea textarea, .stTextInput input { cursor: text; }

/* --- Onglet actif de la barre latérale : pastille de couleur --- */
[data-testid="stSidebar"] div[role="radiogroup"] label { position: relative; }
[data-testid="stSidebar"] div[role="radiogroup"] label::after { content: ""; width: 8px; height: 8px; border-radius: var(--ss-rayon-pilule); background: transparent; margin-left: auto; flex-shrink: 0; transition: background .2s ease, box-shadow .2s ease; }
[data-testid="stSidebar"] div[role="radiogroup"] label[data-selected="true"]::after { background: var(--ss-principale); box-shadow: 0 0 0 3px var(--ss-principale_moyenne); }

@media (max-width: 768px) {
  .ss-hero { padding: var(--ss-espace-5) var(--ss-espace-4); }
  .ss-hero-titre { font-size: 1.8rem !important; }
  .ss-section-titre { font-size: 1.3rem !important; }
  .block-container { padding-left: var(--ss-espace-4); padding-right: var(--ss-espace-4); }
}

/* Téléphone : les colonnes s'empilent et les pastilles prennent toute la largeur */
@media (max-width: 640px) {
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
  [data-testid="stHorizontalBlock"] > .stColumn, [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100% !important; min-width: 100% !important; }
  .st-key-exemples .stButton button[kind="secondary"], .st-key-exemples .stButton button[data-testid="stBaseButton-secondary"] { padding: var(--ss-espace-2) var(--ss-espace-3); }
  .ss-hero-titre { font-size: 1.6rem !important; }
  .ss-compteur-valeur { font-size: 1.6rem; }
  .ss-verdict { font-size: 1.05rem; padding: var(--ss-espace-2) var(--ss-espace-4); }
  .ss-pied { flex-direction: column; align-items: flex-start; }
  .stVerticalBlock.st-key-zone_analyse, .stVerticalBlock[class*="st-key-carte_"] { padding: var(--ss-espace-4); }
}
"""


def couleur_niveau(code: str) -> str:
    """Renvoie la couleur associée à un niveau de risque : sur, suspect ou arnaque."""
    return COULEURS.get(code, COULEURS["principale"])


def badge_verdict(niveau_code: str) -> str:
    """Renvoie le grand badge du verdict, avec l'icône et les couleurs propres au niveau."""
    verdict = VERDICTS.get(niveau_code, VERDICTS["suspect"])
    return (
        f'<span class="ss-verdict" style="color:{verdict["texte"]};border-color:{verdict["couleur"]};'
        f'background:{verdict["couleur"]}1F;">{verdict["icone"]} {html.escape(verdict["libelle"])}</span>'
    )


def carte_signal(icone: str, titre: str, detail: str, source: str, categorie: str = "autre") -> str:
    """Renvoie une carte HTML décrivant un signal suspect, avec son icône colorée et son origine."""
    couleur = CATEGORIE_COULEUR.get(categorie, COULEURS["gris"])
    tag = TEXTE_TAG["ia"] if "IA" in source else TEXTE_TAG["regle"]
    couleur_tag = COULEURS["ia"] if "IA" in source else couleur
    detail_html = f'<div class="ss-signal-detail">{html.escape(detail)}</div>' if detail else ""
    return (
        f'<div class="ss-signal" style="border-left-color:{couleur};">'
        f'<div class="ss-signal-icone" style="background:{couleur}1F;color:{couleur};">{icone}</div>'
        "<div>"
        f'<div class="ss-signal-titre">{html.escape(titre)}'
        f'<span class="ss-tag" style="color:{tag};border-color:{couleur_tag};">{html.escape(source)}</span>'
        "</div>"
        f"{detail_html}"
        "</div>"
        "</div>"
    )


def carte_compteur(icone: str, valeur: str, libelle: str, couleur: str) -> str:
    """Renvoie une carte de compteur : icône colorée, grand chiffre et libellé."""
    return (
        '<div class="ss-compteur">'
        f'<div class="ss-compteur-icone" style="background:{couleur}1F;color:{couleur};">{icone}</div>'
        f'<div class="ss-compteur-valeur">{html.escape(valeur)}</div>'
        f'<div class="ss-compteur-libelle">{html.escape(libelle)}</div>'
        "</div>"
    )


def bloc_etapes(etapes: list[str]) -> str:
    """Renvoie des conseils sous forme d'étapes numérotées, chacune avec un cercle coloré."""
    lignes = "".join(
        f'<div class="ss-etape"><div class="ss-etape-num">{index}</div>'
        f'<div class="ss-etape-texte">{html.escape(etape)}</div></div>'
        for index, etape in enumerate(etapes, start=1)
    )
    return f'<div class="ss-etapes">{lignes}</div>'


def etat_vide(message: str, icone: str = "📊", detail: str = "") -> str:
    """Renvoie un bloc HTML d'état vide : icône, message et précision facultative."""
    detail_html = f'<p class="ss-vide-detail">{html.escape(detail)}</p>' if detail else ""
    return (
        '<div class="ss-vide">'
        f'<div class="ss-vide-icone">{icone}</div>'
        f'<p class="ss-vide-titre">{html.escape(message)}</p>'
        f"{detail_html}"
        "</div>"
    )


def _motif_souple(mot: str) -> str:
    """Construit un motif regex tolérant aux accents, aux harakat et à la casse."""
    morceaux = []
    for caractere in mot:
        if caractere.isspace():
            morceaux.append(r"\s+")
            continue
        classe = f"[{VARIANTES[caractere]}]" if caractere in VARIANTES else re.escape(caractere)
        if "\u0600" <= caractere <= "\u06FF":
            classe += r"[\u064B-\u0652]*"
        morceaux.append(classe)
    return "".join(morceaux)


def surligner(texte: str, mots: list[str], maximum: int = 60) -> str:
    """Renvoie le message échappé en HTML, avec les mots suspects surlignés."""
    intervalles = []
    for mot in sorted({mot.strip() for mot in mots if len(mot.strip()) >= 3}, key=len, reverse=True):
        try:
            motif = re.compile(_motif_souple(mot), re.IGNORECASE)
        except re.error:
            continue
        intervalles += [correspondance.span() for correspondance in motif.finditer(texte)]
    if not intervalles:
        return html.escape(texte)
    intervalles.sort()
    fusionnes = [list(intervalles[0])]
    for debut, fin in intervalles[1:]:
        if debut <= fusionnes[-1][1]:
            fusionnes[-1][1] = max(fusionnes[-1][1], fin)
        else:
            fusionnes.append([debut, fin])
    morceaux, curseur = [], 0
    for debut, fin in fusionnes[:maximum]:
        morceaux.append(html.escape(texte[curseur:debut]))
        morceaux.append(f'<mark class="ss-surligne">{html.escape(texte[debut:fin])}</mark>')
        curseur = fin
    morceaux.append(html.escape(texte[curseur:]))
    return "".join(morceaux)


def _variables_css() -> str:
    """Génère les variables CSS du design system : couleurs, espacements et rayons."""
    declarations = " ".join(f"--ss-{nom}: {valeur};" for nom, valeur in COULEURS.items())
    systeme = (
        "--ss-rayon: 16px;"
        " --ss-rayon-pilule: 999px;"
        " --ss-espace-1: 4px; --ss-espace-2: 8px; --ss-espace-3: 12px;"
        " --ss-espace-4: 16px; --ss-espace-5: 24px; --ss-espace-6: 32px; --ss-espace-7: 48px;"
        " --ss-ombre: 0 1px 2px rgba(15,23,42,.04), 0 8px 24px rgba(15,23,42,.06);"
        " --ss-ombre-hero: 0 12px 32px rgba(37,99,235,.12);"
    )
    return f":root {{ {declarations} {systeme} }}"


def injecter_css() -> None:
    """Injecte le design system dans la page Streamlit."""
    st.markdown(f"<style>{_variables_css()}{CSS_BASE}</style>", unsafe_allow_html=True)
