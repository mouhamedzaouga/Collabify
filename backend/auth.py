"""
routers/auth.py — Authentification simplifiée (JWT stateless)
En production : utiliser python-jose + passlib + PostgreSQL
"""
from fastapi import APIRouter, HTTPException, status
from schemas import LoginRequest, TokenResponse, MemberOut
import database as db

router = APIRouter()

# Mot de passe fictif pour la démo (tous les comptes : "collabify")
DEMO_PASSWORD = "collabify"


def _fake_token(uid: str) -> str:
    """Génère un token fictif pour la démo. Remplacer par JWT réel en prod."""
    import base64
    return base64.b64encode(f"demo:{uid}:{DEMO_PASSWORD}".encode()).decode()


def _decode_token(token: str) -> str | None:
    """Décode le token fictif et retourne l'uid."""
    import base64
    try:
        parts = base64.b64decode(token.encode()).decode().split(":")
        if parts[0] == "demo" and parts[2] == DEMO_PASSWORD:
            return parts[1]
    except Exception:
        pass
    return None


@router.post("/login", response_model=TokenResponse, summary="Connexion")
def login(body: LoginRequest):
    """
    Connexion avec email + mot de passe.
    - Mot de passe démo pour tous : **collabify**
    - Emails disponibles : m.zaouga@univ.tn, n.daasi@univ.tn, k.lamine@univ.tn, s.benali@univ.tn, o.chahed@univ.tn
    """
    member = next((m for m in db.MEMBERS if m["email"] == body.email), None)
    if not member or body.password != DEMO_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )
    token = _fake_token(member["id"])
    return TokenResponse(access_token=token, member=MemberOut(**member))


@router.get("/me", response_model=MemberOut, summary="Profil connecté")
def me(token: str):
    """Retourne le profil du membre connecté à partir du token."""
    uid = _decode_token(token)
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")
    member = db.get_member(uid)
    if not member:
        raise HTTPException(status_code=404, detail="Membre introuvable")
    return MemberOut(**member)
