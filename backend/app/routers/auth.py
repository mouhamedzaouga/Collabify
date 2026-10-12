"""Authentification : JWT (Bearer), mots de passe hachés (scrypt), limitation des tentatives."""
import hmac

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..deps import get_current_user
from ..models import Member, new_id
from ..schemas import LoginRequest, MeOut, PasswordChange, RegisterRequest, TokenResponse
from ..security import (DUMMY_HASH, create_access_token, hash_password, login_throttle, register_throttle,
                        verify_password)
from ..services import h, initials_of, log_activity, me_out

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="Connexion")
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Retourne un JWT à envoyer ensuite dans l'en-tête `Authorization: Bearer <token>`."""
    email = body.email.strip().lower()
    key = f"{email}|{request.client.host if request.client else '?'}"
    if login_throttle.blocked(key):
        raise HTTPException(status_code=429, detail="Trop de tentatives. Réessayez dans quelques minutes.")

    member = db.scalar(select(Member).where(Member.email == email))
    ok = verify_password(body.password, member.password_hash if member else DUMMY_HASH)
    if not member or not ok:
        login_throttle.fail(key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect")

    login_throttle.reset(key)
    return TokenResponse(access_token=create_access_token(member.id), member=MeOut(**me_out(member)))


@router.get("/me", response_model=MeOut, summary="Profil connecté")
def me(user: Member = Depends(get_current_user)):
    return MeOut(**me_out(user))


ROLE_COLORS = {"Enseignant": "#34d399", "Étudiant": "#b8ff57"}


@router.get("/register-options", summary="Options d'inscription")
def register_options():
    """Indique au frontend s'il doit demander un code d'invitation pour les enseignants."""
    return {"teacher_code_required": bool(config.TEACHER_CODE)}


@router.post("/register", response_model=TokenResponse, status_code=201, summary="Créer un compte")
def register(body: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Étudiant : email, identifiant, nom, prénom. Enseignant : email, nom, prénom, matricule.
    Le compte est connecté immédiatement (token retourné)."""
    key = f"register|{request.client.host if request.client else '?'}"
    if register_throttle.blocked(key):
        raise HTTPException(status_code=429, detail="Trop de créations de compte. Réessayez dans quelques minutes.")
    register_throttle.fail(key)  # chaque tentative compte : limite la création en masse

    if body.role == "Enseignant" and config.TEACHER_CODE:
        if not hmac.compare_digest((body.teacher_code or "").encode(), config.TEACHER_CODE.encode()):
            raise HTTPException(status_code=403, detail="Code d'invitation enseignant invalide")

    identifier = body.identifier.upper() if body.identifier else None
    matricule = body.matricule.upper() if body.matricule else None
    if db.scalar(select(Member.id).where(Member.email == body.email)):
        raise HTTPException(status_code=409, detail="Un compte existe déjà avec cet email")
    if identifier and db.scalar(select(Member.id).where(Member.identifier == identifier)):
        raise HTTPException(status_code=409, detail="Cet identifiant est déjà utilisé")
    if matricule and db.scalar(select(Member.id).where(Member.matricule == matricule)):
        raise HTTPException(status_code=409, detail="Ce matricule est déjà utilisé")

    full_name = f"{body.first_name} {body.last_name}"
    member = Member(
        id=new_id("u"), name=full_name, first_name=body.first_name, last_name=body.last_name,
        initials=initials_of(full_name), role=body.role, email=body.email, identifier=identifier, matricule=matricule,
        color=ROLE_COLORS[body.role], password_hash=hash_password(body.password),
    )
    db.add(member)
    log_activity(db, "👤", f"<strong>{h(full_name)}</strong> a rejoint la plateforme ({h(body.role)})")
    try:
        db.commit()
    except IntegrityError:  # course entre deux inscriptions identiques
        db.rollback()
        raise HTTPException(status_code=409, detail="Email, identifiant ou matricule déjà utilisé")
    return TokenResponse(access_token=create_access_token(member.id), member=MeOut(**me_out(member)))


@router.post("/change-password", status_code=204, summary="Changer son mot de passe")
def change_password(body: PasswordChange, user: Member = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    user.password_hash = hash_password(body.new_password)
    db.commit()
