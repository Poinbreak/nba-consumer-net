import React from 'react';
import WinMeter from '../components/WinMeter';

export default function Predictions() {
  const games = [
    {
      id: 1,
      homeTeam: { name: 'Los Angeles Lakers', abbrev: 'LAL', accent: '#552583' },
      awayTeam: { name: 'Denver Nuggets', abbrev: 'DEN', accent: '#0E2240' },
      time: '10:00 PM ET',
      homeWinProb: 42,
      awayWinProb: 58,
      spread: 'DEN -4.5',
      overUnder: '228.5'
    },
    {
      id: 2,
      homeTeam: { name: 'Boston Celtics', abbrev: 'BOS', accent: '#007A33' },
      awayTeam: { name: 'Miami Heat', abbrev: 'MIA', accent: '#98002E' },
      time: '7:30 PM ET',
      homeWinProb: 76,
      awayWinProb: 24,
      spread: 'BOS -8.5',
      overUnder: '212.0'
    }
  ];

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <div className="mb-12">
        <h1 className="text-5xl font-extrabold tracking-tighter mb-4">Tonight's Predictions</h1>
        <p className="text-xl text-gray-400 font-semibold">AI-powered win probabilities and lines.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {games.map(game => (
          <div key={game.id} className="bg-surface border border-border rounded-2xl p-8 relative overflow-hidden">
            <div className="flex justify-between items-center mb-8">
              <span className="text-gray-400 font-bold uppercase tracking-widest text-sm">{game.time}</span>
              <span className="bg-court px-3 py-1 rounded-full text-xs font-bold border border-border">
                {game.spread} • O/U {game.overUnder}
              </span>
            </div>

            <div className="flex justify-between items-center relative z-10">
              <div className="text-center w-1/3">
                <div className="text-4xl font-extrabold tracking-tighter mb-1">{game.awayTeam.abbrev}</div>
                <div className="text-sm font-semibold text-gray-500">{game.awayWinProb}%</div>
              </div>
              
              <div className="flex-1 flex justify-center">
                <WinMeter homeProb={game.homeWinProb} homeColor={game.homeTeam.accent} awayColor={game.awayTeam.accent} />
              </div>

              <div className="text-center w-1/3">
                <div className="text-4xl font-extrabold tracking-tighter mb-1">{game.homeTeam.abbrev}</div>
                <div className="text-sm font-semibold text-gray-500">{game.homeWinProb}%</div>
              </div>
            </div>
            
            <button className="w-full mt-8 bg-white text-black font-bold py-3 rounded-xl hover:bg-gray-200 transition-colors">
              View Player Props
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
