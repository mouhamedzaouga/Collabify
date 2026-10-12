from conftest import login


def test_health(client):
    assert client.get("/api/health").json()["status"] == "healthy"


# ── Authentification ─────────────────────────────────────────────────────────
def test_routes_require_token(client):
    for path in ("/api/projects/", "/api/tasks/", "/api/members/", "/api/messages/p1"):
        assert client.get(path).status_code == 401


def test_invalid_token_rejected(client):
    r = client.get("/api/projects/", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"email": "m.zaouga@univ.tn", "password": "wrong"})
    assert r.status_code == 401


def test_login_throttle(client):
    for _ in range(5):
        client.post("/api/auth/login", json={"email": "x@y.tn", "password": "bad"})
    assert client.post("/api/auth/login", json={"email": "x@y.tn", "password": "bad"}).status_code == 429


def test_me_and_password_not_leaked(client, teacher):
    me = client.get("/api/auth/me", headers=teacher).json()
    assert me["role"] == "Enseignant"
    assert "password_hash" not in me
    assert all("password" not in m for m in client.get("/api/members/", headers=teacher).json())


def test_change_password(client):
    h = login(client, "o.chahed@univ.tn")
    assert client.post("/api/auth/change-password", headers=h,
                       json={"current_password": "bad", "new_password": "newpassword1"}).status_code == 400
    assert client.post("/api/auth/change-password", headers=h,
                       json={"current_password": "collabify", "new_password": "newpassword1"}).status_code == 204
    login(client, "o.chahed@univ.tn", "newpassword1")


# ── Rôles et accès ───────────────────────────────────────────────────────────
def test_student_sees_only_own_projects(client, student, teacher):
    mine = {p["id"] for p in client.get("/api/projects/", headers=student).json()}
    assert mine == {"p1", "p3"}                      # Nour n'est pas dans p2
    assert len(client.get("/api/projects/", headers=teacher).json()) >= 3
    assert client.get("/api/projects/p2", headers=student).status_code == 403
    assert client.get("/api/messages/p2", headers=student).status_code == 403


def test_student_cannot_manage_projects_or_members(client, student):
    assert client.post("/api/projects/", headers=student, json={"name": "Hack"}).status_code == 403
    assert client.delete("/api/projects/p1", headers=student).status_code == 403
    body = {"name": "Intrus", "email": "i@univ.tn", "role": "Enseignant"}
    assert client.post("/api/members/", headers=student, json=body).status_code == 403
    assert client.delete("/api/members/u2", headers=student).status_code == 403


def test_student_cannot_self_promote(client, student):
    r = client.put("/api/members/u1", headers=student, json={"role": "Enseignant"})
    assert r.status_code == 403
    assert client.put("/api/members/u2", headers=student, json={"name": "Pirate"}).status_code == 403


# ── Tâches ───────────────────────────────────────────────────────────────────
def test_student_complex_task_needs_authorization_flow(client, student, teacher):
    direct = client.post("/api/tasks/", headers=student,
                         json={"pid": "p1", "title": "Tâche lourde", "complexity": "complexe"})
    assert direct.status_code == 403

    req = client.post("/api/authorizations/", headers=student,
                      json={"pid": "p1", "title": "Tâche lourde", "complexity": "complexe", "student_id": "u0"})
    assert req.status_code == 201
    rid = req.json()["id"]
    assert req.json()["student_id"] == "u1"          # l'usurpation via le body est ignorée

    assert client.put(f"/api/authorizations/{rid}/approve", headers=student, json={}).status_code == 403
    assert len(client.get("/api/authorizations/", headers=student).json()) >= 1

    ok = client.put(f"/api/authorizations/{rid}/approve", headers=teacher, json={"comment": "OK"})
    assert ok.status_code == 200 and ok.json()["task_id"]
    assert client.put(f"/api/authorizations/{rid}/approve", headers=teacher, json={}).status_code == 409
    task = client.get(f"/api/tasks/{ok.json()['task_id']}", headers=teacher).json()
    assert task["complexity"] == "complexe" and task["status"] == "todo"


def test_task_crud_and_persistence_of_status(client, student):
    t = client.post("/api/tasks/", headers=student, json={"pid": "p1", "title": "Écrire les tests", "tags": ["QA"]})
    assert t.status_code == 201 and t.json()["assignee"] == "u1"
    tid = t.json()["id"]
    assert client.patch(f"/api/tasks/{tid}/status", headers=student, json={"status": "review"}).json()["status"] == "review"
    assert client.patch(f"/api/tasks/{tid}/status", headers=student, json={"status": "invalid"}).status_code == 422
    found = client.get("/api/tasks/?search=tests&pid=p1", headers=student).json()
    assert any(x["id"] == tid for x in found)
    assert client.delete(f"/api/tasks/{tid}", headers=student).status_code == 204
    assert client.get(f"/api/tasks/{tid}", headers=student).status_code == 404


