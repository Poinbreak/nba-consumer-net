# NBA Consumer Net

A full-stack NBA analytics platform with real-time game predictions, player props, and trade machine simulation.

## Features

- **Real-time Game Tracking**: WebSocket-based live score updates
- **Predictive Models**: ML-powered game predictions and player prop predictions
- **Trade Machine**: Simulate team trades with win probability impact
- **Player Statistics**: Comprehensive player and team statistics
- **Bet Tracking**: Track and analyze betting predictions
- **Win Probability Graphs**: Visual win probability forecasting

## Stack

### Backend
- **Framework**: Django + Django Channels (WebSocket support)
- **Database**: Supabase (PostgreSQL)
- **ML**: Python (scikit-learn, TensorFlow)
- **API**: RESTful + WebSocket

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS
- **State Management**: Custom hooks (React)
- **Real-time**: WebSocket integration

### Data
- **ETL**: CSV ingestion from Kaggle
- **ML Models**: Trained on historical NBA data
- **Features**: Player stats, team statistics, game outcomes

## Project Structure

```
├── backend/          # Django application
│   ├── api/         # Main API endpoints & WebSocket consumers
│   ├── ml/          # Machine learning models
│   ├── etl/         # Data ingestion scripts
│   ├── scripts/     # Utility scripts
│   ├── data/        # CSV data files (not tracked in git)
│   └── nba_net/     # Django settings
├── frontend/        # React application
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── hooks/       # Custom React hooks
│   │   └── assets/
│   └── vite.config.js
└── supabase/        # Database migrations
```

## Getting Started

See [SETUP.md](SETUP.md) for detailed installation and setup instructions.

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Documentation

- **Games**: `/api/games/`
- **Players**: `/api/players/`
- **Predictions**: `/api/predictions/`
- **WebSocket**: `ws://localhost:8000/ws/game/<game_id>/`

## Contributing

1. Create a feature branch
2. Make changes
3. Test locally
4. Commit with clear messages
5. Push to main

## License

MIT
