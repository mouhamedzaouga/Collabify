"""Membres : consultation pour tous, gestion réservée aux enseignants (profil : soi-même)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, is_teacher, require_teacher
from ..models import Member, Project, Task, new_id
from ..schemas import MemberCreate, MemberOut, MemberUpdate
from ..security import hash_password
from ..services import h, initials_of, log_activity, member_out, project_out, split_name

router = APIRouter()

ROLE_COLORS = {
    "Développeur": "#57b8ff", "UX Designer": "#ff5f87", "QA": "#ffb857",
    "DevOps": "#a57bff", "Étudiant": "#b8ff57", "Enseignant": "#34d399",
}


def _get_or_404(db: Session, uid: str) -> Member:
    m = db.get(Member, uid)
    if not m:
        raise HTTPException(status_code=404, detail=f"Membre '{uid}' introuvable")
    return m


@router.get("/", response_model=list[MemberOut], summary="Liste tous les membres")
def list_members(db: Session = Depends(get_db), _: Member = Depends(get_current_user)):
    return [member_out(m) for m in db.scalars(select(Member).order_by(Member.name))]


@router.get("/{uid}", response_model=MemberOut, summary="Détail d'un membre")
def get_member(uid: str, db: Session = Depends(get_db), _: Member = Depends(get_current_user)):
    return member_out(_get_or_404(db, uid))


@router.post("/", response_model=MemberOut, status_code=201, summary="Créer un membre (enseignant)")
def create_member(body: MemberCreate, db: Session = Depends(get_db), teacher: Member = Depends(require_teacher)):
    if db.scalar(select(Member).where(Member.email == body.email)):
        raise HTTPException(status_code=409, detail="Email déjà utilisé")
    first, last = split_name(body.name)
    m = Member(
        id=new_id("u"), name=body.name, first_name=first, last_name=last, initials=initials_of(body.name), role=body.role, email=body.email,
        color=body.color or ROLE_COLORS.get(body.role, "#5e5e88"), password_hash=hash_password(body.password),
    )
    db.add(m)
    log_activity(db, "👤", f"<strong>{h(body.name)}</strong> a rejoint l'équipe")
    db.commit()
    return member_out(m)


@router.put("/{uid}", response_model=MemberOut, summary="Modifier un membre (soi-même ou enseignant)")
def update_member(uid: str, body: MemberUpdate, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    m = _get_or_404(db, uid)
    if uid != user.id and not is_teacher(user):
        raise HTTPException(status_code=403, detail="Vous ne pouvez modifier que votre propre profil")
    if body.role is not None and body.role != m.role:
        if not is_teacher(user):
            raise HTTPException(status_code=403, detail="Seul un enseignant peut changer un rôle")
        if m.role == "Enseignant" and db.scalar(select(Member.id).where(Member.role == "Enseignant", Member.id != m.id)) is None:
            raise HTTPException(status_code=409, detail="Il doit rester au moins un enseignant")
    if body.email is not None:
        email = body.email.lower()
        clash = db.scalar(select(Member.id).where(Member.email == email, Member.id != m.id))
        if clash:
            raise HTTPException(status_code=409, detail="Email déjà utilisé")
        m.email = email
    if body.name is not None:
        m.name, m.initials = body.name, initials_of(body.name)
        m.first_name, m.last_name = split_name(body.name)
    if body.role is not None and body.role != m.role:
        m.role = body.role
        m.color = ROLE_COLORS.get(body.role, m.color)
    if body.color is not None:
        m.color = body.color
    db.commit()
    return member_out(m)


@router.delete("/{uid}", status_code=204, summary="Supprimer un membre (enseignant)")
def delete_member(uid: str, db: Session = Depends(get_db), teacher: Member = Depends(require_teacher)):
    m = _get_or_404(db, uid)
    if uid == teacher.id:
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas supprimer votre propre compte")
    # Les tâches du membre supprimé sont réassignées à l'enseignant qui effectue l'action.
    db.execute(update(Task).where(Task.assignee == uid).values(assignee=teacher.id))
    db.delete(m)
    log_activity(db, "👤", f"<strong>{h(m.name)}</strong> a quitté l'équipe")
    db.commit()


@router.get("/{uid}/stats", summary="Statistiques d'un membre")
def member_stats(uid: str, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    m = _get_or_404(db, uid)
    if uid != user.id and not is_teacher(user):
        raise HTTPException(status_code=403, detail="Statistiques réservées au membre concerné et aux enseignants")
    tasks = db.scalars(select(Task).where(Task.assignee == uid)).all()
    pids = {t.pid for t in tasks}
    projects = [db.get(Project, pid) for pid in pids]
    return {
        "member": member_out(m),
        "task_count": len(tasks),
        "done_count": sum(1 for t in tasks if t.status == "done"),
        "project_count": len(projects),
        "tasks": [
            {"id": t.id, "pid": t.pid, "title": t.title, "status": t.status, "priority": t.priority} for t in tasks
        ],
        "projects": [project_out(db, p) for p in projects if p],
    }
