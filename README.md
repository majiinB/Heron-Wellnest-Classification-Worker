# Heron Wellnest Classification Worker

A background worker that exposes scheduler-triggered endpoints to run daily and weekly classification, processing journals, mood check-ins, gratitude, and Flip & Feel sessions to persist analytics and classification results using a Random Forest model.

## Table of Contents

- Features
- Tech Stack
- Architecture
- Getting Started
- Configuration and Environment Variables
- Daily Classification Flow
- Weekly Classification Flow
- Extending Activity Checks
- Troubleshooting
- Project Structure
- Testing
- Deployment
- License & Authors

## Features

- Runs daily batch classification for users with mood check-ins, using journals, gratitude, and Flip & Feel signals as model inputs.
- Persists per-user analytics features and daily classification results in Postgres.
- Runs weekly classification rules and stores weekly rollups and flags.
- Uses a Random Forest model (joblib) with an optional label encoder.
- Uses PostgreSQL (Supabase compatible) and async SQLAlchemy / asyncpg for DB access.
- Supports containerized deployment via Docker.

## Tech Stack

- Python 3.12+
- async SQLAlchemy (SQLAlchemy 2.0 async), asyncpg
- joblib (model loading)
- PostgreSQL / Supabase
- Docker
- pytest (for tests)

## Architecture

- Cron job / scheduler → calls `POST /daily-scheduler` and `POST /weekly-scheduler` on this service.
- Classification Worker (this repo) → builds feature inputs, runs the model, stores analytics + classifications, and computes weekly rollups.

Service entrypoint: FastAPI app in `app/main.py`, routes in `app/routes/classification_route.py`. Random Forest model files live in `app/ml_model/`:

- `app/ml_model/random_forest.joblib`
- `app/ml_model/random_forest_label_encoder.joblib`

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL (or Supabase)
- Google Cloud project with Pub/Sub (or the Pub/Sub emulator)
- git, docker (optional)

### Installation

1. Clone the repository

   bash
   git clone <repository-url> ; cd heron-wellnest-classification-worker

2. Create and activate a virtual environment, install dependencies (PowerShell example)

   bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt

3. Create a `.env` file in the project root (see the "Configuration and Environment Variables" section below).

4. Start the worker locally

   bash
   python -m app.worker

### Docker

   bash
   docker build -t hw-classification-worker .
   docker run --env-file .env --rm hw-classification-worker

## Configuration and Environment Variables

Create a `.env` file at the project root. Do NOT commit secrets. Important variables used by this project (names taken from `app/config/env_config.py`):

- ENVIRONMENT (e.g. production, development, test)
- PORT (defaults to 8080)
- MODEL_PATH (defaults to `xlm-roberta-base`, but this repo ships Random Forest joblib files in `app/ml_model`)
- MODEL_LABEL_ENCODER_PATH (optional)
- DB_HOST (e.g. localhost)
- DB_PORT (default 5432)
- DB_USER (default `postgres`)
- DB_PASSWORD
- DB_NAME (default `heron_wellnest`)
- CONTENT_ENCRYPTION_KEY (must be at least 32 chars)
- CONTENT_ENCRYPTION_ALGORITHM (default `aes-256-gcm`)
- CONTENT_ENCRYPTION_IV_LENGTH (default 16)
- CONTENT_ENCRYPTION_KEY_LENGTH (default 32)
- PUBSUB_NLP_TOPIC (default `journal-topic`)
- GOOGLE_CLOUD_PROJECT_ID

Example `.env` (PowerShell-friendly):

   # .env (example)
   ENVIRONMENT=development
   PORT=8080
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_NAME=heron_wellnest
   CONTENT_ENCRYPTION_KEY=replace-with-a-32-char-min-secret
   GOOGLE_CLOUD_PROJECT_ID=your-gcp-project
   PUBSUB_NLP_TOPIC=journal-topic

Note: The project uses pydantic settings which load `.env` automatically. Use a secret manager for production.

## Daily Classification Flow

The worker implements the following flow for each scheduled daily run:

