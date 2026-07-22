# 🧠 ShermLabs Memory

ShermLabs Memory is an AI-powered knowledge management system that transforms voice recordings, documents, notes, and ideas into an organized, searchable second brain.

Instead of simply storing information, ShermLabs Memory uses AI to transcribe, summarize, organize, and connect your knowledge so it becomes easier to retrieve and build upon over time.

---

## Features

### 🎙 Voice & Audio Capture

- Upload audio recordings
- AI transcription
- Preserve original transcript
- Maintain editable working copy

---

### 📄 Documents & Notes

- Upload documents
- Paste text directly
- Create notes from transcripts
- Rich text editing

---

### 🤖 AI Organization

Each entry is automatically analyzed to generate:

- Summary
- Cleaned text
- Suggested project
- Suggested topics
- Tags
- Entities
- Action items

Original content is always preserved.

---

### 📚 Topics

Organize knowledge into reusable topics.

Topics can contain:

- Voice recordings
- Documents
- Notes
- AI summaries

Browse and search across all related information.

---

### 📁 Projects

Projects provide a higher-level organization for groups of related topics.

Example:

```
Project
    ShermLabs Memory

        Topics
            UI Design
            Authentication
            AI Features
            Database
```

---

### 🔍 Search

Search across:

- Original transcripts
- AI cleaned text
- Notes
- Summaries
- Projects
- Tags

---

### 👥 Multi-user

Each user has their own:

- Entries
- Notes
- Topics
- Projects

Authentication is handled through Flask-Login.

---

## Technology

Backend

- Flask
- SQLAlchemy
- Flask-Login
- PostgreSQL (Supabase)

Storage

- Supabase Storage

AI

- Together AI
- Local Whisper support
- Future embedding pipeline

Frontend

- HTML
- CSS
- JavaScript

Deployment

- Render

---

## Roadmap

### Near Term

- Topic improvements
- Project dashboard
- Better search
- Entry archive
- Delete confirmation
- Improved UI
- Drag-and-drop organization

### Future

- Semantic embeddings
- RAG search
- Knowledge graph
- AI-generated topic wiki
- AI chat across your personal knowledge
- Cross-topic relationship discovery
- Timeline visualization

---

## Philosophy

ShermLabs Memory is designed around one idea:

> Capture everything once. Never lose an idea again.

The goal is not simply to store information, but to build a living knowledge system that grows alongside its user.

---

## Development Status

ShermLabs Memory is currently under active development.

Current capabilities include:

- ✅ User authentication
- ✅ Audio upload
- ✅ AI transcription
- ✅ AI analysis
- ✅ Topics
- ✅ Notes
- ✅ Search
- ✅ Multi-user support
- ✅ Cloud database
- ✅ Cloud storage

Upcoming work focuses on transforming stored information into a fully interconnected AI knowledge system.

---

## Contact

**ShermLabs**

📧 sherm@shermlabs.com