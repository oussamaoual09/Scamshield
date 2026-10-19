"""ScamShield : détecteur d'arnaques financières. Point d'entrée Streamlit : navigation et mise en page."""

import html

import streamlit as st

import charts
import database
from ai_engine import ia_configuree
from analyzer import analyser_message
from rules import CATEGORIES, FICHES_PEDAGOGIQUES, NIVEAUX
from samples import EXEMPLES
from styles import (
    COULEURS,
    badge_verdict,
    bloc_etapes,
    carte_compteur,
    carte_signal,
    etat_vide,
    injecter_css,
    surligner,
)

st.set_page_config(page_title="ScamShield", page_icon="🛡️", layout="wide")

# Version affichée dans la barre latérale
APP_VERSION = "1.2.0"

# Longueur minimale d'un message pour lancer l'analyse
LONGUEUR_MINIMALE = 15
LANGUES = {"Auto": "auto", "Français": "fr", "Arabe": "ar", "Darija": "darija", "Anglais": "en"}
LIBELLE_LANGUE = {code: libelle for libelle, code in LANGUES.items()}
AVERTISSEMENT = "Ne collez jamais de mot de passe, code OTP ou numéro de carte complet."
CONFIG_GRAPHIQUE = {"displayModeBar": False}
TYPE_PAR_COURT = {meta["court"]: code for code, meta in CATEGORIES.items()}

# Sections de l'application, dans l'ordre du menu latéral
SECTIONS = ("🔍 Analyser", "📊 Statistiques", "🗂️ Historique", "🎓 Apprendre")

# Bandeau d'accueil : bouclier, titre, accroche et pastilles de confiance
EN_TETE = (
    '<div class="ss-hero"><div class="ss-hero-contenu">'
    '<div class="ss-hero-bouclier">🛡️</div>'
    '<h1 class="ss-hero-titre">Scam<span>Shield</span></h1>'
    '<p class="ss-hero-accroche">Collez un SMS, un e-mail, un message WhatsApp ou une offre '
    "d'investissement : obtenez un score de risque, les signaux détectés et les bons réflexes.</p>"
    '<div class="ss-pastilles">'
    '<span class="ss-pastille">⚡ Analyse en 5 secondes</span>'
    '<span class="ss-pastille">🧠 Règles + IA</span>'
    '<span class="ss-pastille">🔒 Données non partagées</span>'
    "</div></div></div>"
)

# Logo de la barre latérale
LOGO_LATERAL = (
    '<div class="ss-logo"><div class="ss-logo-icone">🛡️</div>'
    '<div><div class="ss-logo-nom">Scam<span>Shield</span></div>'
    '<div class="ss-logo-slogan">Détecteur d’arnaques</div></div></div>'
)

# Bloc « Numéros utiles » : aucune coordonnée inventée, uniquement les bons interlocuteurs
CARTE_NUMEROS = (
    '<div class="ss-carte-side"><div class="ss-carte-side-titre">📞 Numéros utiles</div>'
    '<ul class="ss-liste">'
    "<li><b>Votre banque</b> : le numéro au dos de votre carte ou sur son site officiel.</li>"
    "<li><b>Police ou Gendarmerie</b> : pour déposer plainte ou signaler l’arnaque.</li>"
    "<li><b>AMMC</b> : pour vérifier qu’un intermédiaire financier est agréé.</li>"
    "</ul></div>"
)


# Pied de page discret : rappel du cadre éducatif et version de l'application
def _pied_de_page() -> None:
    """Affiche le pied de page : avertissement éducatif et version de l'application."""
    st.markdown(
        '<div class="ss-pied">'
        '<span class="ss-pied-note">🎓 <b>Projet éducatif</b> : cet outil ne remplace pas un avis professionnel.</span>'
        f'<span class="ss-pied-note">ScamShield v{APP_VERSION}</span>'
        "</div>",
        unsafe_allow_html=True,
    )


def _titre_section(titre: str, sous_titre: str) -> None:
    """Affiche le titre et le sous-titre d'une section."""
    st.markdown(
        f'<div class="ss-section"><h2 class="ss-section-titre">{titre}</h2>'
        f'<p class="ss-section-sous">{sous_titre}</p></div>',
        unsafe_allow_html=True,
    )


def afficher_graphique(figure) -> None:
    """Affiche un graphique Plotly sur toute la largeur, compatible avec les versions récentes de Streamlit."""
    try:
        st.plotly_chart(figure, width="stretch", theme=None, config=CONFIG_GRAPHIQUE)
    except TypeError:
        st.plotly_chart(figure, use_container_width=True, theme=None, config=CONFIG_GRAPHIQUE)