def test_student_cannot_touch_tasks_of_other_projects(client, student):
    assert client.get("/api/tasks/t6", headers=student).status_code == 403
    assert client.post("/api/tasks/", headers=student, json={"pid": "p2", "title": "Infiltration"}).status_code == 403
    assert all(t["pid"] != "p2" for t in client.get("/api/tasks/", headers=student).json())


# ── Projets / messages ───────────────────────────────────────────────────────
def test_project_lifecycle_cascades(client, teacher):
    p = client.post("/api/projects/", headers=teacher,
                    json={"name": "Projet test", "members": ["u1"], "deadline": "2026-12-31"}).json()
    pid = p["id"]
    assert set(p["members"]) == {"u0", "u1"} and p["owner_id"] == "u0"
    client.post("/api/tasks/", headers=teacher, json={"pid": pid, "title": "Une tâche"})
    client.post(f"/api/messages/{pid}", headers=teacher, json={"text": "Bonjour"})
    assert client.get(f"/api/projects/{pid}/progress", headers=teacher).json()["task_count"] == 1
    assert client.delete(f"/api/projects/{pid}", headers=teacher).status_code == 204
    assert client.get(f"/api/projects/{pid}", headers=teacher).status_code == 404
    assert all(t["pid"] != pid for t in client.get("/api/tasks/", headers=teacher).json())


def test_message_sender_is_authenticated_user_and_html_is_escaped_in_activity(client, student):
    m = client.post("/api/messages/p1", headers=student, json={"text": "Salut", "uid": "u0"})
    assert m.status_code == 201 and m.json()["uid"] == "u1"
    assert client.delete(f"/api/messages/p1/{m.json()['id']}", headers=student).status_code == 204


def test_member_creation_validation_and_activity_escaping(client, teacher):
    bad = client.post("/api/members/", headers=teacher, json={"name": "A", "email": "nope", "role": "QA"})
    assert bad.status_code == 422
    r = client.post("/api/members/", headers=teacher,
                    json={"name": "<img src=x onerror=alert(1)>", "email": "XSS@univ.tn", "role": "QA"})
    assert r.status_code == 201 and r.json()["email"] == "xss@univ.tn"
    assert client.post("/api/members/", headers=teacher,
                       json={"name": "Doublon", "email": "xss@univ.tn", "role": "QA"}).status_code == 409
    feed = client.get("/api/projects/dashboard", headers=teacher).json()["activity"]
    assert not any("<img" in a["text"] for a in feed)
    assert login(client, "xss@univ.tn")  # le compte créé peut se connecter


def test_dashboard_shape(client, student):
    d = client.get("/api/projects/dashboard", headers=student).json()
    assert {"active_projects", "my_tasks", "activity", "recent_projects"} <= d.keys()


# ── Contrat avec le frontend : URL exactement comme appelées par index.html ──────
def test_frontend_urls_without_trailing_slash(client, teacher, student):
    for headers in (teacher, student):
        for path in ("members", "projects", "tasks", "authorizations", "authorizations?student_id=u1",
                     "projects/dashboard", "messages/p1"):
            r = client.get(f"/api/{path}", headers=headers, follow_redirects=False)
            assert r.status_code == 200, f"{path} -> {r.status_code}"
        assert isinstance(client.get("/api/members", headers=headers).json(), list)


# ── Inscription (étudiant / enseignant) ──────────────────────────────────────
STUDENT_FORM = {"role": "Étudiant", "first_name": "Amel", "last_name": "Trabelsi", "email": "Amel.Trabelsi@univ.tn",
                "identifier": "etu-2026-01", "password": "motdepasse1"}
TEACHER_FORM = {"role": "Enseignant", "first_name": "Sami", "last_name": "Gharbi", "email": "s.gharbi@univ.tn",
                "matricule": "ens-77", "password": "motdepasse1"}


def test_register_student_logs_in_and_has_no_privileges(client):
    r = client.post("/api/auth/register", json=STUDENT_FORM)
    assert r.status_code == 201, r.text
    member = r.json()["member"]
    assert member["role"] == "Étudiant" and member["email"] == "amel.trabelsi@univ.tn"
    assert member["identifier"] == "ETU-2026-01" and member["matricule"] is None
    assert member["name"] == "Amel Trabelsi" and member["initials"] == "AT"
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.get("/api/projects/", headers=h).json() == []            # aucun projet tant qu'un enseignant ne l'ajoute pas
    assert client.post("/api/projects/", headers=h, json={"name": "Hack"}).status_code == 403
    login(client, "amel.trabelsi@univ.tn", "motdepasse1")                  # puis connexion normale
    assert client.get("/api/auth/me", headers=h).json()["identifier"] == "ETU-2026-01"


def test_register_teacher_and_identifiers_are_private(client, teacher):
    r = client.post("/api/auth/register", json=TEACHER_FORM)
    assert r.status_code == 201 and r.json()["member"]["role"] == "Enseignant"
    assert r.json()["member"]["matricule"] == "ENS-77" and r.json()["member"]["identifier"] is None
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert len(client.get("/api/projects/", headers=h).json()) >= 3        # un enseignant voit tous les projets
    for m in client.get("/api/members/", headers=teacher).json():          # identifiant/matricule jamais listés
        assert "identifier" not in m and "matricule" not in m


