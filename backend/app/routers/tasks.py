"""Tâches : CRUD avec contrôle d'accès par projet. Un étudiant ne crée pas de tâche « complexe » directement."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import STUDENT, get_accessible_project, get_current_user, is_teacher
from ..models import Member, Project, Task, new_id
from ..schemas import TaskCreate, TaskOut, TaskStatusUpdate, TaskUpdate
from ..services import h, log_activity

router = APIRouter()

STATUS_LABELS = {"todo": "📌 À faire", "doing": "🔄 En cours", "review": "👀 En revue", "done": "✅ Terminé"}
COMPLEX_FORBIDDEN = "Un étudiant doit passer par une demande d'autorisation pour une tâche complexe"


def _task_for(db: Session, tid: str, user: Member) -> Task:
    t = db.get(Task, tid)
    if not t:
        raise HTTPException(status_code=404, detail=f"Tâche '{tid}' introuvable")
    get_accessible_project(db, t.pid, user)  # 403 si hors projet
    return t


@router.get("/", response_model=list[TaskOut], summary="Lister les tâches visibles")
def list_tasks(
    pid: str | None = None, assignee: str | None = None, status: str | None = None,
    priority: str | None = None, complexity: str | None = None, search: str | None = None,
    db: Session = Depends(get_db), user: Member = Depends(get_current_user),
):
    """Filtres cumulables : `pid`, `assignee`, `status`, `priority`, `complexity`, `search` (titre/description)."""
    stmt = select(Task).order_by(Task.created, Task.id)
    if not is_teacher(user):
        stmt = stmt.join(Project, Project.id == Task.pid).where(Project.members.any(Member.id == user.id))
    if pid:
        stmt = stmt.where(Task.pid == pid)
    if assignee:
        stmt = stmt.where(Task.assignee == assignee)
    if status:
        stmt = stmt.where(Task.status == status)
    if priority:
        stmt = stmt.where(Task.priority == priority)
    if complexity:
        stmt = stmt.where(Task.complexity == complexity)
    tasks = db.scalars(stmt).all()
    if search:
        q = search.lower()
        tasks = [t for t in tasks if q in t.title.lower() or q in (t.desc or "").lower()]
    return tasks


@router.get("/{tid}", response_model=TaskOut, summary="Détail d'une tâche")
def get_task(tid: str, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    return _task_for(db, tid, user)


@router.post("/", response_model=TaskOut, status_code=201, summary="Créer une tâche")
def create_task(body: TaskCreate, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    project = get_accessible_project(db, body.pid, user)
    if user.role == STUDENT and body.complexity == "complexe":
        raise HTTPException(status_code=403, detail=COMPLEX_FORBIDDEN)
    assignee = body.assignee or user.id
    if not db.get(Member, assignee):
        raise HTTPException(status_code=404, detail=f"Membre '{assignee}' introuvable")
    t = Task(
        id=new_id("t"), pid=body.pid, title=body.title, desc=body.desc, assignee=assignee, priority=body.priority,
        status=body.status, tags=body.tags, complexity=body.complexity, created=str(date.today()),
    )
    db.add(t)
    log_activity(db, "📋", f"Tâche « {h(body.title)} » créée dans {h(project.name)}")
    db.commit()
    return t


@router.put("/{tid}", response_model=TaskOut, summary="Modifier une tâche")
def update_task(tid: str, body: TaskUpdate, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    t = _task_for(db, tid, user)
    if body.assignee and not db.get(Member, body.assignee):
        raise HTTPException(status_code=404, detail=f"Membre '{body.assignee}' introuvable")
    if user.role == STUDENT and body.complexity == "complexe" and t.complexity != "complexe":
        raise HTTPException(status_code=403, detail=COMPLEX_FORBIDDEN)
    old_status = t.status
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(t, field, value)
    if body.status and body.status != old_status:
        log_activity(db, "🔄", f"Statut de « {h(t.title)} » → {STATUS_LABELS[body.status]}")
    db.commit()
    return t


@router.patch("/{tid}/status", response_model=TaskOut, summary="Changer le statut d'une tâche")
def patch_status(tid: str, body: TaskStatusUpdate, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    t = _task_for(db, tid, user)
    if body.status != t.status:
        t.status = body.status
        log_activity(db, "🔄", f"Statut de « {h(t.title)} » → {STATUS_LABELS[body.status]}")
        db.commit()
    return t


@router.delete("/{tid}", status_code=204, summary="Supprimer une tâche (enseignant, propriétaire du projet ou assigné)")
def delete_task(tid: str, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    t = _task_for(db, tid, user)
    if not (is_teacher(user) or t.project.owner_id == user.id or t.assignee == user.id):
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas supprimer cette tâche")
    title = t.title
    db.delete(t)
    log_activity(db, "🗑️", f"Tâche « {h(title)} » supprimée")
    db.commit()
