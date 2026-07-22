# ShermLabs Memory

<<<<<<< HEAD
**ShermLabs Memory** is a private, AI-assisted knowledge capture system for recording, transcribing, organizing, reviewing, and retrieving personal information.

The application accepts voice recordings, uploaded audio, pasted text, and documents. Each entry is preserved in its original form, then can be cleaned, summarized, categorized, tagged, connected to projects, and converted into reusable notes.

> **ShermLabs Memory does not replace your memory—it extends it.**

ShermLabs Memory is a private Flask application for capturing audio, microphone recordings, pasted text, and documents; preserving the original source; and organizing AI-analyzed content into searchable topics.
>>>>>>> db0ea5c (working on topics stuff)

## New topic knowledge system

<<<<<<< HEAD
## Current Features

### Universal capture

Create a memory from:

- A live microphone recording
- An uploaded audio file
- Pasted text
- A `.txt`, `.md`, `.docx`, or `.pdf` document

### Browser microphone recording

The Audio capture page includes a built-in recorder that:

1. Requests microphone permission
2. Records directly in the browser
3. Shows a live timer
4. Allows playback before submission
5. Allows the recording to be discarded and restarted
6. Uploads the recording through the existing capture workflow

Microphone access requires either:

- `https://` in production
- `http://localhost` during local development

### Speech-to-text

Audio recordings are transcribed before being stored as searchable text.

The current project can be configured to use either:

- **Together AI Whisper** for cloud transcription
- **Local Whisper** for offline or local transcription

For the hosted Render deployment, Together AI is generally the lighter option because loading Whisper inside the web service requires more memory and processing time.

### AI organization

Entries can be analyzed with Together AI to generate:

- Cleaned text
- A concise summary
- Category
- Likely project
- Tags
- Action items
- Named entities
- Confidence score

AI output is stored separately from the original source. The user can edit, approve, or reject the analysis.

### Multi-user accounts

The application includes:

- Registration
- Login and logout
- Secure password hashing
- User-owned entries
- User-owned notes and topics
- Protected routes
- Separate Supabase Storage paths for each user

Stored files use paths such as:

```text
users/<user_id>/audio/
users/<user_id>/documents/
```

### Knowledge organization

Users can:

- Search entries
- Filter by review status
- Edit working transcripts
- Create notes from entries
- Assign notes to topics
- Export topic collections
- Delete entries
- Preserve the original source separately from edits

---

## Technology Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- PostgreSQL or SQLite
- Supabase Postgres
- Supabase Storage
- Together AI
- Whisper
- HTML, CSS, and JavaScript
- Browser `MediaRecorder` API
- Gunicorn
- Render
- GitHub Pages for the public landing page

---

## Project Structure

```text
shermlabs_memory/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── MULTI_USER_SETUP.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── topic.html
│   ├── transcript.html
│   └── upload.html
├── static/
│   ├── app.js
│   └── style.css
├── uploads/
└── exports/
```

The `uploads/` and `exports/` directories are created automatically when the application starts.

---

## Local Installation

### 1. Clone the repository

```bash
git clone https://github.com/shermrecords/shermlabs_memory.git
cd shermlabs_memory
```

### 2. Create a virtual environment

#### macOS or Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows PowerShell

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

#### Windows Command Prompt

```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

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
>>>>>>> db0ea5c (working on topics stuff)

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

<<<<<<< HEAD
Local Whisper also requires FFmpeg.

#### macOS

```bash
brew install ffmpeg
```

#### Windows

Install FFmpeg and make sure `ffmpeg` is available on your system `PATH`.

### 4. Create the environment file

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

On Windows:

```cmd
copy .env.example .env
```

Then edit `.env`.

---

## Environment Variables

A typical configuration looks like this:

```env
SECRET_KEY=replace-with-a-long-random-value

DATABASE_URL=

SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_BUCKET=audio

TOGETHER_API_KEY=
TOGETHER_BASE_URL=https://api.together.xyz/v1
TOGETHER_TRANSCRIPTION_MODEL=openai/whisper-large-v3
TOGETHER_ANALYSIS_MODEL=openai/gpt-oss-20b

MAX_CONTENT_MB=100
```

### `SECRET_KEY`

Used to secure Flask sessions.

Generate one with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### `DATABASE_URL`

When blank, the application uses a local SQLite database:

```text
transcriber.db
```

For Supabase or Render PostgreSQL, use the provided connection string.

The application automatically converts:

```text
postgres://
```

to:

```text
postgresql://
```

when needed by SQLAlchemy.

### Supabase variables

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_BUCKET=audio
```

These enable cloud file storage. Never expose the service-role key in browser JavaScript or commit it to GitHub.

### Together variables

```env
TOGETHER_API_KEY=
TOGETHER_BASE_URL=https://api.together.xyz/v1
TOGETHER_TRANSCRIPTION_MODEL=openai/whisper-large-v3
TOGETHER_ANALYSIS_MODEL=openai/gpt-oss-20b
```

The transcription model processes audio. The analysis model organizes the resulting text.

### Upload limit

```env
MAX_CONTENT_MB=100
```

This controls Flask's maximum request size.

---

## Running Locally

Start the Flask application:

Start command:
>>>>>>> db0ea5c (working on topics stuff)

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

<<<<<<< HEAD
Then open:

```text
http://127.0.0.1:5000
```

The browser microphone recorder works on localhost.

You can also initialize the database manually:

```bash
flask --app app init-db
```

---

## Capture Workflow

### Microphone recording

```text
Open Capture
→ Select Audio
→ Start Recording
→ Allow microphone access
→ Speak
→ Stop
→ Preview
→ Create Entry
→ Transcribe
→ Review
→ Analyze with AI
```

### Uploaded audio