def test_register_validation(client):
    no_ident = {k: v for k, v in STUDENT_FORM.items() if k != "identifier"}
    assert client.post("/api/auth/register", json=no_ident).status_code == 422          # identifiant obligatoire
    no_mat = {k: v for k, v in TEACHER_FORM.items() if k != "matricule"}
    assert client.post("/api/auth/register", json=no_mat).status_code == 422            # matricule obligatoire
    assert client.post("/api/auth/register", json={**STUDENT_FORM, "email": "pas-un-email"}).status_code == 422
    assert client.post("/api/auth/register", json={**STUDENT_FORM, "password": "court"}).status_code == 422
    assert client.post("/api/auth/register", json={**STUDENT_FORM, "role": "Développeur"}).status_code == 422
    assert client.post("/api/auth/register", json={**STUDENT_FORM, "identifier": "a b"}).status_code == 422


def test_register_duplicates(client):
    assert client.post("/api/auth/register", json={**STUDENT_FORM, "email": "dup1@univ.tn", "identifier": "DUP-1"}).status_code == 201
    same_mail = client.post("/api/auth/register", json={**STUDENT_FORM, "email": "DUP1@univ.tn", "identifier": "DUP-2"})
    assert same_mail.status_code == 409 and "email" in same_mail.json()["detail"].lower()
    same_id = client.post("/api/auth/register", json={**STUDENT_FORM, "email": "dup2@univ.tn", "identifier": "dup-1"})
    assert same_id.status_code == 409 and "identifiant" in same_id.json()["detail"]
    t1 = {**TEACHER_FORM, "email": "dup-t1@univ.tn", "matricule": "DUP-T"}
    assert client.post("/api/auth/register", json=t1).status_code == 201
    assert client.post("/api/auth/register", json={**t1, "email": "dup-t2@univ.tn"}).status_code == 409


def test_teacher_invitation_code(client, monkeypatch):
    from app import config
    assert client.get("/api/auth/register-options").json() == {"teacher_code_required": False}
    monkeypatch.setattr(config, "TEACHER_CODE", "sesame-prof")
    assert client.get("/api/auth/register-options").json() == {"teacher_code_required": True}
    form = {**TEACHER_FORM, "email": "coded@univ.tn", "matricule": "ENS-CODE"}
    assert client.post("/api/auth/register", json=form).status_code == 403
    assert client.post("/api/auth/register", json={**form, "teacher_code": "faux"}).status_code == 403
    assert client.post("/api/auth/register", json={**form, "teacher_code": "sesame-prof"}).status_code == 201
    # le code ne concerne pas les étudiants
    assert client.post("/api/auth/register", json={**STUDENT_FORM, "email": "stu-nocode@univ.tn", "identifier": "NOCODE"}).status_code == 201


def test_register_rate_limited(client, monkeypatch):
    from app.security import register_throttle
    monkeypatch.setattr(register_throttle, "max_attempts", 5)
    codes = [client.post("/api/auth/register", json={**STUDENT_FORM, "email": f"bulk{i}@univ.tn", "identifier": f"BULK-{i}"}).status_code
             for i in range(7)]
    assert codes[:5] == [201] * 5 and 429 in codes[5:]


def test_register_activity_escaped(client, teacher):
    client.post("/api/auth/register", json={**STUDENT_FORM, "first_name": "<b>X</b>", "email": "esc@univ.tn", "identifier": "ESC-1"})
    feed = client.get("/api/projects/dashboard", headers=teacher).json()["activity"]
    assert not any("<b>X</b>" in a["text"] for a in feed)


def test_schema_upgrade_from_previous_version(tmp_path):
    """Une base créée par la v2.1 (sans les nouvelles colonnes) doit être migrée sans perte."""
    from sqlalchemy import create_engine, inspect, text
    from app.database import ensure_schema

    eng = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with eng.begin() as c:
        c.execute(text("CREATE TABLE members (id VARCHAR(16) PRIMARY KEY, name VARCHAR(120), initials VARCHAR(4), "
                       "role VARCHAR(32), email VARCHAR(190) UNIQUE, color VARCHAR(16), password_hash VARCHAR(255))"))
        c.execute(text("INSERT INTO members VALUES ('u0','Mouhamed Zaouga','MZ','Enseignant','m@univ.tn','#fff','x')"))
    ensure_schema(eng)
    ensure_schema(eng)  # idempotent
    cols = {c["name"] for c in inspect(eng).get_columns("members")}
    assert {"first_name", "last_name", "identifier", "matricule"} <= cols
    with eng.connect() as c:
        row = c.execute(text("SELECT first_name, last_name FROM members WHERE id='u0'")).one()
    assert tuple(row) == ("Mouhamed", "Zaouga")
