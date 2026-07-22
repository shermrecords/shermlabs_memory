import os
import re
import json
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from sqlalchemy import inspect, text
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash


load_dotenv(override=True)



try:
    from supabase import create_client
except Exception:
    create_client = None


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
EXPORT_DIR = BASE_DIR / "exports"
UPLOAD_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".webm", ".mp4"}
ALLOWED_DOCUMENT_EXTENSIONS = {".txt", ".md", ".docx", ".pdf"}


def normalize_database_url(url: str | None) -> str:
    """
    Supabase/Render usually provide postgres:// URLs.
    SQLAlchemy wants postgresql://.
    """
    if not url:
        return f"sqlite:///{BASE_DIR / 'transcriber.db'}"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = normalize_database_url(os.getenv("DATABASE_URL"))
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_MB", "100")) * 1024 * 1024

OPENAI_TRANSCRIBE_MODELS = [
    "whisper-1",
    "gpt-4o-mini-transcribe",
    "gpt-4o-transcribe",
]
DEFAULT_OPENAI_TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")
OPENAI_ANALYSIS_MODEL = os.getenv("OPENAI_ANALYSIS_MODEL", "gpt-4.1-mini")

if DEFAULT_OPENAI_TRANSCRIBE_MODEL not in OPENAI_TRANSCRIBE_MODELS:
    DEFAULT_OPENAI_TRANSCRIBE_MODEL = "whisper-1"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "audio")

LOCAL_WHISPER_MODELS = ["tiny", "base", "small", "medium"]
DEFAULT_LOCAL_WHISPER_MODEL = "base"

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to continue."


# ---------------------------
# Models
# ---------------------------


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


note_topics = db.Table(
    "note_topics",
    db.Column("note_id", db.Integer, db.ForeignKey("note.id"), primary_key=True),
    db.Column("topic_id", db.Integer, db.ForeignKey("topic.id"), primary_key=True),
)

entry_topics = db.Table(
    "entry_topics",
    db.Column("entry_id", db.Integer, db.ForeignKey("transcript.id"), primary_key=True),
    db.Column("topic_id", db.Integer, db.ForeignKey("topic.id"), primary_key=True),
)


class Transcript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.Text, nullable=True)
    storage_key = db.Column(db.Text, nullable=True)
    original_filename = db.Column(db.String(255), nullable=True)
    input_type = db.Column(db.String(30), nullable=False, default="audio")
    source_title = db.Column(db.String(255), nullable=True)
    source_mimetype = db.Column(db.String(120), nullable=True)

    recording_date = db.Column(db.String(20), nullable=True)
    weekday = db.Column(db.String(30), nullable=True)
    recording_time = db.Column(db.String(30), nullable=True)

    transcript_original = db.Column(db.Text, nullable=False, default="")
    transcript_working = db.Column(db.Text, nullable=False, default="")
    review_status = db.Column(db.String(30), nullable=False, default="unread")

    cleaned_text = db.Column(db.Text, nullable=True)
    ai_summary = db.Column(db.Text, nullable=True)
    ai_category = db.Column(db.String(120), nullable=True)
    ai_project = db.Column(db.String(255), nullable=True)
    ai_tags = db.Column(db.Text, nullable=True)
    ai_action_items = db.Column(db.Text, nullable=True)
    ai_entities = db.Column(db.Text, nullable=True)
    ai_confidence = db.Column(db.Float, nullable=True)
    ai_analysis_json = db.Column(db.Text, nullable=True)
    processing_status = db.Column(db.String(40), nullable=False, default="not_analyzed")
    ai_review_status = db.Column(db.String(40), nullable=False, default="pending")
    processing_error = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    notes = db.relationship("Note", backref="source_transcript", lazy=True)
    topics = db.relationship("Topic", secondary=entry_topics, back_populates="entries")