1. Set the target date to today (UTC).
2. Load all mood check-ins for the date (users without a check-in are skipped).
3. For each user, load journal entries, gratitude presence, and Flip & Feel sessions.
4. Aggregate journal wellness probabilities, one-hot encode moods, and compute Flip & Feel percentages.
5. Run the Random Forest model in batch and produce per-user predictions and probabilities.
6. Persist analytics features and daily classification rows for each user.

## Weekly Classification Flow

The weekly scheduler computes a dominant label and rule-based flags from recent daily classifications, then persists the weekly rollup.

## Extending Activity Checks

- Keep a central dispatch in the service layer (e.g., `classification_service`) that maps event types to checker functions.
- Implement modular checkers with a signature like:

   py
   async def check_journal_entry(user_id: str, journal_id: str) -> bool:
       ...

- Keep checkers idempotent and DB-safe: verify records exist, verify ownership, and avoid double-completing quests.
- Add new events to the event-to-check mapping (e.g., `JOURNAL_ENTRY_CREATED -> check_journal_entry`).
- If you add or update models, place model artifacts under `app/ml_model/` and update `MODEL_PATH` / `MODEL_LABEL_ENCODER_PATH` if necessary.

## Troubleshooting

- Error: `asyncpg.exceptions.InternalServerError: Tenant or user not found`
  - Verify DB credentials and `DB_USER` / `DB_HOST` are correct.
  - Confirm the connecting role/user exists in the DB and has access to the database.
  - If using Supabase, ensure you are using the correct connection string and the user was not rotated.

- Model loading issues:
  - Confirm the model files exist at `app/ml_model/random_forest.joblib` and `app/ml_model/random_forest_label_encoder.joblib`.
  - Check that `joblib` is installed and the model artifact was exported with a compatible scikit-learn version.

- Quest checks failing:
  - Verify `daily_quests`, `quest_definitions`, and `user_quests` table rows exist for the given date and user.
  - Make sure checkers validate ownership (event userId matches DB record owner).

Logs: See `app/utils/logger_util.py` for logging configuration and to increase verbosity when debugging.

## Project Structure

A typical layout:

```
.
├── app/
│   ├── config/                # env and datasource (app/config/env_config.py, datasource_config.py)
│   ├── controllers/           # request handlers
│   ├── services/              # business logic (classification_service, weekly_classification_service)
│   ├── repositories/          # DB access layers
│   ├── ml_model/              # model artifacts (random_forest.joblib, random_forest_label_encoder.joblib)
│   ├── utils/                 # db utils, pubsub helpers, encryption utils, logger_util
│   ├── worker.py              # legacy Pub/Sub worker example (commented)
│   └── main.py                # FastAPI application entry
├── Dockerfile
├── requirements.txt
├── README.md
└── .env.example
```

Key files in this repo:
- `app/main.py` — FastAPI application entry.
- `app/routes/classification_route.py` — scheduler endpoints for daily/weekly runs.
- `app/controllers/classification_controller.py` — batch feature building + inference flow.
- `app/services/classification_service.py` — Random Forest model wrapper.
- `app/services/weekly_classification_service.py` — weekly rollup rules and persistence.
- `app/config/datasource_config.py` — async DB engine/session setup.
- `app/ml_model/` — Random Forest model artifacts.

## Testing

- Run tests with pytest:

   bash
   pytest

- Add unit tests for each checker function to ensure idempotence and correct status transitions.
- For integration tests, mock Pub/Sub messages and use a test Postgres database or a Supabase test project.
- Add a test that loads the model artifact and runs a smoke inference to ensure compatibility.

## Deployment

- Containerize and deploy to your preferred environment (Cloud Run, Cloud Run jobs, Kubernetes).
- Use CI to run tests, build the image, and publish to your container registry.
- Inject secrets using your cloud provider's secret manager (avoid committing secrets).

Example Docker (PowerShell):

   bash
   docker build -t hw-classification-worker .
   docker run --env-file .env --rm hw-classification-worker

## License & Authors

- This project is private / proprietary to the Heron Wellnest platform.
- Author / Maintainer: Arthur M. Artugue

---
Last Updated: 2026-05-27

