"""Gestion de l'historique des analyses dans une base SQLite locale."""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import pandas as pd

# Fichier de la base, situé à côté de ce module
CHEMIN_BASE = Path(__file__).resolve().parent / "scamshield.db"

# Nombre de caractères du message conservés (confidentialité)
LONGUEUR_EXTRAIT = 200

COLONNES = ["date", "extrait", "score", "niveau", "type", "signaux"]

logger = logging.getLogger(__name__)


@contextmanager
def _connexion():
    """Ouvre une connexion SQLite, valide la transaction en fin de bloc puis ferme la connexion."""
    conn = sqlite3.connect(CHEMIN_BASE)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> bool:
    """Crée la table « analyses » si elle n'existe pas encore. Renvoie True en cas de succès."""
    try:
        with _connexion() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    extrait TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    niveau TEXT NOT NULL,
                    type TEXT NOT NULL,
                    signaux TEXT NOT NULL DEFAULT '[]'
                )
                """
            )
        return True
    except sqlite3.Error as exc:
        logger.error("Initialisation de la base impossible : %s", exc)
        return False


def save_analysis(texte: str, score: int, niveau: str, type_arnaque: str, signaux: list[str]) -> bool:
    """Enregistre une analyse : seul un extrait de 200 caractères est conservé, jamais le message complet."""
    try:
        with _connexion() as conn:
            conn.execute(
                "INSERT INTO analyses (date, extrait, score, niveau, type, signaux) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    texte.strip()[:LONGUEUR_EXTRAIT],
                    int(score),
                    niveau,
                    type_arnaque,
                    json.dumps(signaux, ensure_ascii=False),
                ),
            )
        return True
    except sqlite3.Error as exc:
        logger.error("Enregistrement de l'analyse impossible : %s", exc)
        return False


def get_history() -> pd.DataFrame:
    """Renvoie l'historique complet, du plus ancien au plus récent, sous forme de DataFrame."""
    try:
        with _connexion() as conn:
            return pd.read_sql_query(
                "SELECT date, extrait, score, niveau, type, signaux FROM analyses ORDER BY id",
                conn,
            )
    except (sqlite3.Error, pd.errors.DatabaseError) as exc:
        logger.error("Lecture de l'historique impossible : %s", exc)
        return pd.DataFrame(columns=COLONNES)


def clear_history() -> bool:
    """Supprime toutes les analyses enregistrées. Renvoie True en cas de succès."""
    try:
        with _connexion() as conn:
            conn.execute("DELETE FROM analyses")
        return True
    except sqlite3.Error as exc:
        logger.error("Effacement de l'historique impossible : %s", exc)
        return False
