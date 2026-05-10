import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Player from './pages/Player';
import Team from './pages/Team';
import Predictions from './pages/Predictions';
import BetTracker from './pages/BetTracker';
import GM from './pages/GM';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen flex flex-col bg-grid">
          <Navbar />
          <main className="flex-1">
            <Routes>
              <Route path="/"            element={<Home />} />
              <Route path="/player"      element={<Player />} />
              <Route path="/team"        element={<Team />} />
              <Route path="/predictions" element={<Predictions />} />
              <Route path="/bets"        element={<BetTracker />} />
              <Route path="/gm"          element={<GM />} />
            </Routes>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
