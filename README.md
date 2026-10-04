# Voice-Authorized AI

A flexible prototype for a security-first AI authorization layer that sits in front of any LLM or conversational AI model.

## What this prototype does

- Enforces a permanently designated primary speaker
- Verifies speaker identity before any speech is processed
- Rejects unauthorized speakers automatically
- Blocks interruptions during an active AI response
- Supports temporary session-scoped speaker authorization
- Provides voice commands for granting and revoking speaker authorization
- Restores primary-speaker-only mode automatically
- Supports unknown/uncertain-speaker handling
- Allows configurable confidence thresholds
- Keeps the authorization layer independent from the underlying LLM

## Why this is valuable

This is not just a voice assistant. It is an AI access-control system designed for shared environments where multiple people may speak, but only trusted speakers should be allowed to interact with the model.

Use cases include:

- Shared office AI assistants
- Meeting copilots
- Healthcare voice assistants
- Enterprise knowledge assistants
- Secure household or team devices

## Architecture

The project is organized into a small but extensible middleware stack:

- `app/auth/` — authorization policy engine and state models
- `app/voice/` — voice verification interface and mock implementation
- `app/ai/` — AI gateway that only executes requests after authorization
- `app/api.py` — FastAPI endpoints for session control and secure AI interaction
- `tests/` — prototype verification tests for auth behavior

## Quick start

1. Create a virtual environment
2. Install dependencies
3. Run the API server

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.api:app --reload
```

## Example API flow

### Create a session

```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"primary_speaker_id": "alice"}'
```

### Authorize a temporary speaker

```bash
curl -X POST http://localhost:8000/sessions/SESSION_ID/authorize \
  -H "Content-Type: application/json" \
  -d '{"speaker_id": "bob", "duration_seconds": 300}'
```

### Submit an authorized AI request

```bash
curl -X POST http://localhost:8000/sessions/SESSION_ID/submit \
  -H "Content-Type: application/json" \
  -d '{
    "speaker_id": "alice",
    "transcript": "Summarize the action items from this meeting.",
    "confidence": 0.96
  }'
```

### Revoke temporary access

```bash
curl -X POST http://localhost:8000/sessions/SESSION_ID/revoke \
  -H "Content-Type: application/json" \
  -d '{"speaker_id": "bob"}'
```

## Default policy behavior

- Primary speaker is always allowed by default
- Temporary speaker authorization expires by timeout
- Unknown speakers are rejected
- Non-authorized speakers are blocked while an AI response is active
- Confidence below threshold is rejected
- Admin can restore primary-only mode at any time

## Extending the prototype

This is intentionally flexible so it can be adapted for different domains.

You can swap in:

- A real speaker verification backend
- An enterprise policy store
- A different AI provider
- Voice-command processing for grant/revoke workflows
- Auditing and compliance logging

## Testing

```bash
pytest -q
```

## Prototype status

This is a working authorization middleware prototype intended to demonstrate the concept and serve as a foundation for a production-ready implementation.

It is flexible enough to evolve toward:

- enterprise meeting assistants
- healthcare secure voice agents
- office shared AI workstations
- consumer home AI systems with voice access control

---

The core idea is simple:

The model never decides whether a speaker is authorized.

The authorization layer decides first.
