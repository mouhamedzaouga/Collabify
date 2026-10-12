# Collabify — Backend

API REST FastAPI. La documentation complète (installation, configuration, permissions) est dans le [README principal](../README.md).

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload     # http://localhost:8000  ·  Swagger : /docs
pytest                            # après : pip install -r requirements-dev.txt
```

## Endpoints

Tous les endpoints, sauf `POST /api/auth/login` et `GET /api/health`, exigent `Authorization: Bearer <token>`.

| Préfixe | Description |
|---|---|
| `/api/auth` | `POST /login`, `POST /register`, `GET /register-options`, `GET /me`, `POST /change-password` |
| `/api/members` | CRUD des membres, `GET /{id}/stats` |
| `/api/projects` | CRUD, `/dashboard`, `/{id}/members`, `/{id}/board`, `/{id}/progress` |
| `/api/tasks` | CRUD, filtres (`pid`, `assignee`, `status`, `priority`, `complexity`, `search`), `PATCH /{id}/status` |
| `/api/messages` | `GET/POST /{pid}`, `DELETE /{pid}/{mid}` |
| `/api/authorizations` | `GET/POST /`, `PUT /{id}/approve`, `PUT /{id}/reject` |
