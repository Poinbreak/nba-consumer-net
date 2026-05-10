import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart2, TrendingUp, Shield, Zap } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts';

const TEAMS = [
  { id: 1610612747, abbrev: 'LAL', name: 'Los Angeles Lakers',  accent: '#552583', conf: 'Western', record: '47-35', net: '+2.4' },
  { id: 1610612738, abbrev: 'BOS', name: 'Boston Celtics',      accent: '#007A33', conf: 'Eastern', record: '64-18', net: '+9.8' },
  { id: 1610612743, abbrev: 'DEN', name: 'Denver Nuggets',      accent: '#0E2240', conf: 'Western', record: '57-25', net: '+6.1' },
  { id: 1610612760, abbrev: 'OKC', name: 'Oklahoma City Thunder',accent: '#007AC1', conf: 'Western', record: '68-14', net: '+11.3' },
  { id: 1610612759, abbrev: 'SAS', name: 'San Antonio Spurs',   accent: '#C4CED4', conf: 'Western', record: '40-42', net: '-3.1' },
];

const MOCK_STATS = {
  off_rating: 118.4, def_rating: 114.2, pace: 99.6, ts_pct: 59.2, ast_ratio: 17.8,
  efg_pct: 56.1,
};

const RADAR_DATA = [
  { stat: 'Off Rtg',  value: 85 },
  { stat: 'Def Rtg',  value: 72 },
  { stat: 'Pace',     value: 68 },
  { stat: 'eFG%',     value: 80 },
  { stat: 'AST%',     value: 75 },
  { stat: 'TOV%',     value: 65 },
];

const ROSTER = [
  { name: 'LeBron James',    pos: 'SF', age: 39, pts: 25.7, reb: 7.3, ast: 8.3, salary: '$47.6M' },
  { name: 'Anthony Davis',   pos: 'C',  age: 31, pts: 24.7, reb: 12.6, ast: 3.5, salary: '$40.6M' },
  { name: "D'Angelo Russell", pos: 'PG', age: 28, pts: 14.3, reb: 2.8, ast: 6.3, salary: '$17.3M' },
  { name: 'Austin Reaves',   pos: 'SG', age: 25, pts: 15.9, reb: 4.3, ast: 5.5, salary: '$12.0M' },
  { name: 'Rui Hachimura',   pos: 'PF', age: 26, pts: 13.0, reb: 4.4, ast: 1.1, salary: '$17.0M' },
];

const statBoxes = [
  { label: 'Off Rating', value: MOCK_STATS.off_rating.toFixed(1), icon: TrendingUp, color: '#6c63ff' },
  { label: 'Def Rating', value: MOCK_STATS.def_rating.toFixed(1), icon: Shield,     color: '#22c55e' },
  { label: 'Pace',       value: MOCK_STATS.pace.toFixed(1),       icon: Zap,        color: '#f59e0b' },
  { label: 'eFG%',       value: `${MOCK_STATS.efg_pct.toFixed(1)}%`, icon: BarChart2, color: '#ec4899' },
];

export default function Team() {
  const [selected, setSelected] = useState(TEAMS[0]);

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      {/* Team selector strip */}
      <div className="flex gap-3 overflow-x-auto scrollbar-hide pb-4 mb-10">
        {TEAMS.map(t => (
          <button
            key={t.id}
            onClick={() => setSelected(t)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold whitespace-nowrap transition-all ${
              selected.id === t.id
                ? 'text-white scale-105'
                : 'glass-lighter text-gray-400 hover:text-white'
            }`}
            style={selected.id === t.id ? { background: t.accent + '33', border: `1px solid ${t.accent}55`, color: t.accent } : {}}
          >
            <span className="w-5 h-5 rounded-md flex items-center justify-center text-xs font-black"
              style={{ background: t.accent, color: '#fff' }}>
              {t.abbrev[0]}
            </span>
            {t.abbrev}
          </button>
        ))}
      </div>

      {/* Team header */}
      <motion.div
        key={selected.id}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row items-start md:items-end justify-between gap-6 pb-8 mb-10 border-b border-white/5"
      >
        <div className="flex items-center gap-6">
          <div
            className="w-24 h-24 rounded-2xl flex items-center justify-center text-3xl font-black shadow-2xl"
            style={{ background: `linear-gradient(135deg, ${selected.accent}66, ${selected.accent}22)`, color: selected.accent, border: `1px solid ${selected.accent}44` }}
          >
            {selected.abbrev}
          </div>
          <div>
            <h1 className="text-4xl md:text-5xl font-black tracking-tighter mb-1">{selected.name}</h1>
            <div className="flex items-center gap-3 text-gray-500 font-semibold">
              <span>{selected.record}</span>
              <span>·</span>
              <span>{selected.conf}</span>
              <span>·</span>
              <span className={selected.net.startsWith('+') ? 'text-green-400' : 'text-red-400'}>
                Net {selected.net}
              </span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Stat boxes */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        {statBoxes.map(s => (
          <div key={s.label} className="glass rounded-2xl p-5 card-hover">
            <s.icon size={16} style={{ color: s.color }} className="mb-3" />
            <div className="text-2xl font-black mb-0.5" style={{ color: s.color }}>{s.value}</div>
            <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Roster table */}
        <div className="lg:col-span-2 glass rounded-2xl overflow-hidden">
          <div className="px-6 py-4 border-b border-white/5">
            <h2 className="font-bold text-lg">Roster</h2>
          </div>
          <table className="w-full text-left">
            <thead>
              <tr className="text-[10px] font-bold uppercase tracking-widest text-gray-600 border-b border-white/5">
                <th className="px-6 py-3">Player</th>
                <th className="px-4 py-3">Pos</th>
                <th className="px-4 py-3 text-right">PTS</th>
                <th className="px-4 py-3 text-right">REB</th>
                <th className="px-4 py-3 text-right">AST</th>
                <th className="px-4 py-3 text-right">Salary</th>
              </tr>
            </thead>
            <tbody>
              {ROSTER.map(p => (
                <tr key={p.name} className="stat-row border-b border-white/5 last:border-0">
                  <td className="px-6 py-3 font-bold text-sm">{p.name}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs font-bold">{p.pos}</td>
                  <td className="px-4 py-3 text-right font-extrabold" style={{ color: selected.accent }}>{p.pts}</td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-400">{p.reb}</td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-400">{p.ast}</td>
                  <td className="px-4 py-3 text-right font-bold text-gray-300 text-xs">{p.salary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Radar chart */}
        <div className="glass rounded-2xl p-6">
          <h2 className="font-bold text-lg mb-4">Team Radar</h2>
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={RADAR_DATA} cx="50%" cy="50%" outerRadius="70%">
              <PolarGrid stroke="#23232f" />
              <PolarAngleAxis dataKey="stat" tick={{ fill: '#6b7280', fontSize: 11, fontWeight: 600 }} />
              <Radar dataKey="value" stroke={selected.accent} fill={selected.accent} fillOpacity={0.2} strokeWidth={2} />
              <Tooltip
                contentStyle={{ background: '#15151f', border: '1px solid #23232f', borderRadius: 12 }}
                itemStyle={{ color: '#fff' }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
