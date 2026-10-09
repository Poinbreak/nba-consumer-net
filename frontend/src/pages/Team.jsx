import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart2, TrendingUp, Shield, Zap } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts';
import { useTeamStats } from '../hooks/useLiveScore';

// All NBA Teams with their metadata
const ALL_TEAMS = [
  { id: 1610612737, abbrev: 'ATL', name: 'Atlanta Hawks',           accent: '#E03A3E' },
  { id: 1610612738, abbrev: 'BOS', name: 'Boston Celtics',          accent: '#007A33' },
  { id: 1610612739, abbrev: 'CLE', name: 'Cleveland Cavaliers',     accent: '#860038' },
  { id: 1610612740, abbrev: 'NOP', name: 'New Orleans Pelicans',    accent: '#0C2340' },
  { id: 1610612741, abbrev: 'CHI', name: 'Chicago Bulls',           accent: '#CE1141' },
  { id: 1610612742, abbrev: 'DAL', name: 'Dallas Mavericks',        accent: '#00538C' },
  { id: 1610612743, abbrev: 'DEN', name: 'Denver Nuggets',          accent: '#0E2240' },
  { id: 1610612744, abbrev: 'GSW', name: 'Golden State Warriors',   accent: '#1D428A' },
  { id: 1610612745, abbrev: 'HOU', name: 'Houston Rockets',         accent: '#CE1141' },
  { id: 1610612746, abbrev: 'LAC', name: 'LA Clippers',             accent: '#C8102E' },
  { id: 1610612747, abbrev: 'LAL', name: 'Los Angeles Lakers',      accent: '#552583' },
  { id: 1610612748, abbrev: 'MIA', name: 'Miami Heat',              accent: '#98002E' },
  { id: 1610612749, abbrev: 'MIL', name: 'Milwaukee Bucks',         accent: '#00471B' },
  { id: 1610612750, abbrev: 'MIN', name: 'Minnesota Timberwolves',  accent: '#0C2340' },
  { id: 1610612751, abbrev: 'BKN', name: 'Brooklyn Nets',           accent: '#000000' },
  { id: 1610612752, abbrev: 'NYK', name: 'New York Knicks',         accent: '#006BB6' },
  { id: 1610612753, abbrev: 'ORL', name: 'Orlando Magic',           accent: '#0077C0' },
  { id: 1610612754, abbrev: 'IND', name: 'Indiana Pacers',          accent: '#002D62' },
  { id: 1610612755, abbrev: 'PHI', name: 'Philadelphia 76ers',      accent: '#006BB6' },
  { id: 1610612756, abbrev: 'PHX', name: 'Phoenix Suns',            accent: '#1D1160' },
  { id: 1610612757, abbrev: 'POR', name: 'Portland Trail Blazers',  accent: '#E03A3E' },
  { id: 1610612758, abbrev: 'SAC', name: 'Sacramento Kings',        accent: '#5A2D81' },
  { id: 1610612759, abbrev: 'SAS', name: 'San Antonio Spurs',       accent: '#C4CED4' },
  { id: 1610612760, abbrev: 'OKC', name: 'Oklahoma City Thunder',   accent: '#007AC1' },
  { id: 1610612761, abbrev: 'TOR', name: 'Toronto Raptors',         accent: '#CE1141' },
  { id: 1610612762, abbrev: 'UTA', name: 'Utah Jazz',               accent: '#002B5C' },
  { id: 1610612763, abbrev: 'MEM', name: 'Memphis Grizzlies',       accent: '#5D76A9' },
  { id: 1610612764, abbrev: 'WAS', name: 'Washington Wizards',      accent: '#002B5C' },
  { id: 1610612765, abbrev: 'DET', name: 'Detroit Pistons',         accent: '#C8102E' },
  { id: 1610612766, abbrev: 'CHA', name: 'Charlotte Hornets',       accent: '#1D1160' },
];

// Scale each real season-avg stat onto a 0-100 radar axis so the shape actually differs per team
const RADAR_METRICS = [
  { stat: 'PTS',     key: 'pts_avg',     max: 130 },
  { stat: 'REB',     key: 'reb_avg',     max: 50 },
  { stat: 'AST',     key: 'ast_avg',     max: 30 },
  { stat: 'eFG%',    key: 'efg_pct_avg', max: 0.60, scale: 100 },
  { stat: 'FT Rate', key: 'ft_rate_avg', max: 0.30, scale: 100 },
  { stat: 'TOV%',    key: 'tov_pct_avg', max: 0.20, scale: 100, invert: true },
];

