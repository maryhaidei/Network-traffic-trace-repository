def test_login_success(client, admin_user):
    resp = client.post("/auth/login", json={"login": "admin000", "password": "admin000"})
    if resp.status_code == 422:
        resp = client.post("/auth/login", data={"login": "admin000", "password": "admin000"})

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data or "token" in data


def test_login_wrong_password(client, admin_user):
    resp = client.post("/auth/login", json={"login": "admin000", "password": "wrongpass"})
    if resp.status_code == 422:
        resp = client.post("/auth/login", data={"login": "admin000", "password": "wrongpass"})

    assert resp.status_code in (400, 401)