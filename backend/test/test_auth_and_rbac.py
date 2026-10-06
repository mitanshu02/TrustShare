def register(client, email, password="Password123!", full_name="Test User"):
    response = client.post(
        "/api/auth/register",
        json={"full_name": full_name, "email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client, email, password="Password123!"):
    response = client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_then_login_succeeds(client, unique_email):
    register(client, unique_email)
    token = login(client, unique_email)
    assert token


def test_login_with_wrong_password_fails(client, unique_email):
    register(client, unique_email)
    response = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": "WrongPassword!"},
    )
    assert response.status_code == 401


def test_regular_user_cannot_access_admin_endpoint(client, unique_email):
    register(client, unique_email)
    token = login(client, unique_email)

    response = client.get(
        "/api/admin/security-analytics", headers=auth_headers(token)
    )
    assert response.status_code == 403


def test_admin_can_access_admin_endpoint(client, db_session, unique_email):
    from app.models.user import User

    register(client, unique_email)
    user = db_session.query(User).filter(User.email == unique_email).first()
    user.role = "admin"
    db_session.commit()

    token = login(client, unique_email)
    response = client.get(
        "/api/admin/security-analytics", headers=auth_headers(token)
    )
    assert response.status_code == 200


def test_suspicious_login_notifies_both_admin_and_the_targeted_user(
    client, db_session, unique_email
):
    from app.models.user import User

    register(client, unique_email)

    admin_email = f"admin-{unique_email}"
    register(client, admin_email)
    admin = db_session.query(User).filter(User.email == admin_email).first()
    admin.role = "admin"
    db_session.commit()

    # Five wrong-password attempts in a row should trip the detector.
    for _ in range(5):
        client.post(
            "/api/auth/login",
            json={"email": unique_email, "password": "WrongPassword!"},
        )

    user_token = login(client, unique_email)
    user_notifications = client.get(
        "/api/notifications", headers=auth_headers(user_token)
    ).json()
    assert any(
        n["notification_type"] == "security_alert" for n in user_notifications
    ), "the targeted user should be told about the failed-login burst on their own account"

    admin_token = login(client, admin_email)
    admin_notifications = client.get(
        "/api/notifications", headers=auth_headers(admin_token)
    ).json()
    assert any(
        n["notification_type"] == "security_alert" for n in admin_notifications
    ), "admins should also be told"


def test_suspicious_login_alert_is_not_duplicated_on_every_further_attempt(
    client, unique_email
):
    """
    Regression test: an earlier version of this detector re-fired a
    fresh "suspicious activity" alert on every attempt past the 5th,
    which would spam a real admin inbox during an ongoing attack.
    """
    register(client, unique_email)

    for _ in range(8):
        client.post(
            "/api/auth/login",
            json={"email": unique_email, "password": "WrongPassword!"},
        )

    token = login(client, unique_email)
    notifications = client.get("/api/notifications", headers=auth_headers(token)).json()
    security_alerts = [
        n for n in notifications if n["notification_type"] == "security_alert"
    ]
    assert len(security_alerts) == 1