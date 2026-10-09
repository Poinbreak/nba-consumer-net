# NBA·NET

NBA stats you can ask questions of, model predictions you can check, and a GM mode where trades change the projections.

## What's in it

| Area | What it does |
|---|---|
| **Ask** | Search box that answers plain-English stat questions ("Luka last 10 games", "most assists this season", "Jokic vs Lakers") from our own database |
| **Players / Teams** | StatMuse-style pages: season-by-season stats, game logs, contracts, injuries, rosters, schedules |
| **Predict** | Win probability + reasons for every upcoming game, MVP / DPOY / ROY / 6MOY / MIP races, simulated title odds |
| **Odds** | Live sportsbook moneylines next to our model's probability |
| **GM Mode** | Pick a team, make CBA-checked trades with real contracts, see projected record and off/def/net rating, simulate the season |

## Models (all trained on our data, all backtested)

| Model | Method | Held-out result |
|---|---|---|
| Game outcome | XGBoost on point-in-time rolling form + Elo + rest | 67% accuracy on 2025-26 (home-team baseline 56%) |
| Awards | XGBoost on Basketball-Reference voting history (Kaggle), per-season z-scored stats | MVP winner ranked #1 in 4 of 6 seasons, top 3 in 6 of 6; DPOY and MIP are weak |
| Season / title odds | Monte Carlo (5,000 sims) over the real schedule + play-in + best-of-7 series | n/a |
| Roster strength (GM) | Minutes-weighted Game Score/36 → team rating, calibrated by projecting each team's next season from prior-season player stats | correlation 0.52 with real next-season net rating |

Limits worth knowing: ratings don't yet see injuries during a season or offseason context beyond rosters; box scores can't see defense, so GM-mode defensive projections vary little between teams; GM trade *changes* are more reliable than absolute numbers.

## Architecture

```
ESPN public JSON ──► backend/scripts/sync_scores.py, sync_rosters.py ─┐
Kaggle CSVs ───────► backend/scripts/bulk_load.py (history)            ├─► Supabase Postgres
Kaggle awards ─────► backend/ml/train_awards.py                        │         │
GitHub Actions ───── scores /10 min · rosters /6 h · model+predict /3 h │         ▼
                     awards + title odds daily                          Django REST (backend/api) ─► React/Vite (frontend)
```

- **Backend**: Django + DRF. `api/v2.py` (pages), `api/ask.py` (natural-language search), `api/gm.py` (GM mode), `api/db.py` (pooled SQL, parallel queries, short TTL cache).
- **ML**: `backend/ml/` — `features.py`, `train_game_model.py`, `predict_upcoming.py`, `award_features.py`, `train_awards.py`, `predict_awards.py`, `simulate_season.py`, `roster_model.py`.
- **Frontend**: React 19 + Vite + React Query. `src/views/*`, shared kit in `src/ui/kit.jsx`, design tokens in `src/ui.css`.
- **Data sources**: ESPN's public JSON API for live data (NBA's own endpoints block cloud IPs), Kaggle for history and awards, The Odds API for lines.

## Run it locally

```bash
# 1. repo-root .env  (see SETUP.md). The one that matters:
#    DATABASE_URL=postgresql://postgres.<project-ref>:<password>@<region>.pooler.supabase.com:5432/postgres
#    ODDS_API_KEY=...
cd backend && pip install -r requirements.txt && python manage.py runserver 8000
```

```bash
cd frontend && npm install && npm run dev      # http://localhost:5173, proxies /api to :8000
```

Use the Supabase **session pooler** URI (IPv4, works from GitHub Actions). Encode special characters in the password (`@` → `%40`). The pooler allows 15 simultaneous clients in total, so the API keeps only 4–6 open.

## Data & model refresh

```bash
python backend/scripts/bulk_load.py            # one-time history load (idempotent)
python backend/scripts/sync_scores.py          # schedule, live scores, box scores (ESPN)
python backend/scripts/sync_rosters.py         # rosters, contracts, injuries
python backend/ml/train_game_model.py && python backend/ml/predict_upcoming.py
python backend/ml/train_awards.py && python backend/ml/predict_awards.py
python backend/ml/simulate_season.py
python backend/ml/roster_model.py              # refit the GM roster model (writes roster_model.json)
```

GitHub Actions run all of this on a schedule; they need a single repo secret, `DATABASE_URL` (the pooler URI, only the URI, no `DATABASE_URL=` prefix).

## Tests

```bash
cd backend && python -m unittest discover tests     # CBA trade rules + minutes allocation, no database needed
```

## GM Mode rules (simplified CBA)

Thresholds are the 2025-26 official values +7% (editable in `api/gm.py`). Under the cap after the trade: always fine. Over the cap: incoming salary ≤ 200% of outgoing + $0.25M. Above the first apron: ≤ 110% + $0.1M. Above the second apron: ≤ 100% and no combining contracts. Recently signed players can't be traded. Roster ceiling is 21 (camp rosters), 13 minimum is a warning. Verify against the current CBA before relying on any edge case.

See [SETUP.md](SETUP.md) for first-time setup.
