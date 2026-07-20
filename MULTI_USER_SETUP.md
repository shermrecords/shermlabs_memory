# Multi-user setup

## What changed

- Users can register with an email address and password.
- Passwords are stored as Werkzeug password hashes, never plaintext.
- Transcripts/entries, notes, and topics now carry a `user_id`.
- Every protected route filters records by the logged-in user.
- Supabase Storage keys use `users/<user_id>/...`.
- The first registered account automatically claims legacy records whose `user_id` is empty.

## Render

Set a strong `SECRET_KEY` in Render. Keep the existing `DATABASE_URL`, Supabase, Together, and transcription variables.

Generate a secret locally with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Deploy using:

```text
Build command: pip install -r requirements.txt
Start command: gunicorn app:app --bind 0.0.0.0:$PORT
```

## Important migration behavior

Register your own account first after deployment. The first account claims all records created before multi-user support was added. Later accounts begin with empty private workspaces.

## Current authentication design

This version uses Flask-Login and password hashes in the application database. Supabase remains the database/file-storage platform, but Supabase Auth is not yet required. This keeps the existing server-rendered Flask app deployable without rewriting it as a token-based client application.
