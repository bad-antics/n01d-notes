# N01D Notes Documentation

## Overview

N01D Notes is an encrypted note-taking application designed for security researchers. Store research notes, findings, credentials, and sensitive information with AES-256-GCM encryption.

## Features

- **End-to-End Encryption** — AES-256-GCM with Argon2id key derivation
- **Markdown Support** — Write notes in Markdown with live preview
- **Tagging System** — Organize notes with tags and categories
- **Search** — Full-text search across encrypted notes (client-side)
- **Export** — Export to PDF, HTML, or encrypted archive
- **Attachments** — Attach and encrypt files alongside notes

## Security Model

```
User Password
    ↓ (Argon2id, t=3, m=64MB, p=4)
Master Key (256-bit)
    ↓ (HKDF-SHA256)
    ├── Note Encryption Key
    ├── Index Encryption Key
    └── Attachment Encryption Key
```

Each note is encrypted independently with a derived key, so compromising one note doesn't expose others.

## Usage

```bash
# Initialize encrypted vault
n01d-notes init

# Create a new note
n01d-notes new "Target Assessment - 192.168.1.0/24"

# Search notes
n01d-notes search "SQL injection" --tag pentest

# Export findings
n01d-notes export --tag "project-x" --format pdf
```

## Part of N01D Suite

Integrates with other N01D tools — pipe scan results directly into categorized notes.
