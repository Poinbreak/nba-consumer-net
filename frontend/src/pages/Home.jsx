import React from 'react';
import SearchBar from '../components/SearchBar';
import GameTile from '../components/GameTile';

export default function Home() {
  const dummyGames = [
    {
      id: 1,
      homeTeam: { abbrev: 'LAL', accent: '#552583' },
      awayTeam: { abbrev: 'GSW', accent: '#1D428A' },
      homeScore: 102,
      awayScore: 98,
      quarter: 'Q4',
      clock: '2:15',
      winProbHome: 78
    },
    {
      id: 2,
      homeTeam: { abbrev: 'BOS', accent: '#007A33' },
      awayTeam: { abbrev: 'MIA', accent: '#98002E' },
      homeScore: 88,
      awayScore: 92,
      quarter: 'Q3',
      clock: '5:40',
      winProbHome: 42
    },
    {
      id: 3,
      homeTeam: { abbrev: 'DEN', accent: '#0E2240' },
      awayTeam: { abbrev: 'PHX', accent: '#1D1160' },
      homeScore: 115,
      awayScore: 110,
      quarter: 'Final',
      clock: '',
      winProbHome: 100
    }
  ];

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-73px)] py-12">
      <div className="text-center mb-12 w-full px-6 flex flex-col items-center">
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8">
          The NBA, <span className="text-gray-400">Decoded.</span>
        </h1>
        <SearchBar />
      </div>

      <div className="w-full mt-12 overflow-hidden">
        <div className="px-6 mb-4 font-bold text-gray-400 uppercase tracking-widest text-sm">
          Live & Upcoming
        </div>
        <div className="flex space-x-6 overflow-x-auto px-6 pb-8 scrollbar-hide">
          {dummyGames.map(game => (
            <GameTile key={game.id} {...game} />
          ))}
        </div>
      </div>
    </div>
  );
}
