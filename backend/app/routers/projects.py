"""Projets : lecture limitée aux membres (les enseignants voient tout), gestion réservée aux enseignants."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_accessible_project, get_current_user, get_project_or_404, is_teacher, require_teacher
from ..models import Activity, Member, Project, Task, new_id
from ..schemas import ProjectCreate, ProjectMembersUpdate, ProjectOut, ProjectUpdate, TaskOut
from ..services import h, log_activity, member_out, project_completion, project_out, relative_time

router = APIRouter()


def _visible_projects(db: Session, user: Member) -> list[Project]:
    projects = db.scalars(select(Project).order_by(Project.created.desc(), Project.id)).all()
    return projects if is_teacher(user) else [p for p in projects if any(m.id == user.id for m in p.members)]


def _can_manage(user: Member, p: Project) -> bool:
    return is_teacher(user) or p.owner_id == user.id


@router.get("/", response_model=list[ProjectOut], summary="Lister les projets visibles")
def list_projects(status: str | None = None, member_id: str | None = None,
                  db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    result = _visible_projects(db, user)
    if status:
        result = [p for p in result if p.status == status]
    if member_id:
        result = [p for p in result if any(m.id == member_id for m in p.members)]
    return [project_out(db, p) for p in result]


@router.get("/dashboard", summary="Statistiques du tableau de bord (utilisateur connecté)")
def dashboard(db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    projects = _visible_projects(db, user)
    pids = {p.id for p in projects}
    mine = [t for t in db.scalars(select(Task).where(Task.assignee == user.id)) if t.pid in pids]
    done = [t for t in mine if t.status == "done"]
    activity = db.scalars(select(Activity).order_by(Activity.created_at.desc(), Activity.id.desc()).limit(10)).all()
    return {
        "active_projects": sum(1 for p in projects if p.status == "active"),
        "total_projects": len(projects),
        "my_tasks": len(mine),
        "my_done_tasks": len(done),
        "members": db.scalar(select(func.count()).select_from(Member)),
        "my_completion_pct": round(len(done) / len(mine) * 100) if mine else 0,
        "recent_projects": [project_out(db, p) for p in projects[:3]],
        "activity": [
            {"icon": a.icon, "text": a.text, "color": a.color, "time": relative_time(a.created_at)} for a in activity
        ],
    }


@router.get("/{pid}", response_model=ProjectOut, summary="Détail d'un projet")
def get_project(pid: str, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    return project_out(db, get_accessible_project(db, pid, user))


@router.post("/", response_model=ProjectOut, status_code=201, summary="Créer un projet (enseignant)")
def create_project(body: ProjectCreate, db: Session = Depends(get_db), teacher: Member = Depends(require_teacher)):
    ids = {*body.members, teacher.id}
    members = db.scalars(select(Member).where(Member.id.in_(ids))).all()
    if len(members) != len(ids):
        raise HTTPException(status_code=404, detail="Un des membres indiqués est introuvable")
    p = Project(
        id=new_id("p"), name=body.name, desc=body.desc, color=body.color, deadline=body.deadline,
        status=body.status, created=str(date.today()), owner_id=teacher.id, members=sorted(members, key=lambda m: m.id),
    )
    db.add(p)
    log_activity(db, "◫", f"<strong>Projet</strong> « {h(body.name)} » créé")
    db.commit()
    return project_out(db, p)


@router.put("/{pid}", response_model=ProjectOut, summary="Modifier un projet (enseignant ou propriétaire)")
def update_project(pid: str, body: ProjectUpdate, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    p = get_accessible_project(db, pid, user)
    if not _can_manage(user, p):
        raise HTTPException(status_code=403, detail="Seul un enseignant ou le propriétaire peut modifier ce projet")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    log_activity(db, "✏️", f"Projet « {h(p.name)} » mis à jour")
    db.commit()
    return project_out(db, p)


@router.delete("/{pid}", status_code=204, summary="Supprimer un projet (enseignant ou propriétaire)")
def delete_project(pid: str, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    p = get_accessible_project(db, pid, user)
    if not _can_manage(user, p):
        raise HTTPException(status_code=403, detail="Seul un enseignant ou le propriétaire peut supprimer ce projet")
    name = p.name
    db.delete(p)  # tâches, messages et demandes liés sont supprimés en cascade
    log_activity(db, "🗑️", f"Projet « {h(name)} » supprimé")
    db.commit()


# ── Membres du projet ─────────────────────────────────────────────────────────
@router.get("/{pid}/members", summary="Membres du projet")
def project_members(pid: str, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    return [member_out(m) for m in get_accessible_project(db, pid, user).members]


@router.post("/{pid}/members", summary="Ajouter des membres au projet (enseignant ou propriétaire)")
def add_members(pid: str, body: ProjectMembersUpdate, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    p = get_accessible_project(db, pid, user)
    if not _can_manage(user, p):
        raise HTTPException(status_code=403, detail="Seul un enseignant ou le propriétaire peut gérer les membres")
    added = []
    for uid in dict.fromkeys(body.member_ids):
        m = db.get(Member, uid)
        if not m:
            raise HTTPException(status_code=404, detail=f"Membre '{uid}' introuvable")
        if all(x.id != uid for x in p.members):
            p.members.append(m)
            added.append(uid)
    db.commit()
    return {"added": added, "members": [m.id for m in p.members]}


@router.delete("/{pid}/members/{uid}", status_code=204, summary="Retirer un membre du projet")
def remove_member(pid: str, uid: str, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    p = get_accessible_project(db, pid, user)
    if not _can_manage(user, p):
        raise HTTPException(status_code=403, detail="Seul un enseignant ou le propriétaire peut gérer les membres")
    if uid == p.owner_id:
        raise HTTPException(status_code=403, detail="Impossible de retirer le propriétaire du projet")
    target = next((m for m in p.members if m.id == uid), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Membre '{uid}' absent du projet")
    p.members.remove(target)
    db.commit()


# ── Kanban & avancement ───────────────────────────────────────────────────────
@router.get("/{pid}/board", summary="Vue Kanban du projet")
def kanban_board(pid: str, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    p = get_accessible_project(db, pid, user)
    board = {"todo": [], "doing": [], "review": [], "done": []}
    for t in p.tasks:
        board[t.status].append(TaskOut.model_validate(t).model_dump())
    return board


@router.get("/{pid}/progress", summary="Avancement du projet")
def project_progress(pid: str, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    p = get_accessible_project(db, pid, user)
    completion, count = project_completion(db, pid)
    loads = []
    for m in p.members:
        mine = [t for t in p.tasks if t.assignee == m.id]
        done = [t for t in mine if t.status == "done"]
        loads.append({
            "member": member_out(m), "task_count": len(mine), "done_count": len(done),
            "pct": round(len(done) / len(mine) * 100) if mine else 0,
        })
    return {
        "completion": completion,
        "task_count": count,
        "by_status": {s: sum(1 for t in p.tasks if t.status == s) for s in ("todo", "doing", "review", "done")},
        "member_loads": loads,
    }
