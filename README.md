# ShermLabs Memory

ShermLabs Memory is a private Flask application for capturing audio, microphone recordings, pasted text, and documents; preserving the original source; and organizing AI-analyzed content into searchable topics.

## New topic knowledge system

This build adds direct many-to-many links between entries and topics.

After an entry is analyzed, Together AI now returns:

- `suggested_existing_topics`
- `suggested_new_topics`
- summary, cleaned text, tags, action items, entities, category, project, and confidence

The analysis review screen lets the user:

- accept or remove suggested existing topics
- attach any other existing topics
- create one or more new topics
- attach the same entry to several topics
- save edits or approve the analysis and topic links

Topic links are stored in the SQL database through the `entry_topics` association table. `ai_analysis_json` retains the structured AI response and approved topic names, but it is not yet a vector database or full RAG index.

## Topic access

Open `/topics` to:

- browse every topic
- search topic names
- see entry and note counts
- open a combined topic view

Each topic page includes:

- directly linked analyzed entries
- AI summaries and cleaned content
- saved notes
- search within that topic's entry and note content
- links back to each entry's analysis
- links to the read-only original transcript
- combined text export

## Source provenance

Every analyzed entry includes an **Open Original Transcript** link. The dedicated read-only route is:

```text
/transcript/<entry_id>/original
```

This preserves the distinction between:

```text
Original source → editable working copy → AI analysis
```

## Microphone recording

The Audio capture page can record directly through the browser microphone using the `MediaRecorder` API. Microphone access requires HTTPS in production or localhost during development.

## Setup

```bash
python -m venv venv
source venv/bin/activate       # macOS/Linux
# venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open `http://127.0.0.1:5000`.

## Main environment variables

```env
SECRET_KEY=
DATABASE_URL=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_BUCKET=audio
TOGETHER_API_KEY=
TOGETHER_BASE_URL=https://api.together.xyz/v1
TOGETHER_ANALYSIS_MODEL=openai/gpt-oss-20b
MAX_CONTENT_MB=100
```

## Database update

On startup, `db.create_all()` creates the new `entry_topics` table automatically. Existing transcripts, topics, and notes remain intact.

Before deploying a schema update, back up the production database. This MVP still uses lightweight compatibility migrations; Flask-Migrate/Alembic is recommended before larger production changes.

## Render

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

Health check:

```text
/health
```

## Important note about RAG

The current build stores structured analysis and topic relationships, making analyzed material accessible later. A full RAG layer would be a later addition:

```text
Entry text → chunks → embeddings → vector store → retrieval → cited answer
```

The topic system should remain the durable organizational layer even after embeddings are added.

## Version 0.8 Dashboard

This build includes a workspace-style dashboard with:

- Persistent desktop sidebar and responsive mobile header
- Global entry search and status filtering
- Total-entry, review, topic, and AI-project metrics
- Continue Working cards
- Rich recent-entry cards with summaries, source types, projects, and topics
- Recent Topics panel
- AI-derived Active Projects panel
- AI-derived Action Items panel
- Search results view using the same richer cards

The Projects panel currently groups entries using the existing `ai_project` field, so this release does not require a database migration or a new Project model.

## Version 0.9 — Entry Workspaces, Projects, and Archive

This build adds:

- A redesigned entry-detail workspace with tabbed working copy, cleaned text, AI details, and notes
- Reversible entry archiving, restoring, and archive-only permanent deletion
- Real Project database records and dedicated project workspaces
- Action-item completion tracking
- Automatic conversion of existing `ai_project` labels into Project records
- Updated sidebar navigation and responsive layouts

### Upgrading an existing installation

Back up PostgreSQL and Supabase Storage before deploying. The application runs its existing lightweight compatibility migration on startup and adds the new transcript columns automatically. The new `project` table is created through `db.create_all()`.

No manual SQL should be necessary for this MVP build. Existing entries remain intact, and existing AI project labels are linked to real projects when the dashboard is opened.
