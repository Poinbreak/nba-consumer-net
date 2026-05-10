# Setup Guide

Complete setup instructions for the NBA Consumer Net project.

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (via Supabase)
- Git

## Backend Setup

### 1. Python Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

Create a `.env` file in the `backend/` directory:

```env
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_supabase_host
DB_PORT=5432

SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Load Initial Data

```bash
# Bootstrap Kaggle API (for data downloads)
python scripts/bootstrap_kaggle.py

# Load statistics
python scripts/load_stats.py

# Run nightly ingestion
python scripts/nightly_ingest.py
```

### 6. Start Backend Server

```bash
python manage.py runserver
```

Server runs at `http://localhost:8000`

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Environment Variables

Create `.env.local` in `frontend/`:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

Frontend runs at `http://localhost:5173`

## Database Setup (Supabase)

1. Create a Supabase project
2. Run migrations:
   ```bash
   cd supabase
   # Apply migrations manually or via Supabase CLI
   ```
3. Update backend `.env` with database credentials

## Machine Learning Models

Models are trained and stored in `backend/ml/`. Key models:

- `train_game_model.py` - Game outcome prediction
- `train_player_props.py` - Player prop predictions
- `train_awards.py` - Award predictions
- `win_probability.py` - Win probability calculation

To train models:

```bash
cd backend
python ml/train.py
```

## Data Ingestion

### CSV Data Files

Data files are stored in `backend/data/` (not tracked in git):

- `Games.csv` - Game results
- `Players.csv` - Player information
- `PlayerStatistics.csv` - Player stats
- `TeamStatistics.csv` - Team stats
- `LeagueSchedule*.csv` - Upcoming schedule

### ETL Scripts

- `etl/nba_ingestion.py` - Main NBA data ingestion
- `etl/odds_ingestion.py` - Betting odds data
- `etl/salary_ingestion.py` - Player salary data

## Testing

### Backend Tests

```bash
cd backend
python manage.py test
```

### Frontend Tests

```bash
cd frontend
npm run test
```

## Linting & Formatting

### Backend

```bash
cd backend
# Django checks
python manage.py check

# Lint
pylint api/
```

### Frontend

```bash
cd frontend
npm run lint
npm run format
```

## Troubleshooting

### Port Already in Use

Change port for Django:
```bash
python manage.py runserver 8001
```

Change port for Vite in `frontend/vite.config.js`

### Database Connection Issues

1. Verify Supabase credentials in `.env`
2. Check database is running
3. Verify network access is allowed

### WebSocket Connection Issues

1. Ensure Django Channels is running
2. Check WebSocket URL in frontend `.env`
3. Verify CORS settings in `backend/nba_net/settings.py`

### ML Model Issues

1. Ensure training data is loaded in database
2. Check for sufficient disk space
3. Verify scikit-learn/TensorFlow are installed

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Configure `ALLOWED_HOSTS`
3. Use Gunicorn for Django:
   ```bash
   gunicorn nba_net.wsgi:application --bind 0.0.0.0:8000
   ```
4. Use Vite build for frontend:
   ```bash
   npm run build
   ```
5. Deploy with Docker or your preferred platform

## Development Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes
3. Test locally
4. Commit: `git commit -m "Add: detailed description"`
5. Push: `git push origin feature/my-feature`
6. Open PR for review

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Supabase Documentation](https://supabase.com/docs)
- [Django Channels Documentation](https://channels.readthedocs.io/)
