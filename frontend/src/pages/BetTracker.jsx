import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function BetTracker() {
  const chartData = [
    { date: '10/01', pnl: -50 },
    { date: '10/05', pnl: 120 },
    { date: '10/10', pnl: 45 },
    { date: '10/15', pnl: 230 },
    { date: '10/20', pnl: 180 },
    { date: '10/25', pnl: 410 },
    { date: '10/30', pnl: 350 }
  ];

  const activeBets = [
    { id: 1, game: 'LAL @ DEN', type: 'Spread', direction: 'DEN -4.5', stake: 100, odds: -110, potential: 190.90, edge: 4.2, status: 'pending' },
    { id: 2, game: 'BOS vs MIA', type: 'Prop (PTS)', direction: 'Tatum Over 26.5', stake: 50, odds: -115, potential: 93.47, edge: 6.8, status: 'won' },
    { id: 3, game: 'GSW @ PHX', type: 'Moneyline', direction: 'PHX', stake: 200, odds: +130, potential: 460.00, edge: -1.5, status: 'lost' },
  ];

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <div className="flex justify-between items-end mb-12">
        <div>
          <h1 className="text-5xl font-extrabold tracking-tighter mb-2">Bet Tracker</h1>
          <p className="text-xl text-gray-400 font-semibold">Your performance vs the bookmakers.</p>
        </div>
        <button className="bg-white text-black font-bold py-2 px-6 rounded-full hover:bg-gray-200 transition-colors">
          Place Bet
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
        <div className="bg-surface border border-border rounded-xl p-6">
          <div className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-2">Net P&L</div>
          <div className="text-4xl font-extrabold text-green-400">+$350.00</div>
        </div>
        <div className="bg-surface border border-border rounded-xl p-6">
          <div className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-2">Win Rate</div>
          <div className="text-4xl font-extrabold text-white">58.4%</div>
        </div>
        <div className="bg-surface border border-border rounded-xl p-6">
          <div className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-2">Total Bets</div>
          <div className="text-4xl font-extrabold text-white">142</div>
        </div>
        <div className="bg-surface border border-border rounded-xl p-6">
          <div className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-2">ROI</div>
          <div className="text-4xl font-extrabold text-green-400">+8.2%</div>
        </div>
      </div>

      {/* P&L Chart */}
      <div className="bg-surface border border-border rounded-xl p-6 mb-12 h-80">
        <div className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-6">30-Day P&L</div>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4ade80" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#4ade80" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <XAxis dataKey="date" stroke="#52525b" tick={{fill: '#a1a1aa', fontSize: 12}} tickLine={false} axisLine={false} />
            <YAxis stroke="#52525b" tick={{fill: '#a1a1aa', fontSize: 12}} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1a1a1b', borderColor: '#2a2a2b', borderRadius: '8px' }}
              itemStyle={{ color: '#fff', fontWeight: 'bold' }}
            />
            <Area type="monotone" dataKey="pnl" stroke="#4ade80" strokeWidth={3} fillOpacity={1} fill="url(#colorPnl)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Active Bets Table */}
      <h3 className="text-2xl font-bold mb-6">Recent Bets</h3>
      <div className="overflow-x-auto bg-surface border border-border rounded-xl">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-border text-gray-500 uppercase text-xs tracking-wider">
              <th className="p-4 font-semibold">Game</th>
              <th className="p-4 font-semibold">Type</th>
              <th className="p-4 font-semibold">Direction</th>
              <th className="p-4 font-semibold text-right">Stake</th>
              <th className="p-4 font-semibold text-right">Odds</th>
              <th className="p-4 font-semibold text-right">Edge</th>
              <th className="p-4 font-semibold text-center">Status</th>
            </tr>
          </thead>
          <tbody>
            {activeBets.map((bet) => (
              <tr key={bet.id} className="border-b border-border hover:bg-border/50 transition-colors">
                <td className="p-4 font-bold">{bet.game}</td>
                <td className="p-4 font-semibold text-gray-400">{bet.type}</td>
                <td className="p-4 font-bold text-white">{bet.direction}</td>
                <td className="p-4 text-right font-bold">${bet.stake}</td>
                <td className="p-4 text-right font-semibold text-gray-300">{bet.odds > 0 ? `+${bet.odds}` : bet.odds}</td>
                <td className={`p-4 text-right font-bold ${bet.edge > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {bet.edge > 0 ? '+' : ''}{bet.edge}%
                </td>
                <td className="p-4 text-center">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                    bet.status === 'won' ? 'bg-green-400/20 text-green-400' :
                    bet.status === 'lost' ? 'bg-red-400/20 text-red-400' :
                    'bg-yellow-400/20 text-yellow-400'
                  }`}>
                    {bet.status.toUpperCase()}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
