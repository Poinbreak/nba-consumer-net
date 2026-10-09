import React from 'react';
import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Shell } from './ui/kit';
import Home from './views/Home';
import Scores from './views/Scores';
import Ask from './views/Ask';
import PlayerPage from './views/PlayerPage';
import TeamPage from './views/TeamPage';
import Teams from './views/Teams';
import Predict from './views/Predict';
import Odds from './views/Odds';
import GM from './views/GM';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Shell>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/scores" element={<Scores />} />
            <Route path="/ask" element={<Ask />} />
            <Route path="/player/:id" element={<PlayerPage />} />
            <Route path="/team/:id" element={<TeamPage />} />
            <Route path="/teams" element={<Teams />} />
            <Route path="/predict" element={<Predict />} />
            <Route path="/odds" element={<Odds />} />
            <Route path="/gm" element={<GM />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Shell>
      </Router>
    </QueryClientProvider>
  );
}