class Topic(db.Model):
    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_topic_user_name"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    notes = db.relationship("Note", secondary=note_topics, back_populates="topics")
    entries = db.relationship("Transcript", secondary=entry_topics, back_populates="topics")


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    source_transcript_id = db.Column(db.Integer, db.ForeignKey("transcript.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    topics = db.relationship("Topic", secondary=note_topics, back_populates="notes")


# ---------------------------
# Helpers
# ---------------------------

def safe_filename(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"[^\w\-]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_") or "untitled"


def allowed_audio(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_AUDIO_EXTENSIONS


def allowed_document(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_DOCUMENT_EXTENSIONS


def parse_recorder_filename(filename: str) -> dict:
    """
    Example:
    Friday, 6h18m pm.m4a
    """
    stem = Path(filename).stem.strip()
    pattern = (
        r"^(?P<weekday>[A-Za-z]+),\s*"
        r"(?P<hour>\d{1,2})h"
        r"(?P<minute>\d{1,2})m\s*"
        r"(?P<ampm>am|pm|AM|PM)$"
    )
    match = re.match(pattern, stem)

    if not match:
        return {"weekday": "", "time_display": "", "time_slug": ""}

    weekday = match.group("weekday").title()
    hour = match.group("hour")
    minute = match.group("minute").zfill(2)
    ampm = match.group("ampm").upper()

    return {
        "weekday": weekday,
        "time_display": f"{hour}:{minute} {ampm}",
        "time_slug": f"{hour}-{minute}_{ampm}",
    }


def make_transcript_title(recording_date: str, weekday: str, time_slug: str, original_filename: str) -> str:
    parts = []
    if recording_date:
        parts.append(recording_date)
    if weekday:
        parts.append(weekday)
    if time_slug:
        parts.append(time_slug)

    if not parts:
        parts.append(Path(original_filename).stem or "untitled_recording")

    return safe_filename("_".join(parts) + "_transcript")


def get_or_create_topic(name: str) -> Topic:
    normalized = (name or "").strip()
    if not normalized:
        raise ValueError("Topic name cannot be empty.")

    existing = Topic.query.filter(Topic.user_id == current_user.id, db.func.lower(Topic.name) == normalized.lower()).first()
    if existing:
        return existing

    topic = Topic(name=normalized, user_id=current_user.id)
    db.session.add(topic)
    db.session.commit()
    return topic


def get_supabase_client():
    if not (create_client and SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY):
        return None
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def save_uploaded_file(file_storage, folder: str = "uploads"):
    """Save an uploaded source locally and, when configured, in Supabase Storage."""

    original_name = secure_filename(file_storage.filename) or "upload"
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    local_name = f"{timestamp}_{uuid4().hex[:8]}_{original_name}"

    local_path = UPLOAD_DIR / local_name
    file_storage.save(local_path)

    storage_key = None
    supabase = get_supabase_client()

    if supabase:
        try:
            storage_key = f"users/{current_user.id}/{folder}/{local_name}"

            with open(local_path, "rb") as f:
                supabase.storage.from_(SUPABASE_BUCKET).upload(
                    path=storage_key,
                    file=f,
                    file_options={
                        "content-type": file_storage.mimetype or "application/octet-stream",
                        "upsert": "true",
                    },
                )

            print(f"Uploaded to Supabase Storage: {storage_key}")

        except Exception as exc:
            print("SUPABASE STORAGE UPLOAD FAILED:")
            print(exc)

            # Keep app alive even if cloud upload fails
            storage_key = None

    return str(local_path), storage_key


def save_audio_file(file_storage):
    return save_uploaded_file(file_storage, folder="audio")


def extract_document_text(local_path: str) -> str:
    path = Path(local_path)
    suffix = path.suffix.lower()

    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace").strip()

    if suffix == ".docx":
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("DOCX support requires python-docx.") from exc
        doc = Document(path)
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF support requires pypdf.") from exc
        reader = PdfReader(str(path))
        return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()

    raise ValueError("Unsupported document type.")


def transcribe_audio(local_path: str, model_name: str = "base") -> str:
    import whisper

    model = whisper.load_model(model_name)

    result = model.transcribe(local_path)

    return result["text"].strip()



def _json_text(value) -> str:
    return json.dumps(value or [], ensure_ascii=False, indent=2)


def _parse_json_text(value, default=None):
    if default is None:
        default = []
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def analyze_entry_text(source_text: str, title: str = "", existing_topics=None) -> dict:
    """Analyze one entry and suggest existing and new topics."""
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise RuntimeError("TOGETHER_API_KEY is not configured.")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from exc

    existing_topics = existing_topics or []
    topic_list = "\n".join(f"- {name}" for name in existing_topics) or "(none yet)"
    instructions = """You organize personal voice memos, pasted text, and documents into a knowledge system.
Return only valid JSON with these keys: cleaned_text, summary, category, project, tags, action_items, entities, confidence, suggested_existing_topics, suggested_new_topics.
Do not invent facts. Preserve meaning and uncertainty. cleaned_text may fix punctuation, filler words, and obvious transcription errors, but must not add claims or remove meaningful details.
summary should be concise but useful. category should be a stable broad label such as idea, project_note, research, journal, meeting, task_list, music, software, or reference.
project should name the most likely project, or be an empty string when unclear. Tags should be specific. Action items must only include explicit or strongly implied next actions.
Entities is an array of objects with name and type. Confidence is a number from 0 to 1.
For topics, reuse existing topics whenever they fit. suggested_existing_topics must contain exact names from the supplied existing-topic list. suggested_new_topics should contain at most 3 genuinely useful new topic names and should avoid near-duplicates, overly narrow labels, and one-off keywords."""

    client = OpenAI(api_key=api_key, base_url=os.getenv("TOGETHER_BASE_URL", "https://api.together.xyz/v1"))
    response = client.chat.completions.create(
        model=os.getenv("TOGETHER_ANALYSIS_MODEL", "openai/gpt-oss-20b"),
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": f"Existing topics:\n{topic_list}\n\nTitle: {title or '(untitled)'}\n\nSource text:\n{source_text}"},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    if not raw:
        raise RuntimeError("Together returned an empty response.")
    try:
        analysis = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Together returned invalid JSON: {raw[:500]}") from exc
    required = {"cleaned_text", "summary", "category", "project", "tags", "action_items", "entities", "confidence", "suggested_existing_topics", "suggested_new_topics"}
    missing = required - set(analysis)
    if missing:
        raise RuntimeError(f"Together response is missing fields: {', '.join(sorted(missing))}")
    return analysis


def topic_master_text(topic: Topic) -> str:
    lines = [f"Topic: {topic.name}", f"Exported: {datetime.utcnow().isoformat(timespec='seconds')} UTC", "=" * 70, ""]
    entries = (Transcript.query.join(entry_topics).filter(entry_topics.c.topic_id == topic.id, Transcript.user_id == current_user.id).order_by(Transcript.created_at.asc()).all())
    for entry in entries:
        lines.extend([f"Entry: {entry.filename}", f"Created: {entry.created_at.isoformat(timespec='seconds')} UTC", f"Summary: {entry.ai_summary or '(no summary)'}", "Original transcript:", entry.transcript_original or "(empty)", ""])
    notes = (Note.query.join(note_topics).filter(note_topics.c.topic_id == topic.id, Note.user_id == current_user.id).order_by(Note.created_at.asc()).all())
    for note in notes:
        lines.extend([f"Note: {note.title}", f"Created: {note.created_at.isoformat(timespec='seconds')} UTC", "-" * 70, note.body, ""])
    return "\n".join(lines)


def ensure_transcript_columns():
    """Tiny compatibility migration for existing MVP databases."""
    inspector = inspect(db.engine)
    if "transcript" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("transcript")}
    statements = {
        "user_id": "ALTER TABLE transcript ADD COLUMN user_id INTEGER",
        "input_type": "ALTER TABLE transcript ADD COLUMN input_type VARCHAR(30) DEFAULT 'audio' NOT NULL",
        "source_title": "ALTER TABLE transcript ADD COLUMN source_title VARCHAR(255)",
        "source_mimetype": "ALTER TABLE transcript ADD COLUMN source_mimetype VARCHAR(120)",
        "cleaned_text": "ALTER TABLE transcript ADD COLUMN cleaned_text TEXT",
        "ai_summary": "ALTER TABLE transcript ADD COLUMN ai_summary TEXT",
        "ai_category": "ALTER TABLE transcript ADD COLUMN ai_category VARCHAR(120)",
        "ai_project": "ALTER TABLE transcript ADD COLUMN ai_project VARCHAR(255)",
        "ai_tags": "ALTER TABLE transcript ADD COLUMN ai_tags TEXT",
        "ai_action_items": "ALTER TABLE transcript ADD COLUMN ai_action_items TEXT",
        "ai_entities": "ALTER TABLE transcript ADD COLUMN ai_entities TEXT",
        "ai_confidence": "ALTER TABLE transcript ADD COLUMN ai_confidence FLOAT",
        "ai_analysis_json": "ALTER TABLE transcript ADD COLUMN ai_analysis_json TEXT",
        "processing_status": "ALTER TABLE transcript ADD COLUMN processing_status VARCHAR(40) DEFAULT 'not_analyzed' NOT NULL",
        "ai_review_status": "ALTER TABLE transcript ADD COLUMN ai_review_status VARCHAR(40) DEFAULT 'pending' NOT NULL",
        "processing_error": "ALTER TABLE transcript ADD COLUMN processing_error TEXT",
    }
    for column, statement in statements.items():
        if column not in existing:
            db.session.execute(text(statement))
    db.session.commit()


def ensure_owner_columns():
    """Add ownership columns to legacy MVP tables without deleting existing data."""
    inspector = inspect(db.engine)
    table_statements = {
        "topic": "ALTER TABLE topic ADD COLUMN user_id INTEGER",
        "note": "ALTER TABLE note ADD COLUMN user_id INTEGER",
    }
    for table_name, statement in table_statements.items():
        if table_name in inspector.get_table_names():
            columns = {c["name"] for c in inspector.get_columns(table_name)}
            if "user_id" not in columns:
                db.session.execute(text(statement))
    db.session.commit()


def claim_legacy_data(user_id: int) -> None:
    """Assign pre-account records to the first registered user."""
    Transcript.query.filter(Transcript.user_id.is_(None)).update({Transcript.user_id: user_id})
    Topic.query.filter(Topic.user_id.is_(None)).update({Topic.user_id: user_id})
    Note.query.filter(Note.user_id.is_(None)).update({Note.user_id: user_id})
    db.session.commit()


def owned_transcript_or_404(transcript_id: int):
    return Transcript.query.filter_by(id=transcript_id, user_id=current_user.id).first_or_404()


def owned_topic_or_404(topic_id: int):
    return Topic.query.filter_by(id=topic_id, user_id=current_user.id).first_or_404()


# ---------------------------
# Routes
# ---------------------------

@app.cli.command("init-db")
def init_db_command():
    db.create_all()
    print("Database initialized.")


@app.before_request
def ensure_tables():
    # Fine for MVP. Later migrations can replace this.
    db.create_all()
    ensure_transcript_columns()
    ensure_owner_columns()


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not email or "@" not in email:
            flash("Enter a valid email address.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            is_first_user = User.query.count() == 0
            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            if is_first_user:
                claim_legacy_data(user.id)
            login_user(user)
            flash("Account created.", "success")
            return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=request.form.get("remember") == "on")
            return redirect(request.args.get("next") or url_for("index"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()

    query = Transcript.query.filter(Transcript.user_id == current_user.id)

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Transcript.filename.ilike(like),
                Transcript.original_filename.ilike(like),
                Transcript.transcript_original.ilike(like),
                Transcript.transcript_working.ilike(like),
                Transcript.cleaned_text.ilike(like),
                Transcript.ai_summary.ilike(like),
                Transcript.ai_tags.ilike(like),
                Transcript.ai_project.ilike(like),
            )
        )

    if status:
        query = query.filter(Transcript.review_status == status)

    transcripts = query.order_by(
        db.case(
            (Transcript.review_status == "unread", 1),
            (Transcript.review_status == "in_progress", 2),
            (Transcript.review_status == "complete", 3),
            else_=4,
        ),
        Transcript.created_at.desc(),
    ).all()

    topics = Topic.query.filter_by(user_id=current_user.id).order_by(Topic.name.asc()).all()

    return render_template(
        "index.html",
        transcripts=transcripts,
        topics=topics,
        q=q,
        status=status,
    )
@app.route("/topic/<int:topic_id>/delete", methods=["POST"])
@login_required
def delete_topic(topic_id):
    topic = owned_topic_or_404(topic_id)

    # This deletes the topic link, but does NOT delete the notes themselves.
    topic.notes.clear()
    topic.entries.clear()

    db.session.delete(topic)
    db.session.commit()

    flash(f"Deleted topic: {topic.name}", "success")
    return redirect(url_for("topics_index"))


@app.route("/upload", methods=["GET", "POST"])
@app.route("/capture", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        input_type = request.form.get("input_type", "audio").strip()
        title_override = request.form.get("title", "").strip()
        recording_date = request.form.get("recording_date", "").strip()
        transcript_text = ""
        local_path = None
        storage_key = None
        original_filename = None
        source_mimetype = None
        weekday = ""
        recording_time = ""

        if input_type == "text":
            transcript_text = request.form.get("pasted_text", "").strip()
            if not transcript_text:
                flash("Paste some text before saving.", "error")
                return redirect(url_for("upload", type="text"))
            title = safe_filename(title_override or f"text_{datetime.now().strftime('%Y-%m-%d_%H-%M')}")

        elif input_type == "document":
            document = request.files.get("document")
            if not document or not document.filename:
                flash("Choose a document.", "error")
                return redirect(url_for("upload", type="document"))
            if not allowed_document(document.filename):
                flash("Supported documents: TXT, Markdown, DOCX, and PDF.", "error")
                return redirect(url_for("upload", type="document"))
            original_filename = document.filename
            source_mimetype = document.mimetype
            local_path, storage_key = save_uploaded_file(document, folder="documents")
            try:
                transcript_text = extract_document_text(local_path)
            except Exception as exc:
                flash(f"Document saved, but text extraction failed: {exc}", "error")
            title = safe_filename(title_override or Path(document.filename).stem)

        else:
            input_type = "audio"
            audio = request.files.get("audio")
            should_transcribe = request.form.get("transcribe") == "on"
            manual_transcript = request.form.get("manual_transcript", "").strip()
            selected_model = request.form.get("transcribe_model", DEFAULT_LOCAL_WHISPER_MODEL)
            if selected_model not in LOCAL_WHISPER_MODELS:
                selected_model = DEFAULT_LOCAL_WHISPER_MODEL
            if not audio or not audio.filename:
                flash("Choose an audio file.", "error")
                return redirect(url_for("upload", type="audio"))
            if not allowed_audio(audio.filename):
                flash("Unsupported audio type.", "error")
                return redirect(url_for("upload", type="audio"))

            original_filename = audio.filename
            source_mimetype = audio.mimetype
            parsed = parse_recorder_filename(audio.filename)
            weekday = parsed["weekday"]
            recording_time = parsed["time_display"]
            title = safe_filename(title_override) if title_override else make_transcript_title(
                recording_date, weekday, parsed["time_slug"], audio.filename
            )
            local_path, storage_key = save_audio_file(audio)
            transcript_text = manual_transcript
            if should_transcribe and not transcript_text:
                try:
                    transcript_text = transcribe_audio(local_path, selected_model)
                except Exception as exc:
                    flash(f"Uploaded audio, but transcription failed: {exc}", "error")

        entry = Transcript(
            user_id=current_user.id,
            filename=title,
            filepath=local_path,
            storage_key=storage_key,
            original_filename=original_filename,
            input_type=input_type,
            source_title=title_override or None,
            source_mimetype=source_mimetype,
            recording_date=recording_date or None,
            weekday=weekday or None,
            recording_time=recording_time or None,
            transcript_original=transcript_text,
            transcript_working=transcript_text,
            review_status="unread",
        )
        db.session.add(entry)
        db.session.commit()

        flash(f"{input_type.title()} entry created.", "success")
        return redirect(url_for("edit_transcript", transcript_id=entry.id))

    requested_type = request.args.get("type", "audio")
    if requested_type not in {"audio", "text", "document"}:
        requested_type = "audio"
    return render_template(
        "upload.html",
        today=datetime.now().strftime("%Y-%m-%d"),
        selected_type=requested_type,
        transcribe_models=LOCAL_WHISPER_MODELS,
        default_transcribe_model=DEFAULT_LOCAL_WHISPER_MODEL,
    )


@app.route("/transcript/<int:transcript_id>", methods=["GET", "POST"])
@login_required
def edit_transcript(transcript_id):
    transcript = owned_transcript_or_404(transcript_id)

    if request.method == "POST":
        transcript.filename = request.form.get("filename", transcript.filename).strip() or transcript.filename
        transcript.transcript_working = request.form.get("transcript_working", "")
        transcript.review_status = request.form.get("review_status", "unread")
        transcript.updated_at = datetime.utcnow()

        db.session.commit()
        flash("Working copy saved.", "success")
        return redirect(url_for("edit_transcript", transcript_id=transcript.id))

    topics = Topic.query.filter_by(user_id=current_user.id).order_by(Topic.name.asc()).all()
    notes = Note.query.filter_by(source_transcript_id=transcript.id, user_id=current_user.id).order_by(Note.created_at.desc()).all()

    return render_template(
        "transcript.html",
        transcript=transcript,
        topics=topics,
        notes=notes,
        ai_tags=_parse_json_text(transcript.ai_tags),
        ai_action_items=_parse_json_text(transcript.ai_action_items),
        ai_entities=_parse_json_text(transcript.ai_entities),
        analysis_data=_parse_json_text(transcript.ai_analysis_json, {}),
        attached_topic_ids={topic.id for topic in transcript.topics},
    )


@app.route("/transcript/<int:transcript_id>/analyze", methods=["POST"])
@login_required
def analyze_transcript(transcript_id):
    transcript = owned_transcript_or_404(transcript_id)
    source_text = (transcript.transcript_working or transcript.transcript_original or "").strip()
    if not source_text:
        flash("There is no text to analyze yet.", "error")
        return redirect(url_for("edit_transcript", transcript_id=transcript.id))

    transcript.processing_status = "analyzing"
    transcript.processing_error = None
    db.session.commit()

    try:
        existing_topic_names = [t.name for t in Topic.query.filter_by(user_id=current_user.id).order_by(Topic.name.asc()).all()]
        analysis = analyze_entry_text(source_text, transcript.filename, existing_topic_names)
        transcript.cleaned_text = analysis.get("cleaned_text", "").strip()
        transcript.ai_summary = analysis.get("summary", "").strip()
        transcript.ai_category = analysis.get("category", "").strip()
        transcript.ai_project = analysis.get("project", "").strip()
        transcript.ai_tags = _json_text(analysis.get("tags"))
        transcript.ai_action_items = _json_text(analysis.get("action_items"))
        transcript.ai_entities = _json_text(analysis.get("entities"))
        transcript.ai_confidence = float(analysis.get("confidence", 0))
        transcript.ai_analysis_json = json.dumps(analysis, ensure_ascii=False, indent=2)
        transcript.processing_status = "ready_for_review"
        transcript.ai_review_status = "pending"
        transcript.processing_error = None
        transcript.updated_at = datetime.utcnow()
        db.session.commit()
        flash("AI analysis is ready for review.", "success")
    except Exception as exc:
        transcript.processing_status = "failed"
        transcript.processing_error = str(exc)
        db.session.commit()
        flash(f"AI analysis failed: {exc}", "error")

    return redirect(url_for("edit_transcript", transcript_id=transcript.id))


@app.route("/transcript/<int:transcript_id>/ai-review", methods=["POST"])
@login_required
def review_ai_analysis(transcript_id):
    transcript = owned_transcript_or_404(transcript_id)
    action = request.form.get("action", "save")
    transcript.cleaned_text = request.form.get("cleaned_text", transcript.cleaned_text or "").strip()
    transcript.ai_summary = request.form.get("ai_summary", transcript.ai_summary or "").strip()
    transcript.ai_category = request.form.get("ai_category", transcript.ai_category or "").strip()
    transcript.ai_project = request.form.get("ai_project", transcript.ai_project or "").strip()
    tags = [x.strip() for x in request.form.get("ai_tags", "").split(",") if x.strip()]
    actions = [x.strip() for x in request.form.get("ai_action_items", "").splitlines() if x.strip()]
    transcript.ai_tags = _json_text(tags)
    transcript.ai_action_items = _json_text(actions)
    selected_topics = []
    for topic_id in request.form.getlist("entry_topic_ids"):
        topic = Topic.query.filter_by(id=int(topic_id), user_id=current_user.id).first()
        if topic:
            selected_topics.append(topic)
    new_names = [x.strip() for x in request.form.get("new_topic_names", "").splitlines() if x.strip()]
    for name in new_names:
        selected_topics.append(get_or_create_topic(name))
    transcript.topics = list({topic.id: topic for topic in selected_topics}.values())
    analysis_data = _parse_json_text(transcript.ai_analysis_json, {})
    analysis_data.update({"cleaned_text": transcript.cleaned_text, "summary": transcript.ai_summary, "category": transcript.ai_category, "project": transcript.ai_project, "tags": tags, "action_items": actions, "approved_topics": [topic.name for topic in transcript.topics]})
    transcript.ai_analysis_json = json.dumps(analysis_data, ensure_ascii=False, indent=2)
    if action == "approve":
        transcript.ai_review_status = "approved"; transcript.processing_status = "approved"; flash("AI analysis and topic links approved.", "success")
    elif action == "reject":
        transcript.ai_review_status = "rejected"; flash("AI analysis marked rejected. The original entry was not changed.", "success")
    else:
        transcript.ai_review_status = "edited"; flash("AI analysis and topic links saved.", "success")
    transcript.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for("edit_transcript", transcript_id=transcript.id))


@app.route("/transcript/<int:transcript_id>/create-note", methods=["POST"])
@login_required
def create_note_from_transcript(transcript_id):
    transcript = owned_transcript_or_404(transcript_id)

    title = request.form.get("note_title", "").strip()
    body = request.form.get("note_body", "").strip()
    new_topic = request.form.get("new_topic", "").strip()
    topic_ids = request.form.getlist("topic_ids")
    remove_from_working = request.form.get("remove_from_working") == "on"

    if not body:
        flash("Note body is empty.", "error")
        return redirect(url_for("edit_transcript", transcript_id=transcript.id))

    if not title and new_topic:
        title = new_topic

    if not new_topic and title and not topic_ids:
        new_topic = title

    if not title:
        flash("Give the note/topic a name.", "error")
        return redirect(url_for("edit_transcript", transcript_id=transcript.id))

    topics = []

    for topic_id in topic_ids:
        topic = Topic.query.filter_by(id=int(topic_id), user_id=current_user.id).first()
        if topic:
            topics.append(topic)

    if new_topic:
        topics.append(get_or_create_topic(new_topic))

    topics = list({topic.id: topic for topic in topics}.values())

    if not topics:
        flash("Choose an existing topic or create a new one.", "error")
        return redirect(url_for("edit_transcript", transcript_id=transcript.id))

    note = Note(
        user_id=current_user.id,
        title=title,
        body=body,
        source_transcript_id=transcript.id,
        topics=topics,
    )

    db.session.add(note)

    if remove_from_working:
        # Remove first exact occurrence. This is intentionally conservative.
        transcript.transcript_working = transcript.transcript_working.replace(body, "", 1).strip()
        transcript.review_status = "in_progress"
        transcript.updated_at = datetime.utcnow()

    db.session.commit()

    flash("Note saved to topic(s).", "success")
    return redirect(url_for("edit_transcript", transcript_id=transcript.id))


@app.route("/topics")
@login_required
def topics_index():
    q = request.args.get("q", "").strip()
    query = Topic.query.filter_by(user_id=current_user.id)
    if q:
        query = query.filter(Topic.name.ilike(f"%{q}%"))
    topics = query.order_by(Topic.name.asc()).all()
    return render_template("topics.html", topics=topics, q=q)

@app.route("/transcript/<int:transcript_id>/original")
@login_required
def original_transcript(transcript_id):
    transcript = owned_transcript_or_404(transcript_id)
    return render_template("original.html", transcript=transcript)

@app.route("/topic/<int:topic_id>")
@login_required
def view_topic(topic_id):
    topic = owned_topic_or_404(topic_id)
    q = request.args.get("q", "").strip()
    entries_query = Transcript.query.join(entry_topics).filter(entry_topics.c.topic_id == topic.id, Transcript.user_id == current_user.id)
    notes_query = Note.query.join(note_topics).filter(note_topics.c.topic_id == topic.id, Note.user_id == current_user.id)
    if q:
        like = f"%{q}%"
        entries_query = entries_query.filter(db.or_(Transcript.filename.ilike(like), Transcript.ai_summary.ilike(like), Transcript.cleaned_text.ilike(like), Transcript.transcript_original.ilike(like), Transcript.ai_tags.ilike(like)))
        notes_query = notes_query.filter(db.or_(Note.title.ilike(like), Note.body.ilike(like)))
    entries = entries_query.order_by(Transcript.created_at.desc()).all()
    notes = notes_query.order_by(Note.created_at.desc()).all()
    return render_template("topic.html", topic=topic, entries=entries, notes=notes, q=q, master_text=topic_master_text(topic))


@app.route("/topic/<int:topic_id>/export")
@login_required
def export_topic(topic_id):
    topic = owned_topic_or_404(topic_id)
    text = topic_master_text(topic)
    output_path = EXPORT_DIR / f"{safe_filename(topic.name)}_master.txt"
    output_path.write_text(text, encoding="utf-8")
    return send_file(output_path, as_attachment=True, download_name=output_path.name)


@app.route("/transcript/<int:transcript_id>/delete", methods=["POST"])
@login_required
def delete_transcript(transcript_id):
    transcript = owned_transcript_or_404(transcript_id)
    db.session.delete(transcript)
    db.session.commit()
    flash("Transcript deleted.", "success")
    return redirect(url_for("index"))

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(debug=True)
