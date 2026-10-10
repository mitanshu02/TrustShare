import io
from datetime import datetime, timedelta, timezone


def register_and_login(client, email):
    client.post(
        "/api/auth/register",
        json={"full_name": "Owner", "email": email, "password": "Password123!"},
    )
    response = client.post(
        "/api/auth/login", json={"email": email, "password": "Password123!"}
    )
    return response.json()["access_token"]


def upload_test_file(client, token):
    response = client.post(
        "/api/files/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_expired_share_link_cannot_be_downloaded(client, db_session, unique_email):
    from app.models.share_link import ShareLink

    token = register_and_login(client, unique_email)
    file_id = upload_test_file(client, token)

    link_response = client.post(
        f"/api/files/{file_id}/links",
        headers={"Authorization": f"Bearer {token}"},
        json={"access_level": "download", "expires_in_hours": 24, "max_downloads": 5},
    )
    assert link_response.status_code == 201, link_response.text
    link_payload = link_response.json()

    # Force the link into the past directly in the DB, rather than
    # waiting 24 hours for it to actually expire.
    link = db_session.query(ShareLink).filter(ShareLink.id == link_payload["id"]).first()
    link.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    download = client.get(f"/api/share/{link_payload['token']}/download")
    assert download.status_code == 404


def test_revoked_share_link_cannot_be_downloaded(client, unique_email):
    token = register_and_login(client, unique_email)
    file_id = upload_test_file(client, token)

    link_response = client.post(
        f"/api/files/{file_id}/links",
        headers={"Authorization": f"Bearer {token}"},
        json={"access_level": "download", "expires_in_hours": 24, "max_downloads": 5},
    )
    link_payload = link_response.json()

    revoke = client.delete(
        f"/api/files/{file_id}/links/{link_payload['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert revoke.status_code == 204

    download = client.get(f"/api/share/{link_payload['token']}/download")
    assert download.status_code == 404


def test_active_share_link_can_be_downloaded(client, unique_email):
    token = register_and_login(client, unique_email)
    file_id = upload_test_file(client, token)

    link_response = client.post(
        f"/api/files/{file_id}/links",
        headers={"Authorization": f"Bearer {token}"},
        json={"access_level": "download", "expires_in_hours": 24, "max_downloads": 5},
    )
    link_payload = link_response.json()

    download = client.get(f"/api/share/{link_payload['token']}/download")
    assert download.status_code == 200
    assert download.content == b"hello world"


def test_view_only_link_rejects_download(client, unique_email):
    token = register_and_login(client, unique_email)
    file_id = upload_test_file(client, token)

    link_response = client.post(
        f"/api/files/{file_id}/links",
        headers={"Authorization": f"Bearer {token}"},
        json={"access_level": "view", "expires_in_hours": 24, "max_downloads": 5},
    )
    link_payload = link_response.json()

    download = client.get(f"/api/share/{link_payload['token']}/download")
    assert download.status_code == 403
