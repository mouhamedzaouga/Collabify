"""Point d'entrée FastAPI : `uvicorn app.main:app --reload` depuis le dossier backend/."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401  (enregistre les tables)
from .config import CORS_ORIGINS, FRONTEND_DIR, SEED_DEMO_DATA
from .database import SessionLocal, ensure_schema
from .routers import auth, authorizations, members, messages, projects, tasks
from .seed import seed_demo_data

VERSION = "2.2.0"


class TrailingSlashMiddleware:
    """Accepte `/api/members` comme `/api/members/` sans redirection.

    Le frontend est monté sur « / » : sans cela, la redirection automatique de FastAPI ne se
    déclenche pas et les URL sans slash final renvoient une 404.
    """

    ROOTS = {"/api/members", "/api/projects", "/api/tasks", "/api/authorizations"}

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"] in self.ROOTS:
            scope = dict(scope)
            scope["path"] += "/"
            if scope.get("raw_path"):
                scope["raw_path"] += b"/"
        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_schema()
    if SEED_DEMO_DATA:
        with SessionLocal() as db:
            seed_demo_data(db)
    yield


app = FastAPI(
    title="Collabify API",
    description="Backend de la plateforme de gestion de projets étudiants Collabify.",
    version=VERSION,
    lifespan=lifespan,
)

app.add_middleware(TrailingSlashMiddleware)

# L'authentification utilise un en-tête Bearer (pas de cookies) : pas besoin de allow_credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(members.router, prefix="/api/members", tags=["Members"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(authorizations.router, prefix="/api/authorizations", tags=["Authorizations"])


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "healthy", "version": VERSION}


# Sert le frontend sur http://localhost:8000/ (une seule commande pour tout lancer).
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
