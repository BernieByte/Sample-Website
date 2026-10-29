"""Run an isolated end-to-end check of ByteNest's main account flows."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from backend import create_app


def require(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def main():
    with TemporaryDirectory(prefix="bytenest-verify-") as temp_dir:
        app = create_app({
            "TESTING": True,
            "DATABASE_URL": None,
            "DATABASE_PATH": str(Path(temp_dir) / "verify.sqlite3"),
            "APP_BASE_URL": "https://bytenest.example",
            "BREVO_API_KEY": "test-brevo-api-key",
            "EMAIL_FROM": "verify-sender@gmail.com",
        })
        client = app.test_client()
        sent_email = {}

        class CapturingHTTPResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        def capture_api_request(request, timeout):
            require(request.full_url == "https://api.brevo.com/v3/smtp/email", "reset email uses Brevo's HTTPS API")
            require(timeout == 15, "Brevo API request has a timeout")
            sent_email["headers"] = {key.lower(): value for key, value in request.headers.items()}
            sent_email["payload"] = json.loads(request.data.decode("utf-8"))
            return CapturingHTTPResponse()

        with patch("backend.mail.urlopen", side_effect=capture_api_request), patch(
            "backend.routes.auth.resolve_location", return_value={"source": "Unavailable"}
        ):
            home = client.get("/")
            require(home.status_code == 200 and b"ByteNest" in home.data, "home page loads")

            signup = client.post("/api/signup", json={
                "username": "verify-user",
                "email": "verify-user@example.com",
                "password": "old-password-123",
            })
            require(signup.status_code == 201, "signup succeeds")

            logout = client.post("/api/logout")
            require(logout.status_code == 200, "logout succeeds")

            login = client.post("/api/login", json={
                "username_or_email": "verify-user",
                "password": "old-password-123",
            })
            require(login.status_code == 200, "login succeeds")

            create_file = client.post("/api/files", json={"title": "Notes", "content": "hello"})
            require(create_file.status_code == 201, "file creation succeeds")
            file_id = create_file.get_json()["file"]["id"]

            list_files = client.get("/api/files")
            files = list_files.get_json()["files"]
            require(list_files.status_code == 200 and any(item["id"] == file_id for item in files), "file listing returns the created file")

            client.post("/api/logout")
            reset_request = client.post("/api/password-reset/request", json={"email": "verify-user@example.com"})
            require(reset_request.status_code == 200, "password reset request is accepted")
            require(sent_email["headers"].get("api-key") == "test-brevo-api-key", "Brevo API key is sent as an HTTP header")
            require(sent_email["payload"]["sender"]["email"] == "verify-sender@gmail.com", "reset email uses the configured sender")
            require(sent_email["payload"]["to"][0]["email"] == "verify-user@example.com", "reset email is addressed to the account")
            require(sent_email["payload"]["subject"] == "Reset your ByteNest password", "reset email has the expected subject")

            reset_link = next((line for line in sent_email["payload"]["textContent"].splitlines() if "/reset-password?token=" in line), "")
            reset_url = urlparse(reset_link)
            token_values = parse_qs(reset_url.query).get("token", [])
            require(reset_url.path == "/reset-password" and len(token_values) == 1, "reset email contains a reset link")
            token = token_values[0]

            confirm = client.post("/api/password-reset/confirm", json={
                "token": token,
                "new_password": "new-password-456",
            })
            require(confirm.status_code == 200, "reset link changes the password")

            reuse = client.post("/api/password-reset/confirm", json={
                "token": token,
                "new_password": "another-password-789",
            })
            require(reuse.status_code == 400, "reset link cannot be reused")

            old_login = client.post("/api/login", json={
                "username_or_email": "verify-user",
                "password": "old-password-123",
            })
            require(old_login.status_code == 401, "old password no longer works")

            new_login = client.post("/api/login", json={
                "username_or_email": "verify-user",
                "password": "new-password-456",
            })
            require(new_login.status_code == 200, "new password works")

            logout = client.post("/api/logout")
            require(logout.status_code == 200, "final logout succeeds")


if __name__ == "__main__":
    main()
