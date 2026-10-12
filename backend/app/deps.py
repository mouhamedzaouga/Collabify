"""Dépendances FastAPI : utilisateur courant, rôles, accès aux projets."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Member, Project
from .security import decode_access_token

bearer = HTTPBearer(auto_error=False)

TEACHER = "Enseignant"
STUDENT = "Étudiant"


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Member:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise ou session expirée",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if creds is None:
        raise unauthorized
    uid = decode_access_token(creds.credentials)
    user = db.get(Member, uid) if uid else None
    if user is None:
        raise unauthorized
    return user


def require_teacher(user: Member = Depends(get_current_user)) -> Member:
    if user.role != TEACHER:
        raise HTTPException(status_code=403, detail="Action réservée aux enseignants")
    return user


def is_teacher(user: Member) -> bool:
    return user.role == TEACHER


def can_access_project(user: Member, project: Project) -> bool:
    return is_teacher(user) or any(m.id == user.id for m in project.members)


def get_project_or_404(db: Session, pid: str) -> Project:
    project = db.get(Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projet '{pid}' introuvable")
    return project


def get_accessible_project(db: Session, pid: str, user: Member) -> Project:
    """404 si le projet n'existe pas, 403 si l'utilisateur n'en fait pas partie."""
    project = get_project_or_404(db, pid)
    if not can_access_project(user, project):
        raise HTTPException(status_code=403, detail="Vous ne faites pas partie de ce projet")
    return project
