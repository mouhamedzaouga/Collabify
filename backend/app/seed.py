"""Données de démonstration (insérées uniquement si la base est vide)."""
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import DEMO_PASSWORD
from .models import Activity, Member, Message, Project, Task
from .security import hash_password

# (id, nom, initiales, rôle, email, couleur)
_MEMBERS = [
    ("u0", "Mouhamed Zaouga", "MZ", "Enseignant", "m.zaouga@univ.tn", "#b8ff57"),
    ("u1", "Nour Daasi", "ND", "Étudiant", "n.daasi@univ.tn", "#a57bff"),
    ("u2", "Karim Lamine", "KL", "Développeur", "k.lamine@univ.tn", "#57b8ff"),
    ("u3", "Sarra Ben Ali", "SB", "UX Designer", "s.benali@univ.tn", "#ff5f87"),
    ("u4", "Omar Chahed", "OC", "Développeur", "o.chahed@univ.tn", "#ffb857"),
]

# (id, nom, description, statut, couleur, membres, créé, échéance)
_PROJECTS = [
    ("p1", "Plateforme E-Learning", "Système de cours en ligne avec quiz et suivi des étudiants.", "active", "#b8ff57",
     ["u0", "u1", "u2", "u3"], "2025-04-01", "2025-06-30"),
    ("p2", "App Mobile Résidence", "Application pour gérer les demandes de logement étudiant.", "active", "#a57bff",
     ["u0", "u2", "u4"], "2025-04-10", "2025-07-15"),
    ("p3", "Dashboard Analytics RH", "Tableau de bord pour la gestion des ressources humaines.", "done", "#57b8ff",
     ["u0", "u1", "u3"], "2025-03-01", "2025-04-20"),
]

# (id, projet, titre, description, assigné, priorité, statut, créé, tags, complexité)
_TASKS = [
    ("t1", "p1", "Concevoir les maquettes Figma", "Wireframes + prototype haute fidélité.", "u3", "high", "done", "2025-04-05", ["Design", "UX"], "simple"),
    ("t2", "p1", "API REST cours (FastAPI)", "Endpoints GET/POST/PUT/DELETE.", "u2", "high", "doing", "2025-04-08", ["Backend"], "complexe"),
    ("t3", "p1", "Intégration React — module quiz", "Composant interactif de quiz.", "u1", "medium", "todo", "2025-04-10", ["Frontend", "React"], "simple"),
    ("t4", "p1", "Auth JWT + refresh tokens", "Système d'authentification sécurisé.", "u2", "high", "doing", "2025-04-09", ["Backend", "Sécurité"], "complexe"),
    ("t5", "p1", "Setup base de données PostgreSQL", "Schéma, migrations Alembic.", "u0", "medium", "done", "2025-04-06", ["DB"], "simple"),
    ("t6", "p2", "Maquettes app mobile", "Écrans principaux en Figma.", "u3", "high", "todo", "2025-04-12", ["Design"], "simple"),
    ("t7", "p2", "Backend Flask — demandes", "API de gestion des demandes.", "u2", "high", "doing", "2025-04-14", ["Backend"], "complexe"),
    ("t8", "p2", "Module notifications push", "Intégration Firebase Cloud Messaging.", "u4", "low", "todo", "2025-04-15", ["Mobile"], "simple"),
    ("t9", "p3", "Dashboard KPIs", "Graphiques d'avancement et métriques.", "u1", "medium", "done", "2025-03-10", ["Frontend"], "simple"),
    ("t10", "p3", "Export PDF rapports", "Génération automatique de rapports.", "u3", "low", "done", "2025-03-20", ["Backend"], "simple"),
]

_MESSAGES = [
    ("m1", "p1", "u1", "J'ai finalisé les maquettes Figma, jetez un œil !"),
    ("m2", "p1", "u2", "Super ! Je commence l'intégration React dès cet après-midi."),
    ("m3", "p1", "u3", "Les wireframes sont validés par le prof. On peut avancer."),
    ("m4", "p1", "u0", "Parfait, daily standup à 14h00 pour tout le monde."),
    ("m5", "p2", "u2", "L'API de demandes est à 80%, ça avance bien."),
    ("m6", "p2", "u4", "J'ai un souci avec Firebase, quelqu'un peut m'aider ?"),
]

_ACTIVITY = [
    ("✅", "<strong>Karim</strong> a terminé « API REST cours »", "#b8ff57", 20),
    ("💬", "<strong>Sarra</strong> a posté un message dans E-Learning", "#a57bff", 45),
    ("➕", "Tâche « Module notifications push » créée dans App Mobile", "#57b8ff", 120),
    ("👤", "<strong>Omar Chahed</strong> a rejoint le projet App Mobile", "#ffb857", 180),
    ("📋", "Projet « Dashboard Analytics RH » marqué comme terminé", "#ff5f87", 1500),
]


def seed_demo_data(db: Session) -> bool:
    """Retourne True si des données ont été insérées."""
    if db.scalar(select(Member.id).limit(1)):
        return False

    pwd = hash_password(DEMO_PASSWORD)  # un seul hash réutilisé : démarrage rapide
    codes = {"u0": {"matricule": "ENS-0001"}, "u1": {"identifier": "ETU-0001"}}  # démo
    members = {mid: Member(id=mid, name=n, first_name=n.split(maxsplit=1)[0], last_name=n.split(maxsplit=1)[1],
                           initials=i, role=r, email=e, color=c, password_hash=pwd, **codes.get(mid, {}))
               for mid, n, i, r, e, c in _MEMBERS}
    db.add_all(members.values())
    db.flush()

    for pid, name, desc, st, color, mids, created, deadline in _PROJECTS:
        db.add(Project(id=pid, name=name, desc=desc, status=st, color=color, created=created, deadline=deadline,
                       owner_id="u0", members=[members[m] for m in mids]))
    db.flush()

    for tid, pid, title, desc, assignee, prio, st, created, tags, cx in _TASKS:
        db.add(Task(id=tid, pid=pid, title=title, desc=desc, assignee=assignee, priority=prio, status=st,
                    created=created, tags=tags, complexity=cx))

    base = datetime.now().replace(second=0, microsecond=0)
    for k, (mid, pid, uid, text) in enumerate(_MESSAGES):
        db.add(Message(id=mid, pid=pid, uid=uid, text=text, created_at=base - timedelta(minutes=(len(_MESSAGES) - k) * 7)))

    for icon, text, color, minutes_ago in reversed(_ACTIVITY):
        db.add(Activity(icon=icon, text=text, color=color, created_at=base - timedelta(minutes=minutes_ago)))

    db.commit()
    return True
