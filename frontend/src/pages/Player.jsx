import React, { useState } from 'react';

const StatPill = ({ label, value }) => (
  <div className="flex flex-col items-end">
    <div className="text-5xl md:text-6xl font-extrabold tracking-tighter">{value}</div>
    <div className="text-xs font-semibold text-gray-500 uppercase tracking-widest mt-1">{label}</div>
  </div>
);

export default function Player() {
  const [activeTab, setActiveTab] = useState('Overview');

  const tabs = ['Overview', 'Game Log', 'Splits', 'Props', 'Compare'];

  const gameLog = [
    { date: 'Nov 12', opp: '@ PHX', min: '34', pts: 32, reb: 11, ast: 6, fg: '54.2', pm: '+12' },
    { date: 'Nov 10', opp: 'vs DAL', min: '36', pts: 28, reb: 9, ast: 8, fg: '48.5', pm: '+5' },
    { date: 'Nov 8', opp: '@ HOU', min: '31', pts: 24, reb: 10, ast: 12, fg: '60.0', pm: '+18' },
  ];

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      {/* Player Header Strip */}
      <div className="flex flex-col md:flex-row justify-between items-center md:items-end mb-16 border-b border-border pb-8">
        <div className="flex items-center mb-8 md:mb-0">
          <div className="w-32 h-32 md:w-48 md:h-48 rounded-full bg-gray-800 overflow-hidden mr-6 md:mr-10">
            {/* Placeholder for headshot */}
            <div className="w-full h-full bg-[#552583] flex items-end justify-center">
              <span className="text-6xl text-white/20 font-bold mb-4">LJ</span>
            </div>
          </div>
          <div>
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tighter mb-2">LeBron James</h1>
            <div className="text-xl md:text-2xl font-semibold text-gray-400">
              LAL • #23 • SF
            </div>
          </div>
        </div>

        {/* Massive Stat Pills */}
        <div className="flex space-x-6 md:space-x-10">
          <StatPill label="PTS" value="25.4" />
          <StatPill label="REB" value="7.8" />
          <StatPill label="AST" value="8.1" />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-8 mb-10 border-b border-border">
        {tabs.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-4 font-bold text-lg transition-colors relative ${activeTab === tab ? 'text-white' : 'text-gray-500 hover:text-gray-300'}`}
          >
            {tab}
            {activeTab === tab && (
              <div className="absolute bottom-0 left-0 w-full h-1 bg-white rounded-t-full" />
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'Overview' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-2 bg-surface border border-border p-8 rounded-2xl">
            <h3 className="font-bold text-xl mb-6">Last 5 Games</h3>
            <div className="h-64 flex items-end justify-between space-x-2">
              {/* Dummy Bar Chart */}
              {[22, 28, 34, 25, 32].map((pts, i) => (
                <div key={i} className="w-full bg-[#552583] hover:opacity-80 transition-opacity rounded-t-md relative group flex justify-center" style={{ height: `${(pts/40)*100}%` }}>
                  <span className="absolute -top-6 text-sm font-bold opacity-0 group-hover:opacity-100 transition-opacity">{pts}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-surface border border-border p-8 rounded-2xl">
            <h3 className="font-bold text-xl mb-2">Model Says Tonight</h3>
            <p className="text-sm text-gray-400 mb-6">vs Denver Nuggets</p>
            
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <span className="font-bold">Points (24.5)</span>
                <span className="text-green-400 font-extrabold flex items-center">
                  26.2 <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 15l7-7 7 7"></path></svg>
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="font-bold">Rebounds (8.5)</span>
                <span className="text-red-400 font-extrabold flex items-center">
                  7.1 <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M19 9l-7 7-7-7"></path></svg>
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="font-bold">Assists (7.5)</span>
                <span className="text-green-400 font-extrabold flex items-center">
                  8.8 <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 15l7-7 7 7"></path></svg>
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'Game Log' && (
        <div className="overflow-x-auto bg-surface border border-border rounded-2xl">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-border text-gray-500 uppercase text-xs tracking-wider">
                <th className="p-4 font-semibold">Date</th>
                <th className="p-4 font-semibold">Opp</th>
                <th className="p-4 font-semibold text-right">MIN</th>
                <th className="p-4 font-semibold text-right">PTS</th>
                <th className="p-4 font-semibold text-right">REB</th>
                <th className="p-4 font-semibold text-right">AST</th>
                <th className="p-4 font-semibold text-right">FG%</th>
                <th className="p-4 font-semibold text-right">+/-</th>
              </tr>
            </thead>
            <tbody>
              {gameLog.map((game, i) => (
                <tr key={i} className="border-b border-border hover:bg-border/50 transition-colors">
                  <td className="p-4 font-semibold">{game.date}</td>
                  <td className="p-4 font-semibold text-gray-300">{game.opp}</td>
                  <td className="p-4 text-right text-gray-400">{game.min}</td>
                  <td className={`p-4 text-right font-bold ${game.pts > 25.4 ? 'text-green-400' : 'text-white'}`}>{game.pts}</td>
                  <td className="p-4 text-right font-bold">{game.reb}</td>
                  <td className="p-4 text-right font-bold">{game.ast}</td>
                  <td className="p-4 text-right text-gray-300">{game.fg}</td>
                  <td className="p-4 text-right font-bold">{game.pm}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
