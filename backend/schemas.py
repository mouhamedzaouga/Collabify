"""
schemas.py — Pydantic models for request / response validation
"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    member: "MemberOut"


# ── Members ───────────────────────────────────────────────────────────────────
class MemberCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: str
    role: Literal["Scrum Master", "Product Owner", "Développeur", "UX Designer", "QA", "DevOps"]
    color: Optional[str] = None


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[Literal["Scrum Master", "Product Owner", "Développeur", "UX Designer", "QA", "DevOps"]] = None
    color: Optional[str] = None


class MemberOut(BaseModel):
    id: str
    name: str
    initials: str
    role: str
    email: str
    color: str


# ── Projects ──────────────────────────────────────────────────────────────────
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2)
    desc: str = ""
    color: str = "#b8ff57"
    deadline: str = ""
    status: Literal["active", "done", "paused"] = "active"
    members: list[str] = []


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    desc: Optional[str] = None
    color: Optional[str] = None
    deadline: Optional[str] = None
    status: Optional[Literal["active", "done", "paused"]] = None


class ProjectOut(BaseModel):
    id: str
    name: str
    desc: str
    status: str
    color: str
    members: list[str]
    created: str
    deadline: str
    completion: int = 0
    task_count: int = 0


class ProjectMembersUpdate(BaseModel):
    member_ids: list[str]


# ── Tasks ─────────────────────────────────────────────────────────────────────
class TaskCreate(BaseModel):
    pid: str
    title: str = Field(..., min_length=2)
    desc: str = ""
    assignee: str = "u0"
    priority: Literal["high", "medium", "low"] = "medium"
    status: Literal["todo", "doing", "review", "done"] = "todo"
    tags: list[str] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    desc: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[Literal["high", "medium", "low"]] = None
    status: Optional[Literal["todo", "doing", "review", "done"]] = None
    tags: Optional[list[str]] = None


class TaskStatusUpdate(BaseModel):
    status: Literal["todo", "doing", "review", "done"]


class TaskOut(BaseModel):
    id: str
    pid: str
    title: str
    desc: str
    assignee: str
    priority: str
    status: str
    created: str
    tags: list[str]


# ── Messages ──────────────────────────────────────────────────────────────────
class MessageCreate(BaseModel):
    uid: str
    text: str = Field(..., min_length=1)


class MessageOut(BaseModel):
    id: str
    pid: str
    uid: str
    text: str
    time: str
    date: str


# ── Stats / Dashboard ─────────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    active_projects: int
    total_projects: int
    my_tasks: int
    my_done_tasks: int
    members: int
    my_completion_pct: int


class ActivityItem(BaseModel):
    icon: str
    text: str
    time: str
    color: str
