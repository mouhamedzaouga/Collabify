"""
routers/projects.py — CRUD complet pour les projets
"""
from datetime import date
from fastapi import APIRouter, HTTPException
from schemas import ProjectCreate, ProjectUpdate, ProjectOut, ProjectMembersUpdate
import database as db

router = APIRouter()


def _enrich(p: dict) -> ProjectOut:
    ts = [t for t in db.TASKS if t["pid"] == p["id"]]
    return ProjectOut(
        **p,
        completion=db.project_completion(p["id"]),
        task_count=len(ts),
    )


# ── List & filter ─────────────────────────────────────────────────────────────
@router.get("/", response_model=list[ProjectOut], summary="Lister les projets")
def list_projects(status: str | None = None, member_id: str | None = None):
    """
    Filtres optionnels :
    - `status` : active | done | paused
    - `member_id` : retourne uniquement les projets dont le membre fait partie
    """
    result = db.PROJECTS
    if status:
        result = [p for p in result if p["status"] == status]
    if member_id:
        result = [p for p in result if member_id in p["members"]]
    return [_enrich(p) for p in result]


# ── Dashboard stats ───────────────────────────────────────────────────────────
@router.get("/dashboard", summary="Statistiques globales (tableau de bord)")
def dashboard(uid: str = "u0"):
    my_tasks = [t for t in db.TASKS if t["assignee"] == uid]
    done_tasks = [t for t in my_tasks if t["status"] == "done"]
    active = [p for p in db.PROJECTS if p["status"] == "active"]
    pct = round(len(done_tasks) / len(my_tasks) * 100) if my_tasks else 0

    return {
        "active_projects":    len(active),
        "total_projects":     len(db.PROJECTS),
        "my_tasks":           len(my_tasks),
        "my_done_tasks":      len(done_tasks),
        "members":            len(db.MEMBERS),
        "my_completion_pct":  pct,
        "recent_projects":    [_enrich(p) for p in db.PROJECTS[:3]],
        "my_doing_tasks":     [t for t in my_tasks if t["status"] in ("todo", "doing")][:4],
        "activity":           db.ACTIVITY[:10],
    }


# ── Single project ────────────────────────────────────────────────────────────
@router.get("/{pid}", response_model=ProjectOut, summary="Détail d'un projet")
def get_project(pid: str):
    p = db.get_project(pid)
    if not p:
        raise HTTPException(status_code=404, detail=f"Projet '{pid}' introuvable")
    return _enrich(p)


@router.post("/", response_model=ProjectOut, status_code=201, summary="Créer un projet")
def create_project(body: ProjectCreate):
    members = list({*body.members, "u0"})  # Le créateur est toujours membre

    new_project = {
        "id":       db.next_id("project"),
        "name":     body.name,
        "desc":     body.desc,
        "color":    body.color,
        "deadline": body.deadline,
        "status":   body.status,
        "members":  members,
        "created":  str(date.today()),
    }
    db.PROJECTS.append(new_project)
    db.MESSAGES[new_project["id"]] = []
    db.add_activity("◫", f"<strong>Projet</strong> « {body.name} » créé")
    return _enrich(new_project)


@router.put("/{pid}", response_model=ProjectOut, summary="Modifier un projet")
def update_project(pid: str, body: ProjectUpdate):
    p = db.get_project(pid)
    if not p:
        raise HTTPException(status_code=404, detail=f"Projet '{pid}' introuvable")

    for field, value in body.model_dump(exclude_none=True).items():
        p[field] = value

    db.add_activity("✏️", f"Projet « {p['name']} » mis à jour")
    return _enrich(p)


@router.delete("/{pid}", status_code=204, summary="Supprimer un projet")
def delete_project(pid: str):
    p = db.get_project(pid)
    if not p:
        raise HTTPException(status_code=404, detail=f"Projet '{pid}' introuvable")

    db.PROJECTS.remove(p)
    # Supprimer les tâches liées
    db.TASKS[:] = [t for t in db.TASKS if t["pid"] != pid]
    # Supprimer le canal de messages
    db.MESSAGES.pop(pid, None)
    db.add_activity("🗑️", f"Projet « {p['name']} » supprimé")


# ── Members management ────────────────────────────────────────────────────────
@router.get("/{pid}/members", summary="Membres du projet")
def project_members(pid: str):
    p = db.get_project(pid)
    if not p:
        raise HTTPException(status_code=404, detail=f"Projet '{pid}' introuvable")
    return [db.get_member(uid) for uid in p["members"] if db.get_member(uid)]


@router.post("/{pid}/members", summary="Ajouter des membres au projet")
def add_members(pid: str, body: ProjectMembersUpdate):
    p = db.get_project(pid)
    if not p:
        raise HTTPException(status_code=404, detail=f"Projet '{pid}' introuvable")

    added = []
    for uid in body.member_ids:
        if not db.get_member(uid):
            raise HTTPException(status_code=404, detail=f"Membre '{uid}' introuvable")
        if uid not in p["members"]:
            p["members"].append(uid)
            added.append(uid)

    return {"added": added, "members": p["members"]}


@router.delete("/{pid}/members/{uid}", status_code=204, summary="Retirer un membre du projet")
def remove_member(pid: str, uid: str):
    p = db.get_project(pid)
    if not p:
        raise HTTPException(status_code=404, detail=f"Projet '{pid}' introuvable")
    if uid == "u0":
        raise HTTPException(status_code=403, detail="Impossible de retirer le propriétaire du projet")
    if uid not in p["members"]:
        raise HTTPException(status_code=404, detail=f"Membre '{uid}' absent du projet")
    p["members"].remove(uid)


# ── Kanban board ──────────────────────────────────────────────────────────────
@router.get("/{pid}/board", summary="Vue Kanban du projet")
def kanban_board(pid: str):
    p = db.get_project(pid)
    if not p:
        raise HTTPException(status_code=404, detail=f"Projet '{pid}' introuvable")

    ts = [t for t in db.TASKS if t["pid"] == pid]
    return {
        "todo":   [t for t in ts if t["status"] == "todo"],
        "doing":  [t for t in ts if t["status"] == "doing"],
        "review": [t for t in ts if t["status"] == "review"],
        "done":   [t for t in ts if t["status"] == "done"],
    }


# ── Progress ──────────────────────────────────────────────────────────────────
@router.get("/{pid}/progress", summary="Avancement du projet")
def project_progress(pid: str):
    p = db.get_project(pid)
    if not p:
        raise HTTPException(status_code=404, detail=f"Projet '{pid}' introuvable")

    ts = [t for t in db.TASKS if t["pid"] == pid]
    member_loads = []
    for uid in p["members"]:
        m = db.get_member(uid)
        if not m:
            continue
        mt = [t for t in ts if t["assignee"] == uid]
        md = [t for t in mt if t["status"] == "done"]
        member_loads.append({
            "member":     m,
            "task_count": len(mt),
            "done_count": len(md),
            "pct":        round(len(md) / len(mt) * 100) if mt else 0,
        })

    return {
        "completion": db.project_completion(pid),
        "task_count": len(ts),
        "by_status": {
            "todo":   len([t for t in ts if t["status"] == "todo"]),
            "doing":  len([t for t in ts if t["status"] == "doing"]),
            "review": len([t for t in ts if t["status"] == "review"]),
            "done":   len([t for t in ts if t["status"] == "done"]),
        },
        "member_loads": member_loads,
    }
