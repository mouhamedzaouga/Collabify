"""Messagerie par projet. L'expéditeur est toujours l'utilisateur authentifié."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_accessible_project, get_current_user, is_teacher
from ..models import Member, Message, new_id
from ..schemas import MessageCreate, MessageOut
from ..services import h, log_activity, message_out

router = APIRouter()


@router.get("/{pid}", response_model=list[MessageOut], summary="Messages d'un projet")
def get_messages(pid: str, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    get_accessible_project(db, pid, user)
    msgs = db.scalars(select(Message).where(Message.pid == pid).order_by(Message.created_at, Message.id)).all()
    return [message_out(m) for m in msgs]


@router.post("/{pid}", response_model=MessageOut, status_code=201, summary="Envoyer un message")
def send_message(pid: str, body: MessageCreate, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    project = get_accessible_project(db, pid, user)
    msg = Message(id=new_id("m"), pid=pid, uid=user.id, text=body.text)
    db.add(msg)
    log_activity(db, "💬", f"<strong>{h(user.name.split()[0])}</strong> a posté un message dans {h(project.name)}")
    db.commit()
    db.refresh(msg)
    return message_out(msg)


@router.delete("/{pid}/{mid}", status_code=204, summary="Supprimer un message (auteur ou enseignant)")
def delete_message(pid: str, mid: str, db: Session = Depends(get_db), user: Member = Depends(get_current_user)):
    get_accessible_project(db, pid, user)
    msg = db.get(Message, mid)
    if not msg or msg.pid != pid:
        raise HTTPException(status_code=404, detail=f"Message '{mid}' introuvable")
    if msg.uid != user.id and not is_teacher(user):
        raise HTTPException(status_code=403, detail="Vous ne pouvez supprimer que vos propres messages")
    db.delete(msg)
    db.commit()