function buildRadarData(avgs) {
  return RADAR_METRICS.map(m => {
    const raw = (avgs[m.key] || 0) * (m.scale || 1);
    const max = m.max * (m.scale || 1);
    const pct = max > 0 ? Math.min(100, Math.max(0, (raw / max) * 100)) : 0;
    return { stat: m.stat, value: Math.round(m.invert ? 100 - pct : pct) };
  });
}

// game_date is a date-only string (YYYY-MM-DD); build a local Date to avoid UTC-midnight shifting it a day
function formatGameDate(dateStr) {
  if (!dateStr) return '';
  const [y, m, d] = dateStr.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString();
}

export default function Team() {
  const [selectedTeam, setSelectedTeam] = useState(ALL_TEAMS[0]);
  const { data: teamData, isLoading: loading, isError, error } = useTeamStats(selectedTeam?.id);

  const avgs = teamData?.season_avgs || {};
  const lastTen = teamData?.last_10 || [];
  const wins = lastTen.filter(g => g.win).length;
  const losses = lastTen.length - wins;
  const winPct = avgs.games_played ? (avgs.wins / avgs.games_played) * 100 : 0;
  const avgPointDiff = lastTen.length
    ? lastTen.reduce((sum, g) => sum + ((g.pts || 0) - (g.opp_pts || 0)), 0) / lastTen.length
    : 0;

  const statBoxes = [
    { label: 'Win %',   value: `${winPct.toFixed(1)}%`, icon: TrendingUp, color: '#6c63ff' },
    { label: 'eFG%',    value: `${((avgs.efg_pct_avg || 0) * 100).toFixed(1)}%`, icon: BarChart2, color: '#ec4899' },
    { label: 'TOV%',    value: `${((avgs.tov_pct_avg || 0) * 100).toFixed(1)}%`, icon: Zap, color: '#f59e0b' },
    { label: 'FT Rate', value: `${((avgs.ft_rate_avg || 0) * 100).toFixed(1)}%`, icon: Shield, color: '#22c55e' },
  ];

  const radarData = buildRadarData(avgs);

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      {/* Team selector grid */}
      <div className="mb-10">
        <h2 className="text-lg font-bold mb-4">Select a Team</h2>
        <div className="grid grid-cols-3 md:grid-cols-6 lg:grid-cols-10 gap-2">
          {ALL_TEAMS.map(t => (
            <button
              key={t.id}
              onClick={() => setSelectedTeam(t)}
              className={`flex items-center justify-center w-full aspect-square rounded-xl text-xs font-black whitespace-nowrap transition-all ${
                selectedTeam.id === t.id
                  ? 'ring-2 ring-offset-2 scale-105'
                  : 'hover:scale-105 opacity-70 hover:opacity-100'
              }`}
              style={selectedTeam.id === t.id ? { background: t.accent, color: '#fff', '--tw-ring-color': t.accent } : { background: t.accent + '22', color: t.accent }}
              title={t.name}
            >
              {t.abbrev.substring(0, 1)}
            </button>
          ))}
        </div>
      </div>

      {/* Team header */}
      <motion.div
        key={selectedTeam.id}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row items-start md:items-end justify-between gap-6 pb-8 mb-10 border-b border-white/5"
      >
        <div className="flex items-center gap-6 flex-1">
          <div
            className="w-24 h-24 rounded-2xl flex items-center justify-center text-3xl font-black shadow-2xl flex-shrink-0"
            style={{ background: `linear-gradient(135deg, ${selectedTeam.accent}66, ${selectedTeam.accent}22)`, color: selectedTeam.accent, border: `1px solid ${selectedTeam.accent}44` }}
          >
            {selectedTeam.abbrev}
          </div>
          <div>
            <h1 className="text-4xl md:text-5xl font-black tracking-tighter mb-1">{selectedTeam.name}</h1>
            <div className="flex items-center gap-3 text-gray-500 font-semibold text-sm md:text-base">
              <span>{wins}-{losses}</span>
              <span>·</span>
              <span className={avgPointDiff >= 0 ? 'text-green-400' : 'text-red-400'}>
                L10 Diff {avgPointDiff >= 0 ? '+' : ''}{avgPointDiff.toFixed(1)}
              </span>
            </div>
          </div>
        </div>
      </motion.div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">
          <div className="animate-pulse">Loading team data...</div>
        </div>
      ) : isError ? (
        <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-6 text-red-400">
          {error?.response?.data?.error || error?.message || 'Failed to load team data'}
        </div>
      ) : (
        <>
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
            {/* Last 10 Games */}
            <div className="lg:col-span-2 glass rounded-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-white/5">
                <h2 className="font-bold text-lg">Last 10 Games</h2>
              </div>
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="text-[10px] font-bold uppercase tracking-widest text-gray-600 border-b border-white/5">
                    <th className="px-6 py-3">Date</th>
                    <th className="px-4 py-3">Opp</th>
                    <th className="px-4 py-3 text-right">W/L</th>
                    <th className="px-4 py-3 text-right">PTS</th>
                    <th className="px-4 py-3 text-right">OPP</th>
                    <th className="px-4 py-3 text-right">AST</th>
                    <th className="px-4 py-3 text-right">REB</th>
                    <th className="px-4 py-3 text-right">FG%</th>
                  </tr>
                </thead>
                <tbody>
                  {lastTen.map((g, i) => (
                    <tr key={i} className="stat-row border-b border-white/5 last:border-0">
                      <td className="px-6 py-3 font-bold text-xs">{formatGameDate(g.game_date)}</td>
                      <td className="px-4 py-3 text-gray-500 text-xs font-bold">{g.is_home ? 'vs' : '@'} {g.opp_abbrev}</td>
                      <td className={`px-4 py-3 text-right font-extrabold text-sm ${g.win ? 'text-green-400' : 'text-red-400'}`}>
                        {g.win ? 'W' : 'L'}
                      </td>
                      <td className="px-4 py-3 text-right font-extrabold" style={{ color: selectedTeam.accent }}>{g.pts}</td>
                      <td className="px-4 py-3 text-right font-semibold text-gray-400">{g.opp_pts}</td>
                      <td className="px-4 py-3 text-right font-semibold text-gray-400">{g.ast}</td>
                      <td className="px-4 py-3 text-right font-semibold text-gray-400">{g.reb}</td>
                      <td className="px-4 py-3 text-right text-gray-300">{((g.fg_pct || 0) * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Team Stats Card */}
            <div className="glass rounded-2xl p-6">
              <h2 className="font-bold text-lg mb-6">Season Stats</h2>
              <div className="space-y-4 text-sm">
                <div className="flex justify-between items-center pb-4 border-b border-white/5">
                  <span className="text-gray-400">eFG%</span>
                  <span className="font-bold">{((avgs.efg_pct_avg || 0) * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-white/5">
                  <span className="text-gray-400">TOV%</span>
                  <span className="font-bold">{((avgs.tov_pct_avg || 0) * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-white/5">
                  <span className="text-gray-400">PTS/Game</span>
                  <span className="font-bold">{(avgs.pts_avg || 0).toFixed(1)}</span>
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-white/5">
                  <span className="text-gray-400">AST/Game</span>
                  <span className="font-bold">{(avgs.ast_avg || 0).toFixed(1)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">REB/Game</span>
                  <span className="font-bold">{(avgs.reb_avg || 0).toFixed(1)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Radar Chart */}
          <div className="glass rounded-2xl p-6 mt-6">
            <h2 className="font-bold text-lg mb-4">Team Radar</h2>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
                <PolarGrid stroke="#23232f" />
                <PolarAngleAxis dataKey="stat" tick={{ fill: '#6b7280', fontSize: 11, fontWeight: 600 }} />
                <Radar dataKey="value" stroke={selectedTeam.accent} fill={selectedTeam.accent} fillOpacity={0.2} strokeWidth={2} />
                <Tooltip contentStyle={{ backgroundColor: '#1a1a1f', border: `1px solid ${selectedTeam.accent}`, borderRadius: 12 }} itemStyle={{ color: '#fff' }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
