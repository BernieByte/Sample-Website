# ByteNest

ByteNest is a Flask app for student documents. It supports account signup and login, private files, password changes, password reset by email, and an optional admin view. The writing workspace includes rich text formatting, autosave, document search, copy, print, and HTML export.

## Run locally

Install the dependencies and start the Flask development server:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

The app listens on `http://localhost:5000` and creates a SQLite database under `data/` by default.

## Enable password reset email with Brevo

For a Render Free deployment, the app sends reset messages through Brevo's HTTPS API. Set these environment variables in Render's environment settings:

| Variable | Purpose |
| --- | --- |
| `BREVO_API_KEY` | API key from Brevo's SMTP & API settings; keep it secret |
| `EMAIL_FROM` | Sender email registered and verified in Brevo |
| `APP_BASE_URL` | Public site origin used in reset links, such as `https://your-domain.example` |
| `SECRET_KEY` | Long, random secret used to sign Flask sessions |

Keep the API key and `SECRET_KEY` private. Do not commit them to the repository. The reset link expires after 15 minutes and can be used once. Brevo requires a verified sender. Free email senders may be rewritten by Brevo, so delivery and sender appearance can be less consistent until you have a domain you control.

The app can also use SMTP for local development or providers that support SMTP:

```powershell
$env:SMTP_HOST = "smtp.your-provider.example"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "your-smtp-login"
$env:SMTP_PASSWORD = "your-smtp-password"
$env:SMTP_FROM = "verified-sender@example.com"
$env:APP_BASE_URL = "http://localhost:5000"
$env:SECRET_KEY = "replace-with-a-long-random-secret"
```

On Render Free, outbound SMTP ports 25, 465, and 587 are blocked; use the Brevo HTTPS API configuration above for the deployed app. On deployment, `APP_BASE_URL` must be the public HTTPS origin so links sent to users point back to the live site.

## Verify the app

Run:

```powershell
python verify_app.py
```

The script uses a temporary SQLite database and a captured test email, so it exercises the full reset link without sending email or changing the app's normal database. It exits with an error if a check fails.

## Optional PostgreSQL deployment

Set `DATABASE_URL` to a PostgreSQL connection URL. If it is unset, the app uses SQLite.
