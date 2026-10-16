"""ScamShield : détecteur d'arnaques financières. Point d'entrée Streamlit : navigation et mise en page."""

import html

import streamlit as st

import charts
import database
from ai_engine import ia_configuree
from analyzer import analyser_message
from rules import CATEGORIES, FICHES_PEDAGOGIQUES, NIVEAUX
from samples import EXEMPLES
from styles import badge_niveau, carte_signal, injecter_css

st.set_page_config(page_title="ScamShield", page_icon="🛡️", layout="wide")

# Longueur minimale d'un message pour lancer l'analyse
LONGUEUR_MINIMALE = 15
AUCUN_EXEMPLE = "— Choisir un exemple —"
LANGUES = {"Auto": "auto", "Français": "fr", "Arabe": "ar", "Darija": "darija", "Anglais": "en"}
LIBELLE_LANGUE = {code: libelle for libelle, code in LANGUES.items()}
AVERTISSEMENT = "Ne collez jamais de mot de passe, code OTP ou numéro de carte complet."
CONFIG_GRAPHIQUE = {"displayModeBar": False}
TYPE_PAR_COURT = {meta["court"]: code for code, meta in CATEGORIES.items()}

EN_TETE = (
    '<div class="ss-hero">'
    '<h1 class="ss-titre">🛡️ Scam<span>Shield</span></h1>'
    '<p class="ss-sous-titre">Vérifiez en quelques secondes si un SMS, un e-mail ou une offre '
    "d'investissement est une arnaque. Une analyse claire, pour ne plus vous faire piéger.</p>"
    "</div>"
)


def afficher_graphique(figure) -> None:
    """Affiche un graphique Plotly sur toute la largeur, compatible avec les versions récentes de Streamlit."""
    try:
        st.plotly_chart(figure, width="stretch", theme=None, config=CONFIG_GRAPHIQUE)
    except TypeError:
        st.plotly_chart(figure, use_container_width=True, theme=None, config=CONFIG_GRAPHIQUE)


def _charger_exemple() -> None:
    """Remplit la zone de texte et la langue avec l'exemple choisi (callback du sélecteur)."""
    titre = st.session_state.get("choix_exemple", AUCUN_EXEMPLE)
    exemple = next((item for item in EXEMPLES if item["titre"] == titre), None)
    if exemple is None:
        return
    st.session_state["texte_analyse"] = exemple["texte"]
    st.session_state["langue_choisie"] = LIBELLE_LANGUE.get(exemple["langue"], "Auto")
    st.session_state.pop("resultat", None)
    st.session_state.pop("erreur", None)


def _lancer_analyse(libelle_langue: str) -> None:
    """Analyse le message saisi, mémorise le résultat et enregistre l'analyse dans l'historique."""
    texte = (st.session_state.get("texte_analyse") or "").strip()
    st.session_state.pop("erreur", None)
    if len(texte) < LONGUEUR_MINIMALE:
        st.session_state["erreur"] = f"Collez un message d'au moins {LONGUEUR_MINIMALE} caractères pour lancer l'analyse."
        st.session_state.pop("resultat", None)
        return
    try:
        with st.spinner("Analyse en cours : règles, puis intelligence artificielle…"):
            resultat = analyser_message(texte, LANGUES[libelle_langue])
    except Exception:
        st.session_state["erreur"] = "Une erreur inattendue est survenue pendant l'analyse. Réessayez."
        st.session_state.pop("resultat", None)
        return
    st.session_state["resultat"] = resultat
    database.save_analysis(
        texte,
        resultat["score"],
        resultat["niveau"],
        resultat["type"],
        [signal["libelle"] for signal in resultat["signaux"]],
    )


def _carte_synthese(res: dict) -> None:
    """Affiche le badge de niveau, le type d'arnaque et l'explication."""
    meta = CATEGORIES[res["type"]]
    badge = badge_niveau(res["niveau_code"], res["niveau"])
    explication = html.escape(res["explication"])
    st.markdown(
        f'<div class="ss-carte">{badge}'
        '<p class="ss-sous-titre" style="margin:1rem 0 .2rem 0;">Type d’arnaque détecté</p>'
        f'<h3 style="margin:0;">{meta["icone"]} {html.escape(meta["libelle"])}</h3>'
        f'<p style="margin-top:1rem;line-height:1.6;">{explication}</p>'
        "</div>",
        unsafe_allow_html=True,
    )
    if res["niveau_code"] == "sur" and res["type"] != "sur":
        st.caption("Signal faible : le niveau reste Sûr, mais ce type d'arnaque a été évoqué.")
    st.caption(f"Langue du message : {LIBELLE_LANGUE.get(res['langue'], res['langue'])}")


def _bandeau_ia(res: dict) -> None:
    """Indique si le score combine les règles et l'IA, ou si seules les règles ont servi."""
    if res["ia_disponible"]:
        st.caption(
            f"Score combiné : 40 % moteur de règles ({res['score_regles']}/100) "
            f"+ 60 % intelligence artificielle ({res['score_ia']}/100)."
        )
    else:
        st.info(res["message_ia"] or "Analyse réalisée avec le moteur de règles uniquement.")


