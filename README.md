# Collabify — Gestion de Projets Étudiants

## 📋 Description
Collabify est une application web complète de gestion de projets collaboratifs utilisant la méthodologie Scrum. Elle permet aux équipes étudiantes et aux enseignants de planifier, organiser et suivre l'avancement des projets en temps réel, avec un backend robuste et une API REST.

## ✨ Fonctionnalités principales
- 📊 **Tableau de bord** — Vue d'ensemble du sprint avec statistiques et graphiques Chart.js
- 📝 **Product Backlog** — Gestion des user stories avec priorités MoSCoW
- 🏃 **Sprint en cours** — Suivi des tâches du sprint actuel
- 📌 **Kanban Board** — Visualisation des tâches (À faire, En cours, En revue, Terminé)
- 👥 **Gestion d'équipe** — Création et gestion des membres avec différents rôles
- 🔐 **Authentification** — Système de login sécurisé
- 💬 **Messagerie** — Communication entre membres de l'équipe
- 🎯 **Sprint Review** — Résultats et feedback du Product Owner
- 🔄 **Rétrospective** — Analyse des points forts et améliorations
- 📈 **Métriques** — Vélocité, burndown chart et tendances

## 🎭 Rôles disponibles
- **Développeur** — Développe les fonctionnalités
- **UX Designer** — Conçoit l'interface utilisateur
- **QA** — Teste et valide la qualité
- **DevOps** — Gère l'infrastructure et les déploiements
- **Architecte** — Conçoit l'architecture technique
- **Product Owner** — Priorise le backlog et valide les livrables
- **Scrum Master** — Facilite les cérémonies et élimine les obstacles

## 🛠️ Technologies

### Frontend
- **HTML5, CSS3, JavaScript** — Interface responsive
- **Chart.js** — Graphiques et visualisation des métriques
- **Clash Display / Cabinet Grotesk** — Typographie moderne

### Backend
- **Python / FastAPI** — API REST rapide et moderne
- **SQLAlchemy** — ORM pour la base de données
- **Authentification JWT** — Sécurisation des routes

## 📦 Installation

### Prérequis
- Python 3.8+
- pip

### Étapes
1. Clonez le repository :
```bash
   git clone https://github.com/mouhamedzaouga/Collabify.git
   cd Collabify
```

2. Installez les dépendances backend :
```bash
   pip install -r backend/requirements.txt
```

3. Lancez le backend :
```bash
   cd backend
   uvicorn main:app --reload
```

4. Ouvrez `frontend/projectflow_app.html` dans un navigateur moderne.

> **Sur Windows**, vous pouvez utiliser `run.bat` pour démarrer le projet automatiquement.

## 📄 Structure des fichiers
Collabify/
├── backend/
│   ├── main.py           # Point d'entrée FastAPI
│   ├── auth.py           # Authentification JWT
│   ├── database.py       # Configuration base de données
│   ├── projects.py       # Gestion des projets
│   ├── tasks.py          # Gestion des tâches
│   ├── members.py        # Gestion des membres
│   ├── messages.py       # Messagerie
│   ├── schemas.py        # Schémas Pydantic
│   ├── requirements.txt  # Dépendances Python
│   └── README.md         # Doc backend
├── frontend/
│   └── projectflow_app.html  # Application principale
├── patch_frontend.py     # Script de mise à jour frontend
├── run.bat               # Démarrage rapide Windows
├── .gitignore
└── README.md

## 👥 Équipe (Sprint 2)
- **Mouhamed Zaouga** 
- 
## 📞 Support
Pour des questions ou des améliorations, créez une issue sur le repository GitHub.

## 📄 Licence
Ce projet est fourni à titre d'exemple pédagogique.

---
**Version:** 2.0 | **Date:** 1 mai 2026