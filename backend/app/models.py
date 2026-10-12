"""Modèles SQLAlchemy 2.0."""
import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def new_id(prefix: str) -> str:
    """Identifiant court et lisible : p1a2b3c4d, t…, u…, m…, r…"""
    return f"{prefix}{uuid.uuid4().hex[:8]}"


def now() -> datetime:
    return datetime.now()


project_members = Table(
    "project_members",
    Base.metadata,
    Column("project_id", ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("member_id", ForeignKey("members.id", ondelete="CASCADE"), primary_key=True),
)


class Member(Base):
    __tablename__ = "members"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    initials: Mapped[str] = mapped_column(String(4))
    first_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    role: Mapped[str] = mapped_column(String(32))
    identifier: Mapped[str | None] = mapped_column(String(30), unique=True, index=True, nullable=True)  # étudiant
    matricule: Mapped[str | None] = mapped_column(String(30), unique=True, index=True, nullable=True)   # enseignant
    email: Mapped[str] = mapped_column(String(190), unique=True, index=True)
    color: Mapped[str] = mapped_column(String(16), default="#5e5e88")
    password_hash: Mapped[str] = mapped_column(String(255))


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    desc: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="active")
    color: Mapped[str] = mapped_column(String(16), default="#b8ff57")
    created: Mapped[str] = mapped_column(String(10))
    deadline: Mapped[str] = mapped_column(String(10), default="")
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("members.id", ondelete="SET NULL"), nullable=True)

    members: Mapped[list[Member]] = relationship(secondary=project_members, order_by="Member.id")
    tasks: Mapped[list["Task"]] = relationship(back_populates="project", cascade="all, delete-orphan", passive_deletes=True)


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    pid: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    desc: Mapped[str] = mapped_column(Text, default="")
    assignee: Mapped[str] = mapped_column(ForeignKey("members.id"), index=True)
    priority: Mapped[str] = mapped_column(String(8), default="medium")
    status: Mapped[str] = mapped_column(String(8), default="todo")
    created: Mapped[str] = mapped_column(String(10))
    tags: Mapped[list] = mapped_column(JSON, default=list)
    complexity: Mapped[str] = mapped_column(String(10), default="simple")

    project: Mapped[Project] = relationship(back_populates="tasks")


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    pid: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    uid: Mapped[str] = mapped_column(ForeignKey("members.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class AuthRequest(Base):
    __tablename__ = "auth_requests"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("members.id", ondelete="CASCADE"), index=True)
    pid: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    desc: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(8), default="medium")
    assignee: Mapped[str] = mapped_column(ForeignKey("members.id", ondelete="CASCADE"))
    tags: Mapped[list] = mapped_column(JSON, default=list)
    reason: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(10), default="pending")
    created: Mapped[str] = mapped_column(String(10))
    reviewed_by: Mapped[str | None] = mapped_column(String(16), nullable=True)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(16), nullable=True)


class Activity(Base):
    __tablename__ = "activity"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    icon: Mapped[str] = mapped_column(String(8))
    text: Mapped[str] = mapped_column(Text)
    color: Mapped[str] = mapped_column(String(16), default="#b8ff57")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
