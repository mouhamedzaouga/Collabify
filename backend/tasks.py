"""
routers/tasks.py — CRUD complet pour les tâches
"""
from datetime import date
from fastapi import APIRouter, HTTPException
from schemas import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskOut
import database as db

router = APIRouter()


def _out(t: dict) -> TaskOut:
    return TaskOut(**t)


# ── List & search ─────────────────────────────────────────────────────────────
@router.get("/", response_model=list[TaskOut], summary="Lister les tâches")
def list_tasks(
    pid: str | None = None,
    assignee: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    search: str | None = None,
):
    """
    Filtres cumulables :
    - `pid`      : tâches d'un projet
    - `assignee` : tâches d'un membre
    - `status`   : todo | doing | review | done
    - `priority` : high | medium | low
    - `search`   : recherche dans le titre (insensible à la casse)
    """
    result = db.TASKS
    if pid:
        result = [t for t in result if t["pid"] == pid]
    if assignee:
        result = [t for t in result if t["assignee"] == assignee]
    if status:
        result = [t for t in result if t["status"] == status]
    if priority:
        result = [t for t in result if t["priority"] == priority]
    if search:
        q = search.lower()
        result = [t for t in result if q in t["title"].lower() or q in t.get("desc", "").lower()]
    return [_out(t) for t in result]


# ── Single task ───────────────────────────────────────────────────────────────
@router.get("/{tid}", response_model=TaskOut, summary="Détail d'une tâche")
def get_task(tid: str):
    t = db.get_task(tid)
    if not t:
        raise HTTPException(status_code=404, detail=f"Tâche '{tid}' introuvable")
    return _out(t)


@router.post("/", response_model=TaskOut, status_code=201, summary="Créer une tâche")
def create_task(body: TaskCreate):
    if not db.get_project(body.pid):
        raise HTTPException(status_code=404, detail=f"Projet '{body.pid}' introuvable")
    if not db.get_member(body.assignee):
        raise HTTPException(status_code=404, detail=f"Membre '{body.assignee}' introuvable")

    new_task = {
        "id":       db.next_id("task"),
        "pid":      body.pid,
        "title":    body.title,
        "desc":     body.desc,
        "assignee": body.assignee,
        "priority": body.priority,
        "status":   body.status,
        "tags":     body.tags,
        "created":  str(date.today()),
    }
    db.TASKS.append(new_task)
    proj_name = db.get_project(body.pid)["name"]
    db.add_activity("📋", f"Tâche « {body.title} » créée dans {proj_name}")
    return _out(new_task)


@router.put("/{tid}", response_model=TaskOut, summary="Modifier une tâche")
def update_task(tid: str, body: TaskUpdate):
    t = db.get_task(tid)
    if not t:
        raise HTTPException(status_code=404, detail=f"Tâche '{tid}' introuvable")

    if body.assignee and not db.get_member(body.assignee):
        raise HTTPException(status_code=404, detail=f"Membre '{body.assignee}' introuvable")

    old_status = t["status"]
    for field, value in body.model_dump(exclude_none=True).items():
        t[field] = value

    if body.status and body.status != old_status:
        STATUS_LABELS = {"todo": "📌 À faire", "doing": "🔄 En cours", "review": "👀 En revue", "done": "✅ Terminé"}
        db.add_activity("🔄", f"Statut de « {t['title']} » → {STATUS_LABELS.get(body.status, body.status)}")

    return _out(t)


@router.patch("/{tid}/status", response_model=TaskOut, summary="Changer le statut d'une tâche")
def patch_status(tid: str, body: TaskStatusUpdate):
    t = db.get_task(tid)
    if not t:
        raise HTTPException(status_code=404, detail=f"Tâche '{tid}' introuvable")

    STATUS_LABELS = {"todo": "📌 À faire", "doing": "🔄 En cours", "review": "👀 En revue", "done": "✅ Terminé"}
    t["status"] = body.status
    db.add_activity("🔄", f"Statut de « {t['title']} » → {STATUS_LABELS[body.status]}")
    return _out(t)


@router.delete("/{tid}", status_code=204, summary="Supprimer une tâche")
def delete_task(tid: str):
    t = db.get_task(tid)
    if not t:
        raise HTTPException(status_code=404, detail=f"Tâche '{tid}' introuvable")
    db.TASKS.remove(t)
    db.add_activity("🗑️", f"Tâche « {t['title']} » supprimée")