def _liste_signaux(signaux: list[dict]) -> None:
    """Affiche chaque signal suspect sous forme de carte avec son icône et son origine."""
    if not signaux:
        st.success("Aucun signal d'arnaque connu n'a été repéré dans ce message.")
        return
    for signal in signaux:
        icone = CATEGORIES.get(signal["categorie"], CATEGORIES["autre"])["icone"]
        st.markdown(carte_signal(icone, signal["libelle"], signal["detail"], signal["source"]), unsafe_allow_html=True)


def afficher_resultat(res: dict | None) -> None:
    """Affiche le résultat complet d'une analyse : jauge, badge, signaux, conseils et graphiques."""
    if not res:
        return
    st.divider()
    col_jauge, col_synthese = st.columns([1, 1], gap="large")
    with col_jauge:
        with st.container(border=True):
            afficher_graphique(charts.graphique_jauge(res["score"], res["niveau_code"]))
    with col_synthese:
        _carte_synthese(res)
        _bandeau_ia(res)
    st.markdown("#### 🔎 Pourquoi c'est suspect")
    _liste_signaux(res["signaux"])
    st.markdown("#### 🧭 Que faire maintenant")
    for conseil in res["conseils"]:
        st.markdown(f"✅ {html.escape(conseil, quote=False)}")
    col_contributions, col_radar = st.columns(2, gap="large")
    with col_contributions:
        st.markdown("#### 📊 Contribution de chaque signal")
        afficher_graphique(charts.graphique_contributions(res["signaux"]))
        st.caption("Bleu : moteur de règles · Violet : intelligence artificielle")
    with col_radar:
        st.markdown("#### 🕸️ Profil de risque par type")
        afficher_graphique(charts.graphique_radar(res["scores_categories"]))
    st.info("Cet outil donne une estimation, pas une preuve. En cas de doute, contactez directement votre banque ou l'organisme concerné via ses canaux officiels.")


def onglet_analyse() -> None:
    """Onglet 1 : saisie du message, lancement de l'analyse et affichage du résultat."""
    st.warning(AVERTISSEMENT, icon="🔐")
    st.selectbox(
        "Charger un exemple",
        [AUCUN_EXEMPLE] + [item["titre"] for item in EXEMPLES],
        key="choix_exemple",
        on_change=_charger_exemple,
    )
    st.text_area(
        "Message suspect",
        key="texte_analyse",
        height=180,
        placeholder="Collez ici le SMS, l'e-mail, le message WhatsApp ou l'offre d'investissement…",
    )
    libelle_langue = st.selectbox("Langue du message", list(LANGUES), key="langue_choisie")
    if st.button("Analyser le message", type="primary"):
        _lancer_analyse(libelle_langue)
    if st.session_state.get("erreur"):
        st.warning(st.session_state["erreur"])
    afficher_resultat(st.session_state.get("resultat"))


def onglet_statistiques() -> None:
    """Onglet 2 : métriques et graphiques construits à partir de l'historique SQLite."""
    historique = database.get_history()
    if historique.empty:
        st.info("Aucune analyse enregistrée pour le moment. Analysez un premier message dans l'onglet 🔍 Analyser : vos statistiques apparaîtront ici.")
        return
    total = len(historique)
    moyenne = historique["score"].mean()
    part_arnaques = (historique["niveau"] == NIVEAUX["arnaque"]).mean() * 100
    col_1, col_2, col_3 = st.columns(3)
    col_1.metric("Analyses réalisées", f"{total}")
    col_2.metric("Score moyen", f"{moyenne:.0f} / 100")
    col_3.metric("Arnaques probables", f"{part_arnaques:.0f} %")
    col_donut, col_histogramme = st.columns(2, gap="large")
    with col_donut:
        st.markdown("#### Types d'arnaques détectés")
        afficher_graphique(charts.graphique_repartition_types(historique))
    with col_histogramme:
        st.markdown("#### Distribution des scores")
        afficher_graphique(charts.graphique_distribution(historique))
    st.markdown("#### Évolution du score dans le temps")
    afficher_graphique(charts.graphique_evolution(historique))


def onglet_historique() -> None:
    """Onglet 3 : tableau de l'historique, filtres, export CSV et effacement protégé par confirmation."""
    historique = database.get_history()
    if historique.empty:
        st.info("Votre historique est vide. Les analyses réalisées apparaîtront ici.")
        return
    vue = historique.copy()
    vue["type_libelle"] = vue["type"].map(lambda code: CATEGORIES.get(code, CATEGORIES["autre"])["court"])
    col_niveau, col_type = st.columns(2)
    niveau = col_niveau.selectbox("Filtrer par niveau", ["Tous"] + list(NIVEAUX.values()), key="filtre_niveau")
    type_choisi = col_type.selectbox("Filtrer par type", ["Tous"] + list(TYPE_PAR_COURT), key="filtre_type")
    if niveau != "Tous":
        vue = vue[vue["niveau"] == niveau]
    if type_choisi != "Tous":
        vue = vue[vue["type"] == TYPE_PAR_COURT[type_choisi]]
    tableau = (
        vue.sort_values("date", ascending=False)[["date", "extrait", "score", "niveau", "type_libelle"]]
        .rename(columns={"date": "Date", "extrait": "Extrait du message", "score": "Score", "niveau": "Niveau", "type_libelle": "Type"})
    )
    st.caption(f"{len(tableau)} analyse(s) affichée(s) sur {len(historique)}")
    st.dataframe(
        tableau,
        hide_index=True,
        column_config={"Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d")},
    )
    st.download_button(
        "📥 Exporter en CSV",
        data=tableau.to_csv(index=False, sep=";").encode("utf-8-sig"),
        file_name="scamshield_historique.csv",
        mime="text/csv",
    )
    st.divider()
    _zone_effacement()


