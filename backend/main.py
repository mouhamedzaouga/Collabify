from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import projects, tasks, members, messages, auth

app = FastAPI(
    title="Collabify API",
    description="Backend pour la plateforme de gestion de projets étudiants Collabify",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, remplacer par l'URL du frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,     prefix="/api/auth",     tags=["Auth"])
app.include_router(members.router,  prefix="/api/members",  tags=["Members"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(tasks.router,    prefix="/api/tasks",    tags=["Tasks"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": "Collabify API", "version": "1.0.0"}


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "healthy"}
