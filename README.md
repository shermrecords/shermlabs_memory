# ShermLabs Memory

> An AI-powered personal knowledge system that transforms voice recordings, pasted text, and documents into an organized, searchable knowledge base.

---

## Overview

ShermLabs Memory is a Flask-based web application that allows users to capture information in multiple formats and automatically organize it using AI.

Instead of simply storing notes, the system builds a structured knowledge base by extracting summaries, projects, tags, entities, action items, and relationships between entries.

The long-term goal is to create a personal AI assistant capable of remembering, organizing, and synthesizing years of accumulated knowledge.

---

# Features

## Current

- Audio upload
- Automatic transcription
- Paste text
- Document upload
- Transcript editing
- Topic management
- Supabase integration
- AI analysis
- Search

---

## Planned

- Semantic search
- Related entries
- Knowledge graph
- AI chat over all entries
- Timeline view
- Daily digest
- Automatic project detection
- Duplicate detection
- Entity linking
- Task extraction
- Local LLM support (Ollama)
- Multi-user accounts
- Mobile-friendly interface

---

# Supported Inputs

- Voice recordings
- Pasted text
- PDF documents
- DOCX documents
- Markdown
- Plain text

Future:

- Email import
- Images (OCR)
- Web clipping
- YouTube transcripts
- Browser extension

---

# Processing Pipeline

```
Capture
    │
    ▼
Store Original
    │
    ▼
Extract Text
    │
    ▼
Clean Text
    │
    ▼
AI Analysis
    │
    ▼
Review
    │
    ▼
Knowledge Base
```

---

# AI Analysis

Each entry produces:

- Cleaned text
- Summary
- Category
- Suggested project
- Tags
- Action items
- Entities
- Confidence score

The original content is always preserved.

---

# Technology Stack

## Backend

- Flask
- SQLAlchemy
- Supabase
- PostgreSQL

## AI

- OpenAI Whisper / GPT-4o Transcribe
- Together AI
- Ollama (planned)
- OpenAI-compatible API

## Frontend

- HTML
- CSS
- JavaScript

## Deployment

- Render
- GitHub

---

# Installation

Clone the repository.

```bash
git clone https://github.com/YOUR_USERNAME/shermlabs-memory.git
```

Enter the project.

```bash
cd shermlabs-memory
```

Create a virtual environment.

```bash
python -m venv venv
```

Activate it.

### Windows

```bash
venv\Scripts\activate
```

### macOS/Linux

```bash
source venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Create a `.env` file.

Example:

```env
SECRET_KEY=change-me

DATABASE_URL=

SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_ROLE_KEY=

TOGETHER_API_KEY=
TOGETHER_BASE_URL=https://api.together.xyz/v1
TOGETHER_ANALYSIS_MODEL=openai/gpt-oss-20b
```

Run the application.

```bash
python app.py
```

---

# Development Roadmap

## Version 1

- [x] Audio uploads
- [x] Transcription
- [x] Paste text
- [x] Document uploads
- [x] AI summaries

## Version 2

- [ ] Projects
- [ ] Tags
- [ ] Semantic search
- [ ] Related entries

## Version 3

- [ ] Knowledge graph
- [ ] AI chat
- [ ] Timeline
- [ ] Daily review

## Version 4

- [ ] Local AI
- [ ] Offline mode
- [ ] Multi-device synchronization

---

# Vision

ShermLabs Memory is designed to become an external memory system.

Rather than storing files, it stores knowledge.

Every recording, document, and note becomes connected through AI, allowing users to ask questions like:

- "What have I learned about PTSD?"
- "Find every idea I've had about this software project."
- "Show everything related to this person."
- "Summarize my thoughts from the last six months."

The objective is to create a searchable, evolving knowledge base that grows alongside its user.

---

# License

Private project.

Copyright © ShermLabs.
