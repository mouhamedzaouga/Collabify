# Collabify — Backend FastAPI

Backend REST API pour la plateforme de gestion de projets étudiants **Collabify**.

---

## 🚀 Installation & lancement

```bash
# 1. Cloner / copier ce dossier
cd collabify-backend

# 2. Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer le serveur de développement
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

L'API est disponible sur **http://localhost:8000**  
La documentation interactive (Swagger UI) : **http://localhost:8000/docs**  
La doc ReDoc : **http://localhost:8000/redoc**

---

## 📦 Structure du projet

```
collabify-backend/
├── main.py              # Point d'entrée FastAPI + CORS + routers
├── database.py          # Store in-memory + données initiales + helpers
├── schemas.py           # Modèles Pydantic (validation I/O)
├── requirements.txt
├── README.md
└── routers/
    ├── auth.py          # POST /api/auth/login  GET /api/auth/me
    ├── members.py       # CRUD /api/members/
    ├── projects.py      # CRUD /api/projects/ + board, progress, members
    ├── tasks.py         # CRUD /api/tasks/ + PATCH status
    └── messages.py      # GET/POST/DELETE /api/messages/{pid}
```

---

## 🗺️ Endpoints

### Auth
| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/api/auth/login` | Connexion (email + password) |
| GET  | `/api/auth/me?token=…` | Profil du connecté |

> Mot de passe démo pour tous : **collabify**

### Members
| Méthode | URL | Description |
|---------|-----|-------------|
| GET    | `/api/members/` | Liste tous les membres |
| GET    | `/api/members/{uid}` | Détail d'un membre |
| GET    | `/api/members/{uid}/stats` | Stats & tâches d'un membre |
| POST   | `/api/members/` | Créer un membre |
| PUT    | `/api/members/{uid}` | Modifier un membre |
| DELETE | `/api/members/{uid}` | Supprimer un membre |

### Projects
| Méthode | URL | Description |
|---------|-----|-------------|
| GET    | `/api/projects/?status=active&member_id=u0` | Lister (filtres optionnels) |
| GET    | `/api/projects/dashboard?uid=u0` | Stats du tableau de bord |
| GET    | `/api/projects/{pid}` | Détail d'un projet |
| POST   | `/api/projects/` | Créer un projet |
| PUT    | `/api/projects/{pid}` | Modifier un projet |
| DELETE | `/api/projects/{pid}` | Supprimer un projet |
| GET    | `/api/projects/{pid}/members` | Membres du projet |
| POST   | `/api/projects/{pid}/members` | Ajouter des membres |
| DELETE | `/api/projects/{pid}/members/{uid}` | Retirer un membre |
| GET    | `/api/projects/{pid}/board` | Vue Kanban |
| GET    | `/api/projects/{pid}/progress` | Avancement & charge |

### Tasks
| Méthode | URL | Description |
|---------|-----|-------------|
| GET    | `/api/tasks/?pid=p1&assignee=u0&status=doing` | Lister (filtres cumulables) |
| GET    | `/api/tasks/{tid}` | Détail d'une tâche |
| POST   | `/api/tasks/` | Créer une tâche |
| PUT    | `/api/tasks/{tid}` | Modifier une tâche |
| PATCH  | `/api/tasks/{tid}/status` | Changer le statut seulement |
| DELETE | `/api/tasks/{tid}` | Supprimer une tâche |

### Messages
| Méthode | URL | Description |
|---------|-----|-------------|
| GET    | `/api/messages/{pid}` | Messages d'un projet |
| POST   | `/api/messages/{pid}` | Envoyer un message |
| DELETE | `/api/messages/{pid}/{mid}` | Supprimer un message |

---

## 🔗 Intégration avec le frontend

Dans le fichier HTML du frontend, remplacez l'URL de base :

```js
const API = "http://localhost:8000/api";

// Exemple : charger les projets
const res  = await fetch(`${API}/projects/`);
const data = await res.json();
```

---

## 🛠️ Passer en production (guide)

1. **Base de données** — Remplacer le store in-memory par **SQLAlchemy + PostgreSQL** (ou SQLite pour les petits projets).
2. **Authentification** — Utiliser `python-jose` pour de vrais JWT signés + `passlib[bcrypt]` pour les mots de passe.
3. **Variables d'environnement** — Utiliser `pydantic-settings` avec un `.env`.
4. **CORS** — Restreindre `allow_origins` à l'URL exacte du frontend.
5. **WebSockets** — Ajouter `websockets` pour les messages en temps réel.
6. **Déploiement** — Gunicorn + Uvicorn workers, ou Docker.

---

## 📝 Exemple de requête cURL

```bash
# Connexion
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"m.zaouga@univ.tn","password":"collabify"}'

# Créer une tâche
curl -X POST http://localhost:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"pid":"p1","title":"Nouvelle tâche","priority":"high","assignee":"u0","tags":["Backend"]}'

# Changer le statut
curl -X PATCH http://localhost:8000/api/tasks/t1/status \
  -H "Content-Type: application/json" \
  -d '{"status":"done"}'
```
