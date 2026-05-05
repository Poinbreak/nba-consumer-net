import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function GameTile({ homeTeam, awayTeam, homeScore, awayScore, quarter, clock, winProbHome }) {
  const navigate = useNavigate();
  const homeAccent = homeTeam.accent || '#552583';

  return (
    <div 
      className="bg-surface rounded-xl p-4 min-w-[280px] cursor-pointer hover:bg-border transition-colors border border-border shrink-0"
      onClick={() => navigate('/predictions')}
    >
      <div className="flex justify-between items-center mb-4">
        <div className="text-sm font-semibold text-gray-400">
          {quarter} <span className="mx-1">•</span> {clock}
        </div>
      </div>
      
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 rounded-full bg-gray-800 flex items-center justify-center text-xs font-bold" style={{ backgroundColor: awayTeam.accent }}>
              {awayTeam.abbrev[0]}
            </div>
            <span className="font-bold text-lg">{awayTeam.abbrev}</span>
          </div>
          <span className="font-extrabold text-2xl">{awayScore}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 rounded-full bg-gray-800 flex items-center justify-center text-xs font-bold" style={{ backgroundColor: homeTeam.accent }}>
              {homeTeam.abbrev[0]}
            </div>
            <span className="font-bold text-lg">{homeTeam.abbrev}</span>
          </div>
          <span className="font-extrabold text-2xl">{homeScore}</span>
        </div>
      </div>

      <div className="mt-4 w-full bg-gray-800 h-1.5 rounded-full overflow-hidden flex">
        <div 
          className="h-full transition-all duration-1000"
          style={{ width: `${winProbHome}%`, backgroundColor: homeAccent }}
        />
      </div>
      <div className="mt-1 text-[10px] text-gray-500 text-center uppercase tracking-widest">
        Win Probability
      </div>
    </div>
  );
}
