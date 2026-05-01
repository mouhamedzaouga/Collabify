"""
database.py — In-memory store (remplacer par SQLAlchemy + PostgreSQL en production)
"""
from datetime import date
from copy import deepcopy

# ── Members ──────────────────────────────────────────────────────────────────
MEMBERS: list[dict] = [
    {"id": "u0", "name": "Mouhamed Zaouga", "initials": "MZ", "role": "Scrum Master",   "email": "m.zaouga@univ.tn",  "color": "#b8ff57"},
    {"id": "u1", "name": "Nour Daasi",       "initials": "ND", "role": "Product Owner",  "email": "n.daasi@univ.tn",   "color": "#a57bff"},
    {"id": "u2", "name": "Karim Lamine",     "initials": "KL", "role": "Développeur",    "email": "k.lamine@univ.tn",  "color": "#57b8ff"},
    {"id": "u3", "name": "Sarra Ben Ali",    "initials": "SB", "role": "UX Designer",    "email": "s.benali@univ.tn",  "color": "#ff5f87"},
    {"id": "u4", "name": "Omar Chahed",      "initials": "OC", "role": "Développeur",    "email": "o.chahed@univ.tn",  "color": "#ffb857"},
]

# ── Projects ──────────────────────────────────────────────────────────────────
PROJECTS: list[dict] = [
    {
        "id": "p1", "name": "Plateforme E-Learning",
        "desc": "Système de cours en ligne avec quiz et suivi des étudiants.",
        "status": "active", "color": "#b8ff57",
        "members": ["u0", "u1", "u2", "u3"],
        "created": "2025-04-01", "deadline": "2025-06-30",
    },
    {
        "id": "p2", "name": "App Mobile Résidence",
        "desc": "Application pour gérer les demandes de logement étudiant.",
        "status": "active", "color": "#a57bff",
        "members": ["u0", "u2", "u4"],
        "created": "2025-04-10", "deadline": "2025-07-15",
    },
    {
        "id": "p3", "name": "Dashboard Analytics RH",
        "desc": "Tableau de bord pour la gestion des ressources humaines.",
        "status": "done", "color": "#57b8ff",
        "members": ["u1", "u3"],
        "created": "2025-03-01", "deadline": "2025-04-20",
    },
]

# ── Tasks ─────────────────────────────────────────────────────────────────────
TASKS: list[dict] = [
    {"id": "t1",  "pid": "p1", "title": "Concevoir les maquettes Figma",       "desc": "Wireframes + prototype haute fidélité.", "assignee": "u3", "priority": "high",   "status": "done",   "created": "2025-04-05", "tags": ["Design", "UX"]},
    {"id": "t2",  "pid": "p1", "title": "API REST cours (FastAPI)",             "desc": "Endpoints GET/POST/PUT/DELETE.",          "assignee": "u2", "priority": "high",   "status": "doing",  "created": "2025-04-08", "tags": ["Backend"]},
    {"id": "t3",  "pid": "p1", "title": "Intégration React — module quiz",      "desc": "Composant interactif de quiz.",           "assignee": "u4", "priority": "medium", "status": "todo",   "created": "2025-04-10", "tags": ["Frontend", "React"]},
    {"id": "t4",  "pid": "p1", "title": "Auth JWT + refresh tokens",            "desc": "Système d'authentification sécurisé.",   "assignee": "u2", "priority": "high",   "status": "doing",  "created": "2025-04-09", "tags": ["Backend", "Sécurité"]},
    {"id": "t5",  "pid": "p1", "title": "Setup base de données PostgreSQL",     "desc": "Schéma, migrations Alembic.",             "assignee": "u0", "priority": "medium", "status": "done",   "created": "2025-04-06", "tags": ["DB"]},
    {"id": "t6",  "pid": "p2", "title": "Maquettes app mobile",                 "desc": "Écrans principaux en Figma.",             "assignee": "u3", "priority": "high",   "status": "todo",   "created": "2025-04-12", "tags": ["Design"]},
    {"id": "t7",  "pid": "p2", "title": "Backend Flask — demandes",             "desc": "API de gestion des demandes.",            "assignee": "u2", "priority": "high",   "status": "doing",  "created": "2025-04-14", "tags": ["Backend"]},
    {"id": "t8",  "pid": "p2", "title": "Module notifications push",            "desc": "Intégration Firebase Cloud Messaging.",   "assignee": "u4", "priority": "low",    "status": "todo",   "created": "2025-04-15", "tags": ["Mobile"]},
    {"id": "t9",  "pid": "p3", "title": "Dashboard KPIs",                       "desc": "Graphiques d'avancement et métriques.",   "assignee": "u1", "priority": "medium", "status": "done",   "created": "2025-03-10", "tags": ["Frontend"]},
    {"id": "t10", "pid": "p3", "title": "Export PDF rapports",                  "desc": "Génération automatique de rapports.",     "assignee": "u3", "priority": "low",    "status": "done",   "created": "2025-03-20", "tags": ["Backend"]},
]

