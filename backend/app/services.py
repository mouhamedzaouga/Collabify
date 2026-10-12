"""Fonctions métier partagées : fil d'activité, sérialisation, temps relatif."""
from datetime import datetime
from html import escape as h  # noqa: F401  (échappement des données utilisateur dans le fil d'activité)

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Activity, Member, Message, Project, Task, now


def log_activity(db: Session, icon: str, text: str, color: str = "#b8ff57") -> None:
    """Ajoute une entrée au fil d'activité (le commit est fait par l'appelant)."""
    db.add(Activity(icon=icon, text=text, color=color))


def relative_time(dt: datetime) -> str:
    delta = now() - dt
    secs = int(delta.total_seconds())
    if secs < 45:
        return "à l'instant"
    if secs < 3600:
        return f"il y a {max(1, secs // 60)} min"
    if secs < 86400:
        return f"il y a {secs // 3600} h"
    if secs < 172800:
        return "Hier"
    return dt.strftime("%d/%m/%Y")


def member_out(m: Member) -> dict:
    return {"id": m.id, "name": m.name, "initials": m.initials, "role": m.role, "email": m.email, "color": m.color}


def project_completion(db: Session, pid: str) -> tuple[int, int]:
    """(pourcentage de tâches terminées, nombre de tâches)."""
    statuses = db.scalars(select(Task.status).where(Task.pid == pid)).all()
    if not statuses:
        return 0, 0
    return round(statuses.count("done") / len(statuses) * 100), len(statuses)


def project_out(db: Session, p: Project) -> dict:
    completion, count = project_completion(db, p.id)
    return {
        "id": p.id, "name": p.name, "desc": p.desc, "status": p.status, "color": p.color,
        "members": [m.id for m in p.members], "created": p.created, "deadline": p.deadline,
        "owner_id": p.owner_id, "completion": completion, "task_count": count,
    }


def message_out(m: Message) -> dict:
    today = now().date()
    if m.created_at.date() == today:
        day = "Aujourd'hui"
    elif (today - m.created_at.date()).days == 1:
        day = "Hier"
    else:
        day = m.created_at.strftime("%d/%m/%Y")
    return {"id": m.id, "pid": m.pid, "uid": m.uid, "text": m.text, "time": m.created_at.strftime("%H:%M"), "date": day}


def initials_of(name: str) -> str:
    return "".join(p[0] for p in name.split())[:2].upper()


def split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.split(maxsplit=1)
    return parts[0], (parts[1] if len(parts) > 1 else "")


def me_out(m: Member) -> dict:
    """Profil du compte connecté : ajoute prénom/nom et identifiant/matricule (non exposés aux autres membres)."""
    return {**member_out(m), "first_name": m.first_name, "last_name": m.last_name,
            "identifier": m.identifier, "matricule": m.matricule}
