import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import Player from './pages/Player';
import Team from './pages/Team';
import Predictions from './pages/Predictions';
import BetTracker from './pages/BetTracker';
import GM from './pages/GM';

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col">
        <nav className="border-b border-border bg-court text-white px-6 py-4 flex items-center justify-between">
          <Link to="/" className="text-xl font-extrabold tracking-tighter">NBA<span className="text-gray-400">NET</span></Link>
          <div className="flex space-x-6 text-sm font-semibold">
            <Link to="/player" className="hover:text-gray-300 transition-colors">Player</Link>
            <Link to="/team" className="hover:text-gray-300 transition-colors">Team</Link>
            <Link to="/predictions" className="hover:text-gray-300 transition-colors">Predictions</Link>
            <Link to="/bets" className="hover:text-gray-300 transition-colors">Bet Tracker</Link>
            <Link to="/gm" className="hover:text-gray-300 transition-colors">GM Mode</Link>
          </div>
        </nav>
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/player" element={<Player />} />
            <Route path="/team" element={<Team />} />
            <Route path="/predictions" element={<Predictions />} />
            <Route path="/bets" element={<BetTracker />} />
            <Route path="/gm" element={<GM />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
