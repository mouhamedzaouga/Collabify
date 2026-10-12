# Collabify — Gestion de projets étudiants

![CI](https://github.com/mouhamedzaouga/Collabify/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)
![License](https://img.shields.io/badge/license-MIT-green)

Collabify est une application web full-stack de gestion de projets pédagogiques. Les **enseignants** créent et suivent les projets ; les **étudiants** organisent leurs tâches, discutent par projet et demandent l'autorisation de l'enseignant pour les tâches complexes.

## ✨ Fonctionnalités

- 👤 **Création de compte** — au choix *Étudiant* (email, identifiant, nom, prénom) ou *Enseignant* (email, nom, prénom, matricule), avec connexion immédiate
- 🔐 **Authentification JWT** — mots de passe hachés (scrypt), sessions à expiration, limitation des tentatives de connexion et de création de comptes
- 🛡️ **Rôles et permissions appliqués côté serveur** — Enseignant / Étudiant (voir le tableau ci-dessous)
- 📊 **Tableau de bord** — statistiques personnelles, projets récents, fil d'activité, graphiques Chart.js
- 📁 **Projets** — création, édition, échéances (alerte de retard), gestion des membres, export PDF
- ✅ **Tâches** — priorités, tags, complexité, vue liste et **Kanban** (À faire · En cours · En revue · Terminé)
- 🔏 **Demandes d'autorisation** — un étudiant ne crée pas directement une tâche « complexe » : il envoie une demande que l'enseignant approuve (la tâche est alors créée) ou refuse avec un commentaire
- 💬 **Messagerie** par projet
- 📈 **Avancement** — progression globale et charge par membre
- 💾 **Persistance SQLite** via SQLAlchemy 2.0 (données conservées entre les redémarrages)

## 🔑 Permissions

| Action | Enseignant | Étudiant |
|---|:---:|:---:|
| Créer son propre compte | ✅ (matricule) | ✅ (identifiant) |
| Voir tous les projets | ✅ | ❌ (uniquement les siens) |
| Créer / modifier / supprimer un projet | ✅ | ❌ |
| Gérer les membres de l'application | ✅ | ❌ (profil personnel uniquement) |
| Créer une tâche simple | ✅ | ✅ (dans ses projets) |
| Créer une tâche complexe | ✅ | via demande d'autorisation |
| Approuver / refuser une demande | ✅ | ❌ |
| Écrire dans le chat d'un projet | ✅ | ✅ (ses projets) |
| Supprimer un message | ✅ | ✅ (les siens) |

## 🛠️ Stack

| Couche | Technologies |
|---|---|
| Frontend | HTML5 / CSS3 / JavaScript vanilla, Chart.js |
| Backend | Python 3.10+, FastAPI, Pydantic v2 |
| Données | SQLAlchemy 2.0 + SQLite (remplaçable via `COLLABIFY_DATABASE_URL`) |
| Sécurité | PyJWT, scrypt (stdlib), CORS configurable, échappement HTML côté client et dans le fil d'activité |
| Qualité | pytest (26 tests d'API), GitHub Actions |

## 🚀 Démarrage rapide

```bash
git clone https://github.com/mouhamedzaouga/Collabify.git
cd Collabify
```

**Windows** : double-cliquez sur `run.bat`  
**Linux / macOS** : `./run.sh`

Le script crée un environnement virtuel, installe les dépendances, lance le serveur et l'application est disponible sur **http://localhost:8000** (le backend sert aussi le frontend). La documentation interactive de l'API est sur **http://localhost:8000/docs**.

<details>
<summary>Lancement manuel</summary>

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
</details>

<details>
<summary>Problème au lancement ?</summary>

- **La fenêtre se ferme ou affiche une erreur** : `run.bat` reste ouvert en cas d'erreur et indique l'étape qui a échoué.
- **« Python est introuvable »** : installez Python 3.10+ depuis [python.org](https://www.python.org/downloads/) en cochant *Add python.exe to PATH*.
- **Lancement depuis le zip** : extrayez-le complètement avant de lancer `run.bat`.
- **Port 8000 déjà utilisé** : fermez l'autre programme ou changez `--port 8000` dans `run.bat`.
</details>

### Créer un compte

Sur l'écran d'accueil, onglet **Créer un compte**, choisissez votre profil :

| Profil | Champs demandés |
|---|---|
| Étudiant | Prénom, nom, email, **identifiant étudiant**, mot de passe |
| Enseignant | Prénom, nom, email, **matricule**, mot de passe (+ code d'invitation si configuré) |

L'identifiant et le matricule sont uniques (insensibles à la casse) et visibles uniquement par leur propriétaire. Un nouvel étudiant ne voit aucun projet tant qu'un enseignant ne l'a pas ajouté à un projet.

> 🔒 **Sécurité** : le matricule n'est pas vérifié par le serveur. Pour que personne ne puisse se déclarer enseignant, définissez `COLLABIFY_TEACHER_CODE` (code d'invitation à communiquer aux enseignants) avant de mettre l'application en ligne.

### Comptes de démonstration

Mot de passe pour tous les comptes seed : `collabify`

| Email | Rôle |
|---|---|
| `m.zaouga@univ.tn` | Enseignant |
| `n.daasi@univ.tn` | Étudiant |

> ⚠️ Les données de démonstration sont créées au premier lancement. En dehors d'une démo, définissez `COLLABIFY_SEED_DEMO=0` et créez vos propres comptes.

## ⚙️ Configuration

Variables d'environnement (voir [`.env.example`](.env.example)) :

| Variable | Rôle | Défaut |
|---|---|---|
| `COLLABIFY_SECRET_KEY` | Clé de signature des JWT — **à définir en production** (hébergeur, Docker…) | générée et enregistrée dans `backend/.secret_key` au 1er lancement |
| `COLLABIFY_DATABASE_URL` | URL SQLAlchemy | `sqlite:///backend/collabify.db` |
| `COLLABIFY_CORS_ORIGINS` | Origines autorisées, séparées par des virgules | `*` |
| `COLLABIFY_TOKEN_MINUTES` | Durée de vie d'un token | `480` |
| `COLLABIFY_TEACHER_CODE` | Code d'invitation exigé pour créer un compte Enseignant (**recommandé en ligne**) | vide = inscription enseignant libre |
| `COLLABIFY_REGISTER_MAX` | Créations de compte max. par adresse IP et par fenêtre de 10 min | `30` |
| `COLLABIFY_SEED_DEMO` | Insérer les données de démo si la base est vide | `1` |

## 🧪 Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Les tests couvrent l'authentification, l'inscription (validation, doublons, code d'invitation, migration d'une ancienne base), la limitation des tentatives, les permissions par rôle, le flux d'autorisation des tâches complexes, les suppressions en cascade et l'échappement du fil d'activité.

## 📁 Structure

```
Collabify/
├── backend/
│   ├── app/
│   │   ├── main.py            # Application FastAPI, CORS, service du frontend
│   │   ├── config.py          # Configuration via variables d'environnement
│   │   ├── database.py        # Moteur et sessions SQLAlchemy
│   │   ├── models.py          # Modèles ORM
│   │   ├── schemas.py         # Validation Pydantic
│   │   ├── security.py        # scrypt, JWT, limitation des connexions
│   │   ├── deps.py            # Utilisateur courant, rôles, accès aux projets
│   │   ├── services.py        # Fil d'activité, sérialisation
│   │   ├── seed.py            # Données de démonstration
│   │   └── routers/           # auth, members, projects, tasks, messages, authorizations
│   ├── tests/                 # Tests pytest
│   └── requirements*.txt
├── frontend/
│   └── index.html             # Application monopage
├── docs/                      # Documents du projet
├── .github/workflows/ci.yml   # Intégration continue
├── run.bat · run.sh           # Lancement en une commande
└── .env.example
```

## 🗺️ Pistes d'amélioration

- Migrations de base de données (Alembic) et PostgreSQL en production
- Refresh tokens et stockage du token en cookie `HttpOnly`
- Notifications temps réel (WebSocket) pour le chat et les autorisations
- Découpage du frontend en modules / framework

## 👥 Auteur

**Mouhamed Zaouga** — Faculté des Sciences de Bizerte

## 📄 Licence

Distribué sous licence MIT — voir [LICENSE](LICENSE).

---
**Version** 2.2.0
