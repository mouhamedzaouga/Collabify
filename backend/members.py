"""
routers/members.py — CRUD complet pour les membres
"""
from fastapi import APIRouter, HTTPException
from schemas import MemberCreate, MemberUpdate, MemberOut
import database as db

router = APIRouter()

ROLE_COLORS = {
    "Développeur":   "#57b8ff",
    "UX Designer":   "#ff5f87",
    "QA":            "#ffb857",
    "DevOps":        "#a57bff",
    "Product Owner": "#b8ff57",
    "Scrum Master":  "#34d399",
}


def _build_out(m: dict) -> MemberOut:
    return MemberOut(**m)


@router.get("/", response_model=list[MemberOut], summary="Liste tous les membres")
def list_members():
    return [_build_out(m) for m in db.MEMBERS]


@router.get("/{uid}", response_model=MemberOut, summary="Détail d'un membre")
def get_member(uid: str):
    m = db.get_member(uid)
    if not m:
        raise HTTPException(status_code=404, detail=f"Membre '{uid}' introuvable")
    return _build_out(m)


@router.post("/", response_model=MemberOut, status_code=201, summary="Créer un membre")
def create_member(body: MemberCreate):
    # Vérifier email unique
    if any(m["email"] == body.email for m in db.MEMBERS):
        raise HTTPException(status_code=409, detail="Email déjà utilisé")

    initials = "".join(p[0] for p in body.name.split())[:2].upper()
    color = body.color or ROLE_COLORS.get(body.role, "#5e5e88")

    new_member = {
        "id":       db.next_id("member"),
        "name":     body.name,
        "initials": initials,
        "role":     body.role,
        "email":    body.email,
        "color":    color,
    }
    db.MEMBERS.append(new_member)
    db.add_activity("👤", f"<strong>{body.name}</strong> a rejoint l'équipe")
    return _build_out(new_member)


@router.put("/{uid}", response_model=MemberOut, summary="Modifier un membre")
def update_member(uid: str, body: MemberUpdate):
    m = db.get_member(uid)
    if not m:
        raise HTTPException(status_code=404, detail=f"Membre '{uid}' introuvable")
    if uid == "u0":
        raise HTTPException(status_code=403, detail="Impossible de modifier le compte principal en démo")

    if body.name is not None:
        m["name"] = body.name
        m["initials"] = "".join(p[0] for p in body.name.split())[:2].upper()
    if body.email is not None:
        m["email"] = body.email
    if body.role is not None:
        m["role"] = body.role
        m["color"] = ROLE_COLORS.get(body.role, m["color"])
    if body.color is not None:
        m["color"] = body.color

    return _build_out(m)


@router.delete("/{uid}", status_code=204, summary="Supprimer un membre")
def delete_member(uid: str):
    if uid == "u0":
        raise HTTPException(status_code=403, detail="Impossible de supprimer le compte principal")

    m = db.get_member(uid)
    if not m:
        raise HTTPException(status_code=404, detail=f"Membre '{uid}' introuvable")

    db.MEMBERS.remove(m)

    # Réassigner les tâches à u0
    for t in db.TASKS:
        if t["assignee"] == uid:
            t["assignee"] = "u0"

    # Retirer des projets
    for p in db.PROJECTS:
        p["members"] = [i for i in p["members"] if i != uid]

    db.add_activity("👤", f"<strong>{m['name']}</strong> a quitté l'équipe")


@router.get("/{uid}/stats", summary="Statistiques d'un membre")
def member_stats(uid: str):
    m = db.get_member(uid)
    if not m:
        raise HTTPException(status_code=404, detail=f"Membre '{uid}' introuvable")

    my_tasks = [t for t in db.TASKS if t["assignee"] == uid]
    my_project_ids = list({t["pid"] for t in my_tasks})
    my_projects = [db.get_project(pid) for pid in my_project_ids if db.get_project(pid)]

    return {
        "member":       MemberOut(**m),
        "task_count":   len(my_tasks),
        "done_count":   len([t for t in my_tasks if t["status"] == "done"]),
        "project_count": len(my_projects),
        "tasks":        my_tasks,
        "projects":     my_projects,
    }
