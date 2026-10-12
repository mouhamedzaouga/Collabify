"""Demandes d'autorisation : un étudiant demande une tâche « complexe », un enseignant l'approuve (la tâche est créée) ou la refuse."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_accessible_project, get_current_user, is_teacher, require_teacher
from ..models import AuthRequest, Member, Project, Task, new_id
from ..schemas import AuthRequestCreate, AuthRequestDecision, AuthRequestOut
from ..services import h, log_activity

router = APIRouter()


def _pending_or_error(db: Session, rid: str) -> AuthRequest:
    r = db.get(AuthRequest, rid)
    if not r:
        raise HTTPException(status_code=404, detail=f"Demande '{rid}' introuvable")
    if r.status != "pending":
        raise HTTPException(status_code=409, detail="Cette demande a déjà été traitée")
    return r


@router.get("/", response_model=list[AuthRequestOut], summary="Lister les demandes d'autorisation")
def list_requests(status: str | None = None, student_id: str | None = None,
                  db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    """Un enseignant voit toutes les demandes ; un étudiant uniquement les siennes."""
    stmt = select(AuthRequest).order_by(AuthRequest.created.desc(), AuthRequest.id)
    if not is_teacher(user):
        stmt = stmt.where(AuthRequest.student_id == user.id)
    elif student_id:
        stmt = stmt.where(AuthRequest.student_id == student_id)
    if status:
        stmt = stmt.where(AuthRequest.status == status)
    return db.scalars(stmt).all()


@router.post("/", response_model=AuthRequestOut, status_code=201, summary="Créer une demande d'autorisation")
def create_request(body: AuthRequestCreate, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    get_accessible_project(db, body.pid, user)
    assignee = body.assignee or user.id
    if not db.get(Member, assignee):
        raise HTTPException(status_code=404, detail=f"Membre '{assignee}' introuvable")
    r = AuthRequest(
        id=new_id("r"), student_id=user.id, pid=body.pid, title=body.title, desc=body.desc, priority=body.priority,
        assignee=assignee, tags=body.tags, reason=body.reason, status="pending", created=str(date.today()),
    )
    db.add(r)
    log_activity(db, "🔐", f"<strong>{h(user.name)}</strong> demande l'autorisation pour la tâche complexe « {h(body.title)} »")
    db.commit()
    return r


@router.put("/{rid}/approve", response_model=AuthRequestOut, summary="Approuver une demande (crée la tâche)")
def approve_request(rid: str, body: AuthRequestDecision, db: Session = Depends(get_db), teacher: Member = Depends(require_teacher)):
    r = _pending_or_error(db, rid)
    task = Task(
        id=new_id("t"), pid=r.pid, title=r.title, desc=r.desc, assignee=r.assignee, priority=r.priority,
        status="todo", tags=r.tags, complexity="complexe", created=str(date.today()),
    )
    db.add(task)
    r.status, r.reviewed_by, r.review_comment, r.task_id = "approved", teacher.id, body.comment, task.id
    student = db.get(Member, r.student_id)
    project = db.get(Project, r.pid)
    log_activity(db, "✅", f"Demande de <strong>{h(student.name)}</strong> approuvée — tâche « {h(r.title)} » créée dans {h(project.name)}")
    db.commit()
    return r


@router.put("/{rid}/reject", response_model=AuthRequestOut, summary="Refuser une demande")
def reject_request(rid: str, body: AuthRequestDecision, db: Session = Depends(get_db), teacher: Member = Depends(require_teacher)):
    r = _pending_or_error(db, rid)
    r.status, r.reviewed_by, r.review_comment = "rejected", teacher.id, body.comment
    student = db.get(Member, r.student_id)
    log_activity(db, "❌", f"Demande de <strong>{h(student.name)}</strong> refusée pour « {h(r.title)} »")
    db.commit()
    return r
