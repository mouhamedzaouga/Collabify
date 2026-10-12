"""Moteur SQLAlchemy + session par requête."""
from sqlalchemy import create_engine, event, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL

_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    future=True,
)

if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_conn, _record):
        # SQLite n'applique pas les clés étrangères par défaut.
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def ensure_schema(bind=None) -> None:
    """Crée les tables et met à niveau une base créée par une version précédente (colonnes ajoutées en v2.2)."""
    from .models import Member  # import tardif : évite l'import circulaire

    bind = bind or engine
    Base.metadata.create_all(bind=bind)
    existing = {c["name"] for c in inspect(bind).get_columns("members")}
    with bind.begin() as conn:
        for col, ddl in (("first_name", "VARCHAR(80)"), ("last_name", "VARCHAR(80)"),
                         ("identifier", "VARCHAR(30)"), ("matricule", "VARCHAR(30)")):
            if col not in existing:
                conn.execute(text(f"ALTER TABLE members ADD COLUMN {col} {ddl}"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_members_identifier ON members (identifier)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_members_matricule ON members (matricule)"))
    # Renseigne prénom/nom pour les comptes existants à partir du nom complet.
    with sessionmaker(bind=bind)() as db:
        for m in db.scalars(select(Member).where(Member.first_name.is_(None))):
            parts = m.name.split(maxsplit=1)
            m.first_name, m.last_name = parts[0], (parts[1] if len(parts) > 1 else "")
        db.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
