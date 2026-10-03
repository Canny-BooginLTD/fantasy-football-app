# Master App Layout

This repository is organized as the master `fantasy-football-app` project with Watson embedded as a subpackage inside the application folder.

## Target structure

```text
fantasy-football-app/
  watson/
  tests/
  docs/
  credentials
  requirements.txt
  setup.py
  README.md
  .gitignore
```

## Watson subpackage responsibilities

- `watson/main.py` - Watson initialization
- `watson/analyzer.py` - recommendations and analysis logic
- `watson/ingest.py` - ESPN historical import runner
- `watson/history_store.py` - local snapshot persistence
- `watson/master_project.py` - season-wide import/export orchestration
- `watson/export_contract.py` - stable export payload
- `watson/config.py` - Watson-specific runtime config

## Root-level responsibilities

- App bootstrap and runtime wiring
- UI/API/server startup
- Build/deployment config
- Monorepo-level documentation and testing
- Repository ownership and release management

## Rule of thumb

Keep ingestion and analysis inside `watson/`, and keep the app root responsible for composition, launch, and deployment.

## Migration checklist

1. Keep all Watson source files inside `watson/`.
2. Keep all tests under `tests/`.
3. Keep all docs under `docs/`.
4. Keep ESPN credentials out of source control.
5. Run `pytest tests/` before committing changes.