def _zone_effacement() -> None:
    """Bouton d'effacement de l'historique, protégé par une étape de confirmation."""
    if not st.session_state.get("confirmer_effacement"):
        if st.button("🗑️ Effacer l'historique"):
            st.session_state["confirmer_effacement"] = True
            st.rerun()
        return
    st.warning("Cette action supprimera définitivement toutes les analyses enregistrées. Voulez-vous continuer ?")
    col_oui, col_non = st.columns(2)
    if col_oui.button("Oui, tout effacer", type="primary"):
        database.clear_history()
        st.session_state["confirmer_effacement"] = False
        st.rerun()
    if col_non.button("Annuler"):
        st.session_state["confirmer_effacement"] = False
        st.rerun()


def onglet_apprendre() -> None:
    """Onglet 4 : fiches pédagogiques par type d'arnaque et démarches utiles."""
    st.markdown("Chaque arnaque suit des mécanismes reconnaissables. Ouvrez une fiche pour apprendre à les repérer.")
    for code, fiche in FICHES_PEDAGOGIQUES.items():
        meta = CATEGORIES[code]
        with st.expander(f"{meta['icone']} {meta['libelle']}"):
            st.markdown(f"**Comment ça marche**\n\n{fiche['fonctionnement']}")
            st.markdown("**Signes d'alerte**")
            st.markdown("\n".join(f"- {signe}" for signe in fiche["signes"]))
            st.markdown(f"**Exemple**\n\n> {fiche['exemple']}")
            st.markdown("**Que faire**")
            st.markdown("\n".join(f"- {action}" for action in fiche["que_faire"]))
    st.markdown("### 📞 Numéros et démarches utiles")
    st.info("Ne donnez jamais suite au message suspect. Pour tout doute, contactez vous-même l'organisme concerné.")
    st.markdown(
        "- **Votre banque** : appelez le numéro figurant au dos de votre carte ou sur son site officiel, jamais celui du message.\n"
        "- **Police nationale (DGSN) ou Gendarmerie royale** : déposez plainte ou signalez l'arnaque.\n"
        "- **AMMC** (Autorité marocaine du marché des capitaux) : vérifiez si un intermédiaire financier est agréé.\n"
        "- **Ne payez jamais** de frais pour recevoir un gain, un héritage ou un prêt.\n"
        "- **Si vous avez transmis vos codes** : changez vos mots de passe, faites opposition sur votre carte et prévenez votre banque sans attendre.\n\n"
        "Ces démarches concernent surtout le Maroc. Dans un autre pays, adressez-vous aux autorités locales équivalentes."
    )


def barre_laterale() -> None:
    """Affiche la barre latérale : présentation, mode d'emploi, confidentialité et statut de l'IA."""
    with st.sidebar:
        st.markdown("## 🛡️ ScamShield")
        st.caption("Détecteur d'arnaques financières : SMS, WhatsApp, e-mails, annonces et offres d'investissement.")
        st.markdown("### Mode d'emploi")
        st.markdown(
            "1. **Collez** le message suspect.\n"
            "2. **Cliquez** sur « Analyser le message ».\n"
            "3. **Lisez** le score, les signaux et les conseils."
        )
        st.markdown("### 🔒 Confidentialité")
        st.caption(
            "Seuls les 200 premiers caractères de chaque message sont conservés dans l'historique local. "
            "Si l'IA est activée, le texte est envoyé à l'API Groq pour analyse."
        )
        etat_ia = "activée ✅" if ia_configuree() else "désactivée (règles uniquement)"
        st.caption(f"Intelligence artificielle : {etat_ia}")


def main() -> None:
    """Assemble la page : style, barre latérale, en-tête et les quatre onglets."""
    injecter_css()
    database.init_db()
    barre_laterale()
    st.markdown(EN_TETE, unsafe_allow_html=True)
    onglet_1, onglet_2, onglet_3, onglet_4 = st.tabs(["🔍 Analyser", "📊 Statistiques", "🗂️ Historique", "🎓 Apprendre"])
    with onglet_1:
        onglet_analyse()
    with onglet_2:
        onglet_statistiques()
    with onglet_3:
        onglet_historique()
    with onglet_4:
        onglet_apprendre()


if __name__ == "__main__":
    main()
