"""Configuration centralisée (variables d'environnement avec valeurs par défaut sûres pour le dev)."""
import logging
import os
import secrets
from pathlib import Path

logger = logging.getLogger("collabify")

BASE_DIR = Path(__file__).resolve().parent.parent          # backend/
FRONTEND_DIR = BASE_DIR.parent / "frontend"

DATABASE_URL = os.getenv("COLLABIFY_DATABASE_URL", f"sqlite:///{BASE_DIR / 'collabify.db'}")

def _load_secret_key() -> str:
    """Clé JWT : variable d'environnement, sinon fichier local `backend/.secret_key` (créé au 1er lancement)."""
    env = os.getenv("COLLABIFY_SECRET_KEY")
    if env:
        return env
    key_file = BASE_DIR / ".secret_key"
    try:
        if key_file.exists():
            stored = key_file.read_text().strip()
            if stored:
                return stored
        key = secrets.token_urlsafe(48)
        key_file.write_text(key)
        try:
            key_file.chmod(0o600)
        except OSError:
            pass
        return key
    except OSError:
        logger.warning(
            "COLLABIFY_SECRET_KEY non défini et fichier .secret_key non inscriptible : clé aléatoire pour ce processus "
            "(les sessions seront invalidées au redémarrage). Définissez COLLABIFY_SECRET_KEY en production."
        )
        return secrets.token_urlsafe(48)


SECRET_KEY = _load_secret_key()

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("COLLABIFY_TOKEN_MINUTES", "480"))

CORS_ORIGINS = [o.strip() for o in os.getenv("COLLABIFY_CORS_ORIGINS", "*").split(",") if o.strip()]

SEED_DEMO_DATA = os.getenv("COLLABIFY_SEED_DEMO", "1") == "1"
DEMO_PASSWORD = "collabify"

# Code d'invitation exigé pour créer un compte Enseignant (vide = inscription enseignant libre : à éviter en production).
TEACHER_CODE = os.getenv("COLLABIFY_TEACHER_CODE", "").strip()

LOGIN_MAX_ATTEMPTS = int(os.getenv("COLLABIFY_LOGIN_MAX_ATTEMPTS", "5"))
LOGIN_WINDOW_SECONDS = int(os.getenv("COLLABIFY_LOGIN_WINDOW_SECONDS", "300"))

# Création de comptes : plus permissif que la connexion (une classe peut s'inscrire depuis la même adresse IP).
REGISTER_MAX_ATTEMPTS = int(os.getenv("COLLABIFY_REGISTER_MAX", "30"))
REGISTER_WINDOW_SECONDS = int(os.getenv("COLLABIFY_REGISTER_WINDOW_SECONDS", "600"))
