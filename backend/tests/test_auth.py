"""Auth endpoint tests against a mongomock-backed Flask test client."""

import pytest


def test_register_logs_in(app_client):
    res = app_client.post(
        "/api/auth/register",
        json={"name": "Ada", "email": "ada@example.com", "password": "Sup3rSecret"},
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["user"]["role"] == "buyer"
    assert data["access_token"]
    assert data["refresh_token"]


def test_register_duplicate_email_conflicts(app_client):
    payload = {"name": "Ada", "email": "dup@example.com", "password": "Sup3rSecret"}
    assert app_client.post("/api/auth/register", json=payload).status_code == 201
    res = app_client.post("/api/auth/register", json=payload)
    assert res.status_code == 409
    assert res.get_json()["error"]["code"] == "conflict"


def test_register_rejects_weak_password(app_client):
    res = app_client.post(
        "/api/auth/register", json={"name": "Ada", "email": "weak@example.com", "password": "short"}
    )
    assert res.status_code == 422


def test_login_and_me(app_client):
    app_client.post(
        "/api/auth/register",
        json={"name": "Ada", "email": "login@example.com", "password": "Sup3rSecret"},
    )
    res = app_client.post(
        "/api/auth/login", json={"email": "login@example.com", "password": "Sup3rSecret"}
    )
    assert res.status_code == 200
    token = res.get_json()["access_token"]

    me = app_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.get_json()["user"]["email"] == "login@example.com"


def test_login_wrong_password_is_401(app_client):
    app_client.post(
        "/api/auth/register",
        json={"name": "Ada", "email": "badpw@example.com", "password": "Sup3rSecret"},
    )
    res = app_client.post(
        "/api/auth/login", json={"email": "badpw@example.com", "password": "wrong-pass"}
    )
    assert res.status_code == 401


def test_me_without_token_is_401(app_client):
    assert app_client.get("/api/auth/me").status_code == 401


def test_health_ok(app_client):
    assert app_client.get("/api/health").status_code == 200