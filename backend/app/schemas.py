"""Schémas Pydantic (validation des entrées / forme des sorties)."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Role = Literal["Enseignant", "Étudiant", "Développeur", "UX Designer", "QA", "DevOps"]
Priority = Literal["high", "medium", "low"]
TaskStatus = Literal["todo", "doing", "review", "done"]
Complexity = Literal["simple", "complexe"]
ProjectStatus = Literal["active", "done", "paused"]


class _Strict(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


# ── Auth ──────────────────────────────────────────────────────────────────────
class LoginRequest(_Strict):
    email: str
    password: str


class MemberOut(BaseModel):
    id: str
    name: str
    initials: str
    role: str
    email: str
    color: str


class MeOut(MemberOut):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    identifier: Optional[str] = None
    matricule: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    member: MeOut


_CODE = r"^[A-Za-z0-9._-]{3,30}$"


class RegisterRequest(_Strict):
    """Inscription : Étudiant → identifiant requis ; Enseignant → matricule requis."""
    role: Literal["Étudiant", "Enseignant"]
    first_name: str = Field(..., min_length=1, max_length=60)
    last_name: str = Field(..., min_length=1, max_length=60)
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=190)
    password: str = Field(..., min_length=8, max_length=128)
    identifier: Optional[str] = Field(default=None, pattern=_CODE)
    matricule: Optional[str] = Field(default=None, pattern=_CODE)
    teacher_code: Optional[str] = Field(default=None, max_length=128)

    @field_validator("identifier", "matricule", "teacher_code", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        return None if isinstance(v, str) and not v.strip() else v

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.lower()

    @model_validator(mode="after")
    def _role_fields(self):
        if self.role == "Étudiant":
            if not self.identifier:
                raise ValueError("L'identifiant est obligatoire pour un étudiant")
            self.matricule = None
        else:
            if not self.matricule:
                raise ValueError("Le matricule est obligatoire pour un enseignant")
            self.identifier = None
        return self


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ── Members ───────────────────────────────────────────────────────────────────
class MemberCreate(_Strict):
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=190)
    role: Role
    password: str = Field(default="collabify", min_length=6, max_length=128)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.lower()


class MemberUpdate(_Strict):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    email: Optional[str] = Field(default=None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=190)
    role: Optional[Role] = None
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")


# ── Projects ──────────────────────────────────────────────────────────────────
class ProjectCreate(_Strict):
    name: str = Field(..., min_length=2, max_length=160)
    desc: str = Field(default="", max_length=4000)
    color: str = Field(default="#b8ff57", pattern=r"^#[0-9a-fA-F]{6}$")
    deadline: str = Field(default="", pattern=r"^(\d{4}-\d{2}-\d{2})?$")
    status: ProjectStatus = "active"
    members: list[str] = []


class ProjectUpdate(_Strict):
    name: Optional[str] = Field(default=None, min_length=2, max_length=160)
    desc: Optional[str] = Field(default=None, max_length=4000)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    deadline: Optional[str] = Field(default=None, pattern=r"^(\d{4}-\d{2}-\d{2})?$")
    status: Optional[ProjectStatus] = None


class ProjectOut(BaseModel):
    id: str
    name: str
    desc: str
    status: str
    color: str
    members: list[str]
    created: str
    deadline: str
    owner_id: Optional[str] = None
    completion: int = 0
    task_count: int = 0


class ProjectMembersUpdate(BaseModel):
    member_ids: list[str]


# ── Tasks ─────────────────────────────────────────────────────────────────────
class TaskCreate(_Strict):
    pid: str
    title: str = Field(..., min_length=2, max_length=200)
    desc: str = Field(default="", max_length=4000)
    assignee: Optional[str] = None            # défaut : l'utilisateur connecté
    priority: Priority = "medium"
    status: TaskStatus = "todo"
    tags: list[str] = Field(default=[], max_length=10)
    complexity: Complexity = "simple"


class TaskUpdate(_Strict):
    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    desc: Optional[str] = Field(default=None, max_length=4000)
    assignee: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[TaskStatus] = None
    tags: Optional[list[str]] = Field(default=None, max_length=10)
    complexity: Optional[Complexity] = None


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    pid: str
    title: str
    desc: str
    assignee: str
    priority: str
    status: str
    created: str
    tags: list[str]
    complexity: str = "simple"


# ── Messages ──────────────────────────────────────────────────────────────────
class MessageCreate(_Strict):
    text: str = Field(..., min_length=1, max_length=4000)
    uid: Optional[str] = None  # ignoré : l'expéditeur est toujours l'utilisateur authentifié


class MessageOut(BaseModel):
    id: str
    pid: str
    uid: str
    text: str
    time: str
    date: str


# ── Demandes d'autorisation (Étudiant → Enseignant) ────────────────────────────
class AuthRequestCreate(_Strict):
    pid: str
    title: str = Field(..., min_length=2, max_length=200)
    desc: str = Field(default="", max_length=4000)
    priority: Priority = "medium"
    assignee: Optional[str] = None
    tags: list[str] = Field(default=[], max_length=10)
    reason: str = Field(default="", max_length=2000)
    student_id: Optional[str] = None  # ignoré : toujours l'utilisateur connecté


class AuthRequestDecision(_Strict):
    comment: Optional[str] = Field(default=None, max_length=2000)
    reviewer_id: Optional[str] = None  # ignoré : toujours l'utilisateur connecté


class AuthRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    student_id: str
    pid: str
    title: str
    desc: str
    priority: str
    assignee: str
    tags: list[str]
    reason: str
    status: Literal["pending", "approved", "rejected"]
    created: str
    reviewed_by: Optional[str] = None
    review_comment: Optional[str] = None
    task_id: Optional[str] = None
