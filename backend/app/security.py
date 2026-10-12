"""Hachage des mots de passe (scrypt, stdlib), JWT et limitation des tentatives de connexion."""
import hashlib
import hmac
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone

import jwt

from .config import (ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, LOGIN_MAX_ATTEMPTS, LOGIN_WINDOW_SECONDS,
                     REGISTER_MAX_ATTEMPTS, REGISTER_WINDOW_SECONDS, SECRET_KEY)

_N, _R, _P = 2 ** 14, 8, 1


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, n, r, p, salt_hex, hash_hex = stored.split("$")
        dk = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=int(n), r=int(r), p=int(p))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


# Hash factice pour égaliser le temps de réponse quand l'email n'existe pas.
DUMMY_HASH = hash_password("not-a-real-password")


def create_access_token(member_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": member_id, "iat": now, "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)}
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


class LoginThrottle:
    """Limite en mémoire : N événements par clé (ex. email+ip) sur une fenêtre glissante."""

    def __init__(self, max_attempts: int = LOGIN_MAX_ATTEMPTS, window_seconds: int = LOGIN_WINDOW_SECONDS) -> None:
        self.max_attempts, self.window_seconds = max_attempts, window_seconds
        self._fails: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _prune(self, key: str) -> list[float]:
        cutoff = time.monotonic() - self.window_seconds
        fails = [t for t in self._fails.get(key, []) if t > cutoff]
        self._fails[key] = fails
        return fails

    def blocked(self, key: str) -> bool:
        with self._lock:
            return len(self._prune(key)) >= self.max_attempts

    def fail(self, key: str) -> None:
        with self._lock:
            self._prune(key).append(time.monotonic())

    def reset(self, key: str | None = None) -> None:
        with self._lock:
            if key is None:
                self._fails.clear()
            else:
                self._fails.pop(key, None)


login_throttle = LoginThrottle()
register_throttle = LoginThrottle(REGISTER_MAX_ATTEMPTS, REGISTER_WINDOW_SECONDS)