def _formater_date(horodatage: str) -> str:
    """Transforme un horodatage « 2026-10-18 22:37:21 » en une date courte « 18/10/2026 »."""
    try:
        annee, mois, jour = horodatage.split(" ")[0].split("-")
        return f"{jour}/{mois}/{annee}"
    except (ValueError, AttributeError):
        return "—"


def _compteurs() -> None:
    """Affiche les quatre cartes de synthèse en haut de page, à partir de l'historique."""
    historique = database.get_history()
    total = len(historique)
    arnaques = int((historique["niveau"] == NIVEAUX["arnaque"]).sum()) if total else 0
    taux = f"{arnaques / total * 100:.0f} %" if total else "—"
    derniere = _formater_date(historique["date"].iloc[-1]) if total else "—"
    cartes = (
        ("💬", f"{total}", "Messages analysés", COULEURS["principale"]),
        ("🚨", f"{arnaques}", "Arnaques détectées", COULEURS["arnaque"]),
        ("🎯", taux, "Taux de détection", COULEURS["suspect"]),
        ("🕒", derniere, "Dernière analyse", COULEURS["gris"]),
    )
    for colonne, (icone, valeur, libelle, couleur) in zip(st.columns(4), cartes):
        colonne.markdown(carte_compteur(icone, valeur, libelle, couleur), unsafe_allow_html=True)


def _appliquer_exemple(exemple: dict) -> None:
    """Charge un exemple dans la zone de texte, avec sa langue, puis relance la page."""
    st.session_state["texte_analyse"] = exemple["texte"]
    st.session_state["langue_choisie"] = LIBELLE_LANGUE.get(exemple["langue"], "Auto")
    st.session_state.pop("resultat", None)
    st.session_state.pop("texte_affiche", None)
    st.session_state.pop("erreur", None)
    st.rerun()


