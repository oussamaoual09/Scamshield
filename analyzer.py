"""Analyseur final de ScamShield : fusionne le moteur de règles et l'IA en un résultat unique, prêt à afficher."""

import re
from difflib import SequenceMatcher

from ai_engine import analyser_avec_ia
from rules import CATEGORIES, CONSEILS_GENERAUX, CONSEILS_PAR_TYPE, NIVEAUX, analyser_regles, normaliser_texte

# Pondérations du score final
POIDS_REGLES = 0.4
POIDS_IA = 0.6

# Seuils des niveaux de risque (Sûr 0-30, Suspect 31-65, Arnaque probable 66-100)
SEUIL_SUR = 30
SEUIL_SUSPECT = 65

# Similarité minimale pour considérer deux signaux comme identiques
SEUIL_SIMILARITE = 0.75

# Marqueurs de darija et d'anglais utilisés par la détection de langue
MARQUEURS_DARIJA = {"bghit", "bghiti", "dyal", "daba", "khdma", "khlas", "wach", "3afak", "salam", "mzyan", "ghadi", "kayn", "chno", "flous", "bla"}
MARQUEURS_ANGLAIS = {"the", "you", "your", "and", "account", "click", "with", "to"}


def niveau_pour_score(score: int) -> str:
    """Convertit un score sur 100 en code de niveau : sur, suspect ou arnaque."""
    if score <= SEUIL_SUR:
        return "sur"
    if score <= SEUIL_SUSPECT:
        return "suspect"
    return "arnaque"


def detecter_langue(texte: str) -> str:
    """Devine la langue du message par heuristique simple : arabe, darija, anglais, sinon français."""
    lettres = re.findall(r"[^\W\d_]", texte)
    arabes = re.findall(r"[\u0600-\u06FF]", texte)
    if lettres and len(arabes) / len(lettres) > 0.3:
        return "ar"
    mots = set(re.findall(r"[a-z0-9']+", texte.lower()))
    if len(mots & MARQUEURS_DARIJA) >= 2:
        return "darija"
    if len(mots & MARQUEURS_ANGLAIS) >= 3:
        return "en"
    return "fr"


def analyser_message(texte: str, langue: str = "auto") -> dict:
    """Analyse un message avec le moteur de règles et l'IA, puis renvoie un dictionnaire unique prêt à afficher."""
    regles = analyser_regles(texte)
    ia = analyser_avec_ia(texte, langue)
    donnees = ia["donnees"] if ia["disponible"] else None
    score_regles = regles["score"]
    score_ia = donnees["score"] if donnees else None
    score = round(POIDS_REGLES * score_regles + POIDS_IA * score_ia) if donnees else score_regles
    niveau_code = niveau_pour_score(score)
    scores_categories = _scores_combines(regles, donnees)
    type_code = _type_final(scores_categories, score)
    return {
        "score": score,
        "niveau": NIVEAUX[niveau_code],
        "niveau_code": niveau_code,
        "type": type_code,
        "type_libelle": CATEGORIES[type_code]["libelle"],
        "type_icone": CATEGORIES[type_code]["icone"],
        "langue": _langue_finale(langue, donnees, texte),
        "explication": _explication(donnees, regles, type_code),
        "conseils": _conseils(donnees, type_code, niveau_code),
        "signaux": _fusionner_signaux(regles, donnees),
        "score_regles": score_regles,
        "score_ia": score_ia,
        "ia_disponible": donnees is not None,
        "message_ia": ia["message"],
        "scores_categories": scores_categories,
    }


def _similaires(a: str, b: str) -> bool:
    """Indique si deux libellés expriment la même idée (inclusion ou similarité élevée)."""
    na, nb = normaliser_texte(a), normaliser_texte(b)
    if min(len(na), len(nb)) < 4:
        return False
    if na in nb or nb in na:
        return True
    return SequenceMatcher(None, na, nb).ratio() >= SEUIL_SIMILARITE


def _correspond(texte: str, signal: dict) -> bool:
    """Vérifie si un signal de l'IA correspond à un signal déjà présent (libellé ou mots détectés)."""
    candidats = [signal["libelle"], *signal.get("mots", [])]
    return any(_similaires(texte, candidat) for candidat in candidats)


def _detail_regle(signal: dict) -> str:
    """Construit le texte explicatif d'un signal des règles, avec les mots détectés."""
    detail = signal["explication"]
    if signal["mots"]:
        detail += " Mots détectés : " + ", ".join(f"« {mot} »" for mot in signal["mots"]) + "."
    return detail


