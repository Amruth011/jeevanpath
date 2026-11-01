# JeevanPath

JeevanPath is a browser voice prototype for a post-discharge assistant using synthetic patient data only.

The backend runs audio through configurable Gnani Prisma, deterministic safety rules, Gnani Evon, and Gnani Timbre adapters. Provider URLs and keys are required environment variables; no vendor endpoint is assumed by the application.

## Local development

```powershell
cd backend
python -m pip install -e ".[test]"
pytest
python -m app.seed
uvicorn app.main:app --reload
```

In another terminal:

```powershell
cd dashboard
npm install
npm run typecheck
npm run dev
```

Copy `backend/.env.example` to `.env` and set the Prisma and Timbre URLs and keys before attempting a real voice turn. The backend loads this file with `python-dotenv`; `.env` is ignored by Git.

The seed command explicitly inserts one clearly marked synthetic development test patient with conversation ID `conversation-001` into SQLite. It is idempotent and never runs automatically unless `DEMO_SEED=true` is explicitly configured. The dashboard rejects the assumption that records are real clinical data without consent. On Vercel, set `DEMO_SEED=true` only for the demo environment; leave it unset or set it to `false` for production data environments. The API uses the writable ephemeral `/tmp/jeevanpath.db` location on Vercel.

The documented REST adapters use Gnani's Vachana API:

- Health check: `GET /api/health` (the unprefixed `/health` endpoint remains available for local use).
- Prisma: `POST /stt/v3`, multipart `audio_file`, `language_code`, `model=prisma-v3.0`, and `format=transcribe`; response JSON contains `transcript`.
- Timbre: `POST /api/v1/tts/inference`, JSON text/voice/model/audio configuration; response is audio bytes, configured here as 48 kHz linear PCM WAV.
- Authentication uses `X-API-Key-ID`; secrets are never included in health responses.

No Evon HTTP adapter is implemented because no reasoning API is available. Deterministic safety rules remain authoritative; without verified discharge context or a reasoning provider, the workflow returns a safe uncertainty response and opens human review.

The browser test page is available at `http://localhost:3000`.

## Vercel deployments

The GitHub repository is connected to Vercel. Pushes to `main` trigger a new
deployment automatically; use a small documentation change such as this one
to verify the connection without changing application behavior. If a push
does not create a deployment, check the Vercel project's Git settings and
confirm that the production branch is `main`.