def _exemples_en_pastilles() -> None:
    """Affiche les exemples de messages sous forme de pastilles cliquables."""
    st.markdown(
        '<p class="ss-sous-titre" style="margin:0 0 .35rem 0;">Ou testez directement un exemple :</p>',
        unsafe_allow_html=True,
    )
    with st.container(key="exemples"):
        lignes = [st.columns(3) for _ in range((len(EXEMPLES) + 2) // 3)]
        for index, exemple in enumerate(EXEMPLES):
            colonne = lignes[index // 3][index % 3]
            libelle = exemple["titre"].split(" : ")[-1]
            if colonne.button(libelle, key=f"exemple_{index}", help=exemple["titre"]):
                _appliquer_exemple(exemple)


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
    st.session_state["texte_affiche"] = texte
    database.save_analysis(
        texte,
        resultat["score"],
        resultat["niveau"],
        resultat["type"],
        [signal["libelle"] for signal in resultat["signaux"]],
    )
    # Relance la page pour que les compteurs du haut reflètent immédiatement la nouvelle analyse
    st.rerun()


def _carte_synthese(res: dict) -> None:
    """Affiche le verdict en grand badge, le type d'arnaque et l'explication."""
    meta = CATEGORIES[res["type"]]
    badge = badge_verdict(res["niveau_code"])
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
    """Affiche chaque signal suspect sous forme de petite carte avec son icône colorée et son origine."""
    if not signaux:
        st.success("Aucun signal d'arnaque connu n'a été repéré dans ce message.")
        return
    for signal in signaux:
        icone = CATEGORIES.get(signal["categorie"], CATEGORIES["autre"])["icone"]
        st.markdown(
            carte_signal(icone, signal["libelle"], signal["detail"], signal["source"], signal["categorie"]),
            unsafe_allow_html=True,
        )


def afficher_resultat(res: dict | None) -> None:
    """Affiche le résultat complet : jauge, verdict, signaux, étapes à suivre et message surligné."""
    if not res:
        return
    texte = st.session_state.get("texte_affiche") or st.session_state.get("texte_analyse") or ""
    mots_suspects = [mot for signal in res["signaux"] for mot in signal["mots"]]
    st.divider()
    col_jauge, col_verdict = st.columns([1, 1], gap="large")
    with col_jauge:
        with st.container(key="carte_jauge", border=True):
            afficher_graphique(charts.graphique_jauge(res["score"]))
    with col_verdict:
        _carte_synthese(res)
        _bandeau_ia(res)
    st.markdown("#### 🔎 Pourquoi c'est suspect")
    _liste_signaux(res["signaux"])
    st.markdown("#### 🧭 Que faire maintenant ?")
    st.markdown(bloc_etapes(res["conseils"]), unsafe_allow_html=True)
    st.markdown("#### 📩 Message analysé")
    st.markdown(f'<div class="ss-message">{surligner(texte, mots_suspects)}</div>', unsafe_allow_html=True)
    st.caption("Les passages surlignés sont les mots repérés par le moteur de règles.")
    col_contributions, col_radar = st.columns(2, gap="large")
    with col_contributions:
        with st.container(key="carte_contributions", border=True):
            afficher_graphique(charts.graphique_contributions(res["signaux"]))
    with col_radar:
        with st.container(key="carte_radar", border=True):
            afficher_graphique(charts.graphique_radar(res["scores_categories"]))
    st.info("Cet outil donne une estimation, pas une preuve. En cas de doute, contactez directement votre banque ou l'organisme concerné via ses canaux officiels.")


def section_analyse() -> None:
    """Section 1 : saisie du message, lancement de l'analyse et affichage du résultat."""
    _titre_section("Analyser un message", "Collez le message suspect, puis lancez l'analyse.")
    st.warning(AVERTISSEMENT, icon="🔐")
    _exemples_en_pastilles()
    with st.container(key="zone_analyse", border=True):
        st.text_area(
            "Message suspect",
            key="texte_analyse",
            height=180,
            placeholder="Collez ici le SMS, l'e-mail, le message WhatsApp ou l'offre d'investissement…",
        )
        libelle_langue = st.selectbox("Langue du message", list(LANGUES), key="langue_choisie")
        if st.button("🔎 Analyser le message", type="primary", key="bouton_analyse"):
            _lancer_analyse(libelle_langue)
    if st.session_state.get("erreur"):
        st.warning(st.session_state["erreur"])
    afficher_resultat(st.session_state.get("resultat"))


def section_statistiques() -> None:
    """Section 2 : métriques et graphiques arrondis construits à partir de l'historique SQLite."""
    _titre_section("Statistiques", "Vue d'ensemble de vos analyses enregistrées.")
    historique = database.get_history()
    if historique.empty:
        st.markdown(
            etat_vide(
                "Aucune donnée pour l'instant",
                "📊",
                "Analysez un premier message dans la section 🔍 Analyser : vos statistiques apparaîtront ici.",
            ),
            unsafe_allow_html=True,
        )
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
        with st.container(key="carte_repartition", border=True):
            afficher_graphique(charts.graphique_repartition_types(historique))
    with col_histogramme:
        with st.container(key="carte_distribution", border=True):
            afficher_graphique(charts.graphique_distribution(historique))
    with st.container(key="carte_evolution", border=True):
        afficher_graphique(charts.graphique_evolution(historique))


def section_historique() -> None:
    """Section 3 : tableau de l'historique, filtres, export CSV et effacement protégé par confirmation."""
    _titre_section("Historique", "Retrouvez, filtrez et exportez vos analyses.")
    historique = database.get_history()
    if historique.empty:
        st.markdown(
            etat_vide(
                "Aucune analyse enregistrée",
                "🗂️",
                "Les analyses réalisées dans la section 🔍 Analyser apparaîtront ici, avec leur score et leur type.",
            ),
            unsafe_allow_html=True,
        )
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


def section_apprendre() -> None:
    """Section 4 : fiches pédagogiques par type d'arnaque et démarches utiles."""
    _titre_section("Apprendre", "Reconnaître les arnaques, et savoir quoi faire.")
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


def barre_laterale() -> str:
    """Affiche la barre latérale : logo, menu de navigation, numéros utiles et version. Renvoie la section choisie."""
    with st.sidebar:
        st.markdown(LOGO_LATERAL, unsafe_allow_html=True)
        section = st.radio("Navigation", SECTIONS, key="section", label_visibility="collapsed")
        st.markdown(CARTE_NUMEROS, unsafe_allow_html=True)
        with st.popover("ℹ️ À propos"):
            st.markdown(f"**ScamShield v{APP_VERSION}**")
            st.markdown(
                "Détecteur d'arnaques financières : phishing, faux placements, pyramides, faux prêts, "
                "faux gains et faux emplois."
            )
            etat_ia = "activée" if ia_configuree() else "désactivée (règles seules)"
            st.markdown(
                f"**Intelligence artificielle** : {etat_ia}. Si elle est activée, le texte analysé est envoyé "
                "à l'API Groq. Seuls les 200 premiers caractères de chaque message sont conservés dans "
                "l'historique local."
            )
            st.caption("Estimation, pas preuve : vérifiez toujours auprès de l'organisme concerné.")
        st.caption(f"Version {APP_VERSION}")
    return section


def main() -> None:
    """Assemble la page : design system, barre latérale, bandeau d'accueil, compteurs, section active et pied de page."""
    injecter_css()
    database.init_db()
    section = barre_laterale()
    st.markdown(EN_TETE, unsafe_allow_html=True)
    _compteurs()
    sections = (section_analyse, section_statistiques, section_historique, section_apprendre)
    sections[SECTIONS.index(section) if section in SECTIONS else 0]()
    _pied_de_page()


if __name__ == "__main__":
    main()
