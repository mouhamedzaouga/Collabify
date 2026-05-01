"""
routers/messages.py — Messages par canal de projet
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from schemas import MessageCreate, MessageOut
import database as db

router = APIRouter()


def _now_time() -> str:
    return datetime.now().strftime("%H:%M")


@router.get("/{pid}", response_model=list[MessageOut], summary="Messages d'un projet")
def get_messages(pid: str):
    if not db.get_project(pid):
        raise HTTPException(status_code=404, detail=f"Projet '{pid}' introuvable")
    return db.MESSAGES.get(pid, [])


@router.post("/{pid}", response_model=MessageOut, status_code=201, summary="Envoyer un message")
def send_message(pid: str, body: MessageCreate):
    if not db.get_project(pid):
        raise HTTPException(status_code=404, detail=f"Projet '{pid}' introuvable")
    if not db.get_member(body.uid):
        raise HTTPException(status_code=404, detail=f"Membre '{body.uid}' introuvable")

    msg = {
        "id":   db.next_id("message"),
        "pid":  pid,
        "uid":  body.uid,
        "text": body.text,
        "time": _now_time(),
        "date": "Aujourd'hui",
    }

    if pid not in db.MESSAGES:
        db.MESSAGES[pid] = []
    db.MESSAGES[pid].append(msg)

    sender = db.get_member(body.uid)
    proj = db.get_project(pid)
    db.add_activity(
        "💬",
        f"<strong>{sender['name'].split()[0]}</strong> a posté un message dans {proj['name']}",
    )
    return MessageOut(**msg)


@router.delete("/{pid}/{mid}", status_code=204, summary="Supprimer un message")
def delete_message(pid: str, mid: str):
    if not db.get_project(pid):
        raise HTTPException(status_code=404, detail=f"Projet '{pid}' introuvable")
    msgs = db.MESSAGES.get(pid, [])
    msg = next((m for m in msgs if m["id"] == mid), None)
    if not msg:
        raise HTTPException(status_code=404, detail=f"Message '{mid}' introuvable")
    msgs.remove(msg)