def _contributions_regles(regles: dict, facteur: float) -> list[dict]:
    """Répartit le score des règles entre leurs signaux, proportionnellement à leur poids."""
    brut = regles["brut"]
    if brut <= 0:
        return []
    echelle = regles["score"] / brut
    return [
        {
            "libelle": signal["libelle"],
            "source": "Règle",
            "categorie": signal["categorie"],
            "points": round(signal["poids"] * echelle * facteur, 1),
            "detail": _detail_regle(signal),
            "mots": signal["mots"],
        }
        for signal in regles["signaux"]
    ]


def _trier(signaux: list[dict]) -> list[dict]:
    """Trie les signaux du plus contributif au moins contributif."""
    return sorted(signaux, key=lambda signal: signal["points"], reverse=True)


def _fusionner_signaux(regles: dict, donnees: dict | None) -> list[dict]:
    """Fusionne les signaux des règles et de l'IA sans doublon, avec la contribution de chacun au score."""
    facteur = POIDS_REGLES if donnees else 1.0
    signaux = _contributions_regles(regles, facteur)
    if donnees is None:
        return _trier(signaux)
    part_ia = POIDS_IA * donnees["score"]
    textes = donnees["signaux"]
    if not textes:
        if part_ia > 0:
            signaux.append(
                {
                    "libelle": "Évaluation globale de l'IA",
                    "source": "IA",
                    "categorie": donnees["type"],
                    "points": round(part_ia, 1),
                    "detail": donnees["explication"],
                    "mots": [],
                }
            )
        return _trier(signaux)
    part = part_ia / len(textes)
    for texte in textes:
        cible = next((signal for signal in signaux if _correspond(texte, signal)), None)
        if cible is None:
            signaux.append(
                {
                    "libelle": texte,
                    "source": "IA",
                    "categorie": donnees["type"],
                    "points": round(part, 1),
                    "detail": "",
                    "mots": [],
                }
            )
            continue
        cible["points"] = round(cible["points"] + part, 1)
        if cible["source"] == "Règle":
            cible["source"] = "Règle + IA"
    return _trier(signaux)


def _scores_combines(regles: dict, donnees: dict | None) -> dict:
    """Calcule le score de chaque type d'arnaque, en combinant les règles et l'IA si elle est disponible."""
    scores = {}
    for code in CATEGORIES:
        if code == "sur":
            continue
        base = regles["scores_categories"].get(code, 0)
        if donnees is None:
            scores[code] = base
            continue
        part_ia = donnees["score"] if donnees["type"] == code else 0
        scores[code] = round(POIDS_REGLES * base + POIDS_IA * part_ia)
    return scores


def _type_final(scores_categories: dict, score: int) -> str:
    """Choisit le type d'arnaque le plus probable ; renvoie « sur » si aucun signal n'est retenu."""
    meilleur = max(scores_categories, key=scores_categories.get)
    if scores_categories[meilleur] > 0:
        return meilleur
    return "sur" if score <= SEUIL_SUR else "autre"


def _langue_finale(langue: str, donnees: dict | None, texte: str) -> str:
    """Choisit la langue affichée : celle du sélecteur, sinon celle de l'IA, sinon l'heuristique."""
    if langue != "auto":
        return langue
    if donnees and donnees["langue"]:
        return donnees["langue"]
    return detecter_langue(texte)


def _explication(donnees: dict | None, regles: dict, type_code: str) -> str:
    """Renvoie l'explication de l'IA, ou une explication générée à partir des règles."""
    if donnees and donnees["explication"]:
        return donnees["explication"]
    if type_code == "sur":
        return "Aucun signal d'arnaque connu n'a été repéré dans ce message."
    return (
        f"Le moteur de règles a repéré {len(regles['signaux'])} signal(aux) d'alerte. "
        f"Type d'arnaque le plus probable : {CATEGORIES[type_code]['libelle']}."
    )


def _conseils(donnees: dict | None, type_code: str, niveau_code: str) -> list[str]:
    """Assemble les conseils : ceux de l'IA d'abord, puis les conseils par défaut sans doublon."""
    conseils = list(donnees["conseils"]) if donnees else []
    conseils += CONSEILS_PAR_TYPE.get(type_code, [])
    if niveau_code != "sur":
        conseils += CONSEILS_GENERAUX
    uniques: list[str] = []
    for conseil in conseils:
        if conseil.lower() not in [deja.lower() for deja in uniques]:
            uniques.append(conseil)
    return uniques[:7]
