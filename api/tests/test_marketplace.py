"""Marketplace API smoke tests: health, listing lifecycle, RBAC and orders."""


def _sample_listing():
    return {
        "title": "Fresh Watermelon",
        "description": "Sweet and ripe",
        "category": "fruits",
        "price": 2500,
        "unit": "crate",
        "quantity": 40,
        "location": {"city": "Kumasi"},
        "images": [],
    }


def test_health(client):
    assert client.get("/api/health").status_code == 200


def test_categories_seeded_on_boot(client):
    res = client.get("/api/v1/categories")
    assert res.status_code == 200
    slugs = {c["slug"] for c in res.json()["items"]}
    assert "fruits" in slugs and "vegetables" in slugs


def test_seller_can_create_and_public_can_read(client, seller):
    _user, headers = seller
    created = client.post("/api/v1/listings", json=_sample_listing(), headers=headers)
    assert created.status_code == 201
    listing_id = created.json()["id"]

    listing = client.get("/api/v1/listings").json()
    assert listing["total"] == 1
    assert listing["items"][0]["title"] == "Fresh Watermelon"

    detail = client.get(f"/api/v1/listings/{listing_id}")
    assert detail.status_code == 200
    assert detail.json()["seller"]["role"] == "seller"


def test_buyer_cannot_create_listing(client, buyer):
    _user, headers = buyer
    res = client.post("/api/v1/listings", json=_sample_listing(), headers=headers)
    assert res.status_code == 403


def test_create_listing_requires_auth(client):
    assert client.post("/api/v1/listings", json=_sample_listing()).status_code == 401


def test_listing_requires_valid_category(client, seller):
    _user, headers = seller
    payload = {**_sample_listing(), "category": "unicorns"}
    res = client.post("/api/v1/listings", json=payload, headers=headers)
    assert res.status_code == 422


def test_order_and_transition_flow(client, seller, buyer):
    _su, seller_headers = seller
    _bu, buyer_headers = buyer
    listing_id = client.post("/api/v1/listings", json=_sample_listing(), headers=seller_headers).json()["id"]

    order = client.post(
        "/api/v1/orders", json={"listing_id": listing_id, "quantity": 2}, headers=buyer_headers
    )
    assert order.status_code == 201
    order_id = order.json()["id"]
    assert order.json()["total"] == 5000

    accepted = client.patch(
        f"/api/v1/orders/{order_id}", json={"action": "accept"}, headers=seller_headers
    )
    assert accepted.json()["status"] == "accepted"

    fulfilled = client.patch(
        f"/api/v1/orders/{order_id}", json={"action": "fulfill"}, headers=seller_headers
    )
    assert fulfilled.json()["status"] == "fulfilled"

    completed = client.patch(
        f"/api/v1/orders/{order_id}", json={"action": "complete"}, headers=buyer_headers
    )
    assert completed.json()["status"] == "completed"

    review = client.post(
        "/api/v1/reviews",
        json={"listing_id": listing_id, "rating": 5, "comment": "Great produce"},
        headers=buyer_headers,
    )
    assert review.status_code == 201


def test_buyer_cannot_order_own_listing_via_seller(client, seller):
    _u, headers = seller
    listing_id = client.post("/api/v1/listings", json=_sample_listing(), headers=headers).json()["id"]
    res = client.post("/api/v1/orders", json={"listing_id": listing_id, "quantity": 1}, headers=headers)
    assert res.status_code == 422


def test_notifications_require_auth(client):
    assert client.get("/api/v1/notifications").status_code == 401