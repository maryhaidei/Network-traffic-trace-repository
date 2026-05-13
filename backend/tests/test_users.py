def test_me_returns_current_user(client, admin_headers, admin_user):
    resp = client.get("/users/me", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["login"] == "admin000"
    assert data["role"] == "admin"


def test_admin_can_create_user(client, admin_headers):
    payload = {
        "login": "user0002",
        "password": "user0002",
        "last_name": "Petrov",
        "first_name": "Petr",
        "organization": "MSU",
        "email": "user2@example.com",
        "role": "user",
    }
    resp = client.post("/users", json=payload, headers=admin_headers)
    assert resp.status_code in (200, 201), resp.text
    data = resp.json()
    assert data["login"] == "user0002"
    assert data["role"] == "user"


def test_regular_user_cannot_create_user(client, user_headers):
    payload = {
        "login": "user0003",
        "password": "user0003",
        "last_name": "Sidorov",
        "first_name": "Sidr",
        "organization": "MSU",
        "email": "user3@example.com",
        "role": "user",
    }
    resp = client.post("/users", json=payload, headers=user_headers)
    assert resp.status_code == 403