# ── Messages ──────────────────────────────────────────────────────────────────
MESSAGES: dict[str, list[dict]] = {
    "p1": [
        {"id": "m1", "pid": "p1", "uid": "u1", "text": "J'ai finalisé les maquettes Figma, jetez un œil !", "time": "10:30", "date": "Aujourd'hui"},
        {"id": "m2", "pid": "p1", "uid": "u2", "text": "Super ! Je commence l'intégration React dès cet après-midi.", "time": "10:45", "date": "Aujourd'hui"},
        {"id": "m3", "pid": "p1", "uid": "u3", "text": "Les wireframes sont validés par le prof. On peut avancer.", "time": "11:02", "date": "Aujourd'hui"},
        {"id": "m4", "pid": "p1", "uid": "u0", "text": "Parfait, daily standup à 14h00 pour tout le monde.", "time": "11:15", "date": "Aujourd'hui"},
    ],
    "p2": [
        {"id": "m5", "pid": "p2", "uid": "u2", "text": "L'API de demandes est à 80%, ça avance bien.", "time": "09:20", "date": "Aujourd'hui"},
        {"id": "m6", "pid": "p2", "uid": "u4", "text": "J'ai un souci avec Firebase, quelqu'un peut m'aider ?", "time": "09:55", "date": "Aujourd'hui"},
    ],
    "p3": [],
}

# ── Activity feed ─────────────────────────────────────────────────────────────
ACTIVITY: list[dict] = [
    {"icon": "✅", "text": "<strong>Karim</strong> a terminé « API REST cours »",          "time": "il y a 20 min",  "color": "#b8ff57"},
    {"icon": "💬", "text": "<strong>Sarra</strong> a posté un message dans E-Learning",    "time": "il y a 45 min",  "color": "#a57bff"},
    {"icon": "➕", "text": "Tâche « Module notifications push » créée dans App Mobile",     "time": "il y a 2h",      "color": "#57b8ff"},
    {"icon": "👤", "text": "<strong>Omar Chahed</strong> a rejoint le projet App Mobile",  "time": "il y a 3h",      "color": "#ffb857"},
    {"icon": "📋", "text": "Projet « Dashboard Analytics RH » marqué comme terminé",       "time": "Hier",           "color": "#ff5f87"},
]

# ── Counters for ID generation ────────────────────────────────────────────────
_counters: dict[str, int] = {"project": 100, "task": 100, "member": 100, "message": 100}


def next_id(prefix: str) -> str:
    _counters[prefix] += 1
    return f"{prefix[0]}{_counters[prefix]}"


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_member(uid: str) -> dict | None:
    return next((m for m in MEMBERS if m["id"] == uid), None)


def get_project(pid: str) -> dict | None:
    return next((p for p in PROJECTS if p["id"] == pid), None)


def get_task(tid: str) -> dict | None:
    return next((t for t in TASKS if t["id"] == tid), None)


def project_completion(pid: str) -> int:
    ts = [t for t in TASKS if t["pid"] == pid]
    if not ts:
        return 0
    return round(len([t for t in ts if t["status"] == "done"]) / len(ts) * 100)


def add_activity(icon: str, text: str) -> None:
    ACTIVITY.insert(0, {"icon": icon, "text": text, "time": "il y a quelques secondes", "color": "#b8ff57"})
    if len(ACTIVITY) > 20:
        ACTIVITY.pop()
