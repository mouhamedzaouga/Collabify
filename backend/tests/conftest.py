import os
import tempfile

# Doit être défini AVANT l'import de l'application.
_tmp = tempfile.mkdtemp()
os.environ["COLLABIFY_DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["COLLABIFY_SECRET_KEY"] = "test-secret-key-test-secret-key-1234"
os.environ["COLLABIFY_SEED_DEMO"] = "1"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security import login_throttle, register_throttle


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _reset_throttle():
    login_throttle.reset()
    register_throttle.reset()


def login(client, email, password="collabify"):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def teacher(client):
    return login(client, "m.zaouga@univ.tn")


@pytest.fixture()
def student(client):
    return login(client, "n.daasi@univ.tn")