```text
Choose audio file
→ Upload original
→ Transcribe
→ Save searchable transcript
→ Analyze
→ Review AI output
```

### Pasted text

```text
Paste text
→ Save original
→ Analyze
→ Approve or edit results
```

### Document upload

```text
Upload document
→ Extract text
→ Save original
→ Analyze
→ Organize into notes and topics
```

---

## Microphone Compatibility

The recorder uses the browser's `MediaRecorder` API.

Expected support is strongest in current versions of:

- Chrome
- Edge
- Firefox
- Safari

The exact recording format depends on the browser. Common outputs include:

- `.webm`
- `.m4a`
- `.mp4`
- `.ogg`

The application accepts these formats.

On mobile devices, microphone recording must be opened from a secure HTTPS page. Render supplies HTTPS automatically.

---

## Database and Legacy Data

The application creates required tables on startup and includes compatibility helpers for older databases.

When upgrading from the earlier single-user version:

- The first registered account can claim legacy entries
- Existing entries are assigned to that first user
- New entries are associated with the currently logged-in user

Back up the database before deploying major schema changes.

For a production system, Flask-Migrate/Alembic should eventually replace automatic compatibility migrations.

---

## Supabase Storage

When Supabase is configured, source files are stored remotely.

Recommended bucket:

```text
audio
```

Example object paths:

```text
users/1/audio/20260720_recording.webm
users/1/documents/research_notes.pdf
```

The bucket should remain private. The server accesses it using the service-role key.

When Supabase is not configured, uploads are stored locally in:

```text
uploads/
```

Local files on Render's standard filesystem are not guaranteed to persist across deployments, so Supabase Storage is recommended for production.

---

## Deploying the Flask App to Render

### Build command

```bash
pip install -r requirements.txt
```

### Start command

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

### Required Render environment variables

At minimum:

```text
SECRET_KEY
DATABASE_URL
TOGETHER_API_KEY
TOGETHER_TRANSCRIPTION_MODEL
TOGETHER_ANALYSIS_MODEL
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_BUCKET
```

After saving the variables, redeploy the service.

### Health check

The application includes:

```text
/health
```

This can be used as the Render health-check path.

---

## Hosting the Landing Page

The public ShermLabs Memory landing page can be hosted separately on GitHub Pages.

Recommended setup:

```text
Custom domain
→ GitHub Pages landing page
→ Launch App button
→ Render Flask application
```

A suitable landing-page repository name is:

```text
shermlabs-memory-site
```

The landing page can use a custom domain such as:

```text
memory.shermlabs.com
```

Contact:

```text
sherm@shermlabs.com
```

The application itself remains on Render because GitHub Pages only hosts static files and cannot run Flask.

---

## Security Notes

- Never commit `.env`
- Never expose `SUPABASE_SERVICE_ROLE_KEY`
- Never expose `TOGETHER_API_KEY`
- Use a long random `SECRET_KEY`
- Use HTTPS in production
- Keep the Supabase bucket private
- Use strong passwords
- Back up the production database
- Do not use Flask's development server in production
- Review privacy and consent requirements before storing sensitive or clinical information

This project is not currently presented as a HIPAA-compliant medical records platform. Sensitive health information should not be stored until the hosting, access-control, logging, encryption, retention, and vendor agreements have been evaluated for the intended use.

---

## Troubleshooting

### Microphone button does not work

Confirm that:

- The page is served over HTTPS or localhost
- Microphone permission was granted
- No other application is exclusively using the microphone
- The browser supports `MediaRecorder`
- The selected microphone is enabled in operating-system settings

### Recording completes but no file is submitted

Confirm that `static/app.js` is loading and that the recorded Blob is attached to the form's audio field before submission.

Use the browser developer console to check for JavaScript errors.

### `transcribe_audio() takes 1 positional argument but 2 were given`

The function call and definition do not match.

Either call:

```python
transcribe_audio(local_path)
```

or allow an optional model argument:

```python
def transcribe_audio(local_path, selected_model=None):
    ...
```

### FFmpeg error

Install FFmpeg and restart the terminal or Render service.

### Together key error

Confirm:

```env
TOGETHER_API_KEY=your_actual_key
```

Do not place quotes around the value in Render.

### Empty transcription

Try a short, clearly audible recording first. Confirm the file type is supported and that the recording contains an audio track.

### Render reports `gunicorn: command not found`

Confirm `requirements.txt` contains:

```text
gunicorn
```

Then redeploy.

### Database column errors

Restart the app so compatibility migrations can run. For production upgrades, inspect the database and migrate carefully rather than repeatedly modifying tables by hand.

---

## Roadmap

Planned features include:

- Automatic analysis immediately after transcription
- Background processing for long recordings
- Progress indicators for upload, transcription, and analysis
- Silence detection and automatic recording stop
- Pause and resume recording
- Audio waveform display
- Knowledge graph connections
- Project dashboards
- Timeline view
- Conversational search across all memories
- Related-memory suggestions
- Mobile-first capture experience
- Local Ollama analysis
- Provider switching for transcription and language models
- User account recovery and email verification
- Administrative tools
- Export and backup utilities

---

## Product Vision

ShermLabs Memory is intended to become a durable personal knowledge system.

The long-term workflow is simple:

```text
Capture a thought
→ Preserve the source
→ Transcribe or extract
→ Organize with AI
→ Review
→ Connect it to prior knowledge
→ Retrieve it later through search or conversation
```

The goal is not merely to store files. The goal is to convert scattered recordings, notes, documents, and ideas into an evolving body of useful, connected memory.

---

## Contact

Questions, feedback, or early-access inquiries:

**sherm@shermlabs.com**

---

## License

No open-source license has been selected yet. Unless a license file is added, all rights are reserved by the project owner.

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
>>>>>>> db0ea5c (working on topics stuff)
