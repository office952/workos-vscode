from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dependencies.auth import get_current_user
from routers.storage import router as storage_router
from schemas.auth import UserResponse
from services.storage import StorageService
from services.storage_key_validation import is_valid_storage_object_key, validate_storage_object_key


_INVALID_KEYS = [
    "",
    "   ",
    "/etc/passwd",
    "C:\\Windows\\win.ini",
    "C:/Windows/win.ini",
    "\\\\server\\share\\file.txt",
    "../secret.txt",
    "folder/../secret.txt",
    "..\\secret.txt",
    "file:///etc/passwd",
    "http://example.com/file.pdf",
    "https://example.com/file.pdf",
    "s3://bucket/key",
    "gs://bucket/key",
    "ftp://host/file",
    "file\u0000.pdf",
    "file\n.pdf",
    "file\r.pdf",
    "file\t.pdf",
    "./file.pdf",
    "folder/./file.pdf",
    "folder//file.pdf",
    " folder/file.pdf",
    "folder/file.pdf ",
    "%2e%2e/secret.txt",
    "..%2fsecret.txt",
    "%2e%2e%5csecret.txt",
]

_VALID_KEYS = [
    "file.pdf",
    "quote-10.pdf",
    "quote_10.pdf",
    "quotes/10/offer.pdf",
    "clients/acme/logo.png",
    "output-blocks/snapshots/quote-10.json",
    "folder name/file name.pdf",
    "Romanian-name-fara-probleme.pdf",
    "invoice.v1.final.pdf",
    "nume-client-șină.pdf",
]


def _request_as_role(
    role: str,
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
    params: dict | None = None,
):
    app = FastAPI()
    app.include_router(storage_router)

    async def _override_get_current_user():
        return UserResponse(
            id=f"user-{role}",
            email=f"{role}@workos.test",
            name=f"{role} user",
            role=role,
            last_login=None,
        )

    app.dependency_overrides[get_current_user] = _override_get_current_user

    with TestClient(app, raise_server_exceptions=False) as client:
        return client.request(method=method, url=path, json=json_body, params=params)


@pytest.fixture
def mocked_oss(monkeypatch):
    def _fake_init(self):
        self.headers = {"Authorization": "Bearer test", "Content-Type": "application/json"}

    monkeypatch.setattr(StorageService, "__init__", _fake_init)

    calls: list[dict] = []

    async def _fake_request(self, method, endpoint, params=None, payload=None):
        calls.append({"method": method, "endpoint": endpoint, "params": params, "payload": payload})

        if endpoint.endswith("/upload_url"):
            return {
                "upload_url": "https://oss.example/upload",
                "expires_at": "2099-01-01T00:00:00Z",
            }

        if endpoint.endswith("/download_url"):
            return {
                "download_url": "https://oss.example/download",
                "expires_at": "2099-01-01T00:00:00Z",
            }

        if endpoint.endswith("/metadata"):
            key = (params or {}).get("object_key", "")
            return {
                "key": key,
                "size": 123,
                "last_modified": "2099-01-01T00:00:00Z",
                "etag": "etag-test",
            }

        return {}

    monkeypatch.setattr(StorageService, "_arequest_oss_service", _fake_request)
    return calls


@pytest.mark.parametrize("invalid_key", _INVALID_KEYS)
def test_validator_rejects_invalid_object_keys(invalid_key: str):
    with pytest.raises(ValueError):
        validate_storage_object_key(invalid_key)
    assert is_valid_storage_object_key(invalid_key) is False


@pytest.mark.parametrize("valid_key", _VALID_KEYS)
def test_validator_accepts_valid_object_keys(valid_key: str):
    assert validate_storage_object_key(valid_key) == valid_key
    assert is_valid_storage_object_key(valid_key) is True


def test_upload_url_invalid_key_rejected_for_authorized_user(mocked_oss):
    response = _request_as_role(
        "manager",
        "POST",
        "/api/v1/storage/upload-url",
        json_body={"bucket_name": "valid-bucket", "object_key": "../secret.txt"},
    )
    assert response.status_code in (400, 422)
    assert "Invalid storage object key" in str(response.json())
    assert mocked_oss == []


def test_download_url_invalid_key_rejected_for_authorized_user(mocked_oss):
    response = _request_as_role(
        "manager",
        "POST",
        "/api/v1/storage/download-url",
        json_body={"bucket_name": "valid-bucket", "object_key": "file:///etc/passwd"},
    )
    assert response.status_code in (400, 422)
    assert "Invalid storage object key" in str(response.json())
    assert mocked_oss == []


def test_delete_object_invalid_key_rejected_for_authorized_user(mocked_oss):
    response = _request_as_role(
        "manager",
        "DELETE",
        "/api/v1/storage/delete-object",
        json_body={"bucket_name": "valid-bucket", "object_key": "folder/../secret.txt"},
    )
    assert response.status_code in (400, 422)
    assert "Invalid storage object key" in str(response.json())
    assert mocked_oss == []


def test_rename_object_invalid_source_rejected_for_authorized_user(mocked_oss):
    response = _request_as_role(
        "manager",
        "POST",
        "/api/v1/storage/rename-object",
        json_body={
            "bucket_name": "valid-bucket",
            "source_key": "../secret.txt",
            "target_key": "docs/ok.pdf",
            "overwrite_key": True,
        },
    )
    assert response.status_code in (400, 422)
    assert "Invalid storage object key" in str(response.json())
    assert mocked_oss == []


def test_rename_object_invalid_target_rejected_for_authorized_user(mocked_oss):
    response = _request_as_role(
        "manager",
        "POST",
        "/api/v1/storage/rename-object",
        json_body={
            "bucket_name": "valid-bucket",
            "source_key": "docs/source.pdf",
            "target_key": "folder//target.pdf",
            "overwrite_key": True,
        },
    )
    assert response.status_code in (400, 422)
    assert "Invalid storage object key" in str(response.json())
    assert mocked_oss == []


def test_get_object_info_invalid_key_rejected_for_authenticated_user(mocked_oss):
    response = _request_as_role(
        "manager",
        "GET",
        "/api/v1/storage/get-object-info",
        params={"bucket_name": "valid-bucket", "object_key": "..%2fsecret.txt"},
    )
    assert response.status_code in (400, 422), response.text
    assert "Invalid storage object key" in str(response.json())
    assert mocked_oss == []


def test_user_without_storage_permission_still_gets_403(mocked_oss):
    response = _request_as_role(
        "viewer",
        "POST",
        "/api/v1/storage/upload-url",
        json_body={"bucket_name": "valid-bucket", "object_key": "quotes/10/offer.pdf"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "permission_denied"
    assert response.json()["detail"]["permission"] == "storage.upload_url"


def test_authorized_user_with_valid_key_reaches_provider(mocked_oss):
    valid_key = "quotes/10/invoice.v1.final.pdf"
    response = _request_as_role(
        "manager",
        "POST",
        "/api/v1/storage/upload-url",
        json_body={"bucket_name": "valid-bucket", "object_key": valid_key},
    )

    assert response.status_code == 200
    assert response.json()["upload_url"] == "https://oss.example/upload"

    assert len(mocked_oss) == 1
    assert mocked_oss[0]["endpoint"].endswith("/upload_url")
    assert mocked_oss[0]["payload"]["object_key"] == valid_key
