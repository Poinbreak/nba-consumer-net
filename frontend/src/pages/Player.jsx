import React, { useState, useEffect } from 'react';
import { Search, AlertCircle } from 'lucide-react';
import { usePlayerStats, usePlayerSearch } from '../hooks/useLiveScore';

const StatPill = ({ label, value, accent }) => (
  <div className="flex flex-col items-end">
    <div className="text-5xl md:text-6xl font-extrabold tracking-tighter" style={{ color: accent }}>{value}</div>
    <div className="text-xs font-semibold text-gray-500 uppercase tracking-widest mt-1">{label}</div>
  </div>
);

// game_date is a date-only string (YYYY-MM-DD); build a local Date to avoid UTC-midnight shifting it a day
function formatGameDate(dateStr) {
  if (!dateStr) return '';
  const [y, m, d] = dateStr.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString();
}

export default function Player() {
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [activeTab, setActiveTab] = useState('Overview');

  const tabs = ['Overview', 'Game Log', 'Splits', 'Props'];

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const { data: searchData, isFetching: searching } = usePlayerSearch(debouncedQuery);
  const searchResults = searchData?.results || [];

  const { data: playerData, isLoading: loading, isError, error } = usePlayerStats(selectedPlayer?.player_id);

  const handleSelectPlayer = (player) => {
    setSelectedPlayer(player);
    setSearchQuery('');
    setDebouncedQuery('');
  };

  if (!selectedPlayer) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold mb-8">Search Players</h1>

        <div className="relative mb-8">
          <div className="relative">
            <Search className="absolute left-4 top-3.5 text-gray-500" size={20} />
            <input
              type="text"
              placeholder="Search by player name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-surface border border-border rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-white"
            />
          </div>

          {searching && (
            <div className="absolute right-4 top-3.5">
              <div className="animate-spin">⏳</div>
            </div>
          )}
        </div>

        {searchResults.length > 0 && (
          <div className="grid grid-cols-1 gap-2 mb-8">
            {searchResults.map(player => (
              <button
                key={player.player_id}
                onClick={() => handleSelectPlayer(player)}
                className="w-full text-left p-4 bg-surface border border-border rounded-xl hover:border-white transition-colors group"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-lg text-white">{player.full_name}</h3>
                    <p className="text-sm text-gray-400">{player.position} • {player.team_abbrev}</p>
                  </div>
                  <span className="text-gray-500 group-hover:text-white transition-colors">→</span>
                </div>
              </button>
            ))}
          </div>
        )}

        {debouncedQuery.length >= 2 && searchResults.length === 0 && !searching && (
          <div className="text-center py-12 text-gray-400">
            <AlertCircle className="mx-auto mb-4 opacity-50" size={32} />
            <p>No players found. Try another search.</p>
          </div>
        )}
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-12 text-center">
        <div className="animate-pulse">Loading player data...</div>
      </div>
    );
  }

  if (isError || !playerData) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-12">
        <button
          onClick={() => setSelectedPlayer(null)}
          className="mb-8 px-4 py-2 bg-surface border border-border rounded-xl hover:border-white transition-colors"
        >
          ← Back to Search
        </button>
        <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-6 text-red-400">
          {error?.response?.data?.error || error?.message || 'Failed to load player data'}
        </div>
      </div>
    );
  }

  const player = playerData.player;
  const avgs = playerData.season_avgs || {};
  const gameLogs = playerData.game_log || [];
  const teamAccent = playerData.team_meta?.accent || '#6c63ff';

  // Format position abbreviation for headshot: a single position shows in full (e.g. "PG"),
  // hybrid positions condense to initials (e.g. "PG/SG" -> "PS")
  const posParts = (player?.position || '').split('/').map(p => p.trim()).filter(Boolean);
  const posInitials = posParts.length > 1 ? posParts.map(p => p.substring(0, 1)).join('') : (posParts[0] || '');

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      {/* Back button */}
      <button
        onClick={() => setSelectedPlayer(null)}
        className="mb-8 px-4 py-2 bg-surface border border-border rounded-xl hover:border-white transition-colors text-sm"
      >
        ← Back to Search
      </button>

      {/* Player Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-16 border-b border-border pb-8 gap-6">
        <div className="flex items-center gap-6 flex-1">
          <div
            className="w-32 h-32 md:w-48 md:h-48 rounded-full flex items-center justify-center text-5xl font-black shadow-2xl flex-shrink-0"
            style={{ background: `linear-gradient(135deg, ${teamAccent}66, ${teamAccent}22)`, color: teamAccent }}
          >
            {posInitials || player?.full_name?.substring(0, 2).toUpperCase()}
          </div>
          <div>
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tighter mb-2">{player?.full_name}</h1>
            <div className="text-xl md:text-2xl font-semibold text-gray-400">
              {playerData.team_meta?.abbrev} • #{player?.jersey_number || '?'} • {player?.position}
            </div>
          </div>
        </div>

        {/* Stat Pills */}
        <div className="flex gap-6 md:gap-10 flex-wrap">
          <StatPill label="PTS" value={(avgs.pts_avg || 0).toFixed(1)} accent={teamAccent} />
          <StatPill label="REB" value={(avgs.reb_avg || 0).toFixed(1)} accent={teamAccent} />
          <StatPill label="AST" value={(avgs.ast_avg || 0).toFixed(1)} accent={teamAccent} />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-8 mb-10 border-b border-border overflow-x-auto">
        {tabs.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-4 font-bold text-lg transition-colors relative whitespace-nowrap ${activeTab === tab ? 'text-white' : 'text-gray-500 hover:text-gray-300'}`}
          >
            {tab}
            {activeTab === tab && (
              <div className="absolute bottom-0 left-0 w-full h-1 rounded-t-full" style={{ background: teamAccent }} />
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'Overview' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-2 bg-surface border border-border p-8 rounded-2xl">
            <h3 className="font-bold text-xl mb-6">Season Stats</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
              <div>
                <div className="text-3xl font-bold" style={{ color: teamAccent }}>{(avgs.pts_avg || 0).toFixed(1)}</div>
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Points Per Game</div>
              </div>
              <div>
                <div className="text-3xl font-bold" style={{ color: teamAccent }}>{(avgs.reb_avg || 0).toFixed(1)}</div>
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Rebounds Per Game</div>
              </div>
              <div>
                <div className="text-3xl font-bold" style={{ color: teamAccent }}>{(avgs.ast_avg || 0).toFixed(1)}</div>
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Assists Per Game</div>
              </div>
              <div>
                <div className="text-3xl font-bold" style={{ color: teamAccent }}>{((avgs.fg_pct_avg || 0) * 100).toFixed(1)}%</div>
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">FG Percentage</div>
              </div>
              <div>
                <div className="text-3xl font-bold" style={{ color: teamAccent }}>{((avgs.fg3_pct_avg || 0) * 100).toFixed(1)}%</div>
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">3P Percentage</div>
              </div>
              <div>
                <div className="text-3xl font-bold" style={{ color: teamAccent }}>{(avgs.games_played || 0)}</div>
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Games Played</div>
              </div>
            </div>
          </div>
          <div className="bg-surface border border-border p-8 rounded-2xl">
            <h3 className="font-bold text-xl mb-4">Player Info</h3>
            <div className="space-y-4 text-sm">
              <div>
                <div className="text-gray-500 uppercase text-xs font-bold tracking-widest">Position</div>
                <div className="font-semibold">{player?.position || 'N/A'}</div>
              </div>
              <div>
                <div className="text-gray-500 uppercase text-xs font-bold tracking-widest">Jersey Number</div>
                <div className="font-semibold">#{player?.jersey_number || '?'}</div>
              </div>
              <div>
                <div className="text-gray-500 uppercase text-xs font-bold tracking-widest">Age</div>
                <div className="font-semibold">{player?.age || 'N/A'}</div>
              </div>
              <div>
                <div className="text-gray-500 uppercase text-xs font-bold tracking-widest">Team</div>
                <div className="font-semibold">{playerData.team_meta?.name || 'N/A'}</div>
              </div>
              <div>
                <div className="text-gray-500 uppercase text-xs font-bold tracking-widest">Status</div>
                <div className="font-semibold">{player?.is_active ? 'Active' : 'Inactive'}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'Game Log' && (
        <div className="overflow-x-auto bg-surface border border-border rounded-2xl">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border text-gray-500 uppercase text-xs tracking-wider">
                <th className="p-4 font-semibold">Date</th>
                <th className="p-4 font-semibold">Opp</th>
                <th className="p-4 font-semibold text-right">MIN</th>
                <th className="p-4 font-semibold text-right">PTS</th>
                <th className="p-4 font-semibold text-right">REB</th>
                <th className="p-4 font-semibold text-right">AST</th>
                <th className="p-4 font-semibold text-right">STL</th>
                <th className="p-4 font-semibold text-right">BLK</th>
                <th className="p-4 font-semibold text-right">FG%</th>
                <th className="p-4 font-semibold text-right">3P%</th>
                <th className="p-4 font-semibold text-right">+/-</th>
              </tr>
            </thead>
            <tbody>
              {gameLogs.map((game, i) => (
                <tr key={i} className="border-b border-border hover:bg-border/50 transition-colors">
                  <td className="p-4 font-semibold text-sm">{formatGameDate(game.game_date)}</td>
                  <td className="p-4 font-semibold text-gray-300 text-sm">{game.is_home ? 'vs' : '@'} {game.opp_abbrev}</td>
                  <td className="p-4 text-right text-gray-400">{Math.round(game.min_played || 0)}</td>
                  <td className={`p-4 text-right font-bold ${game.pts > (avgs.pts_avg || 0) ? 'text-green-400' : 'text-white'}`}>{game.pts}</td>
                  <td className="p-4 text-right font-bold">{game.reb}</td>
                  <td className="p-4 text-right font-bold">{game.ast}</td>
                  <td className="p-4 text-right font-bold">{game.stl}</td>
                  <td className="p-4 text-right font-bold">{game.blk}</td>
                  <td className="p-4 text-right text-gray-300">{((game.fg_pct || 0) * 100).toFixed(1)}%</td>
                  <td className="p-4 text-right text-gray-300">{((game.fg3_pct || 0) * 100).toFixed(1)}%</td>
                  <td className="p-4 text-right font-bold">{game.plus_minus > 0 ? '+' : ''}{game.plus_minus}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'Splits' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-surface border border-border p-8 rounded-2xl">
            <h3 className="font-bold text-xl mb-6">Home vs Away</h3>
            <div className="space-y-4 text-sm">
              <div className="flex justify-between items-center pb-4 border-b border-border">
                <span className="text-gray-400">Home Games</span>
                <span className="font-bold">{gameLogs.filter(g => g.is_home).length}</span>
              </div>
              <div className="flex justify-between items-center pb-4 border-b border-border">
                <span className="text-gray-400">Away Games</span>
                <span className="font-bold">{gameLogs.filter(g => !g.is_home).length}</span>
              </div>
            </div>
          </div>
          <div className="bg-surface border border-border p-8 rounded-2xl">
            <h3 className="font-bold text-xl mb-6">W-L Record</h3>
            <div className="space-y-4 text-sm">
              <div className="flex justify-between items-center pb-4 border-b border-border">
                <span className="text-gray-400 flex items-center gap-2">
                  <span className="text-green-400">●</span> Wins
                </span>
                <span className="font-bold text-green-400">{gameLogs.filter(g => g.win).length}</span>
              </div>
              <div className="flex justify-between items-center pb-4">
                <span className="text-gray-400 flex items-center gap-2">
                  <span className="text-red-400">●</span> Losses
                </span>
                <span className="font-bold text-red-400">{gameLogs.filter(g => !g.win).length}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'Props' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-surface border border-border p-6 rounded-2xl">
            <div className="text-gray-500 uppercase text-xs font-bold tracking-widest mb-2">Points Over/Under</div>
            <div className="text-3xl font-bold" style={{ color: teamAccent }}>{(avgs.pts_avg || 0).toFixed(1)}</div>
            <div className="text-xs text-gray-400 mt-2">Season Average: {(avgs.pts_avg || 0).toFixed(1)} PPG</div>
          </div>
          <div className="bg-surface border border-border p-6 rounded-2xl">
            <div className="text-gray-500 uppercase text-xs font-bold tracking-widest mb-2">Rebounds Over/Under</div>
            <div className="text-3xl font-bold" style={{ color: teamAccent }}>{(avgs.reb_avg || 0).toFixed(1)}</div>
            <div className="text-xs text-gray-400 mt-2">Season Average: {(avgs.reb_avg || 0).toFixed(1)} RPG</div>
          </div>
          <div className="bg-surface border border-border p-6 rounded-2xl">
            <div className="text-gray-500 uppercase text-xs font-bold tracking-widest mb-2">Assists Over/Under</div>
            <div className="text-3xl font-bold" style={{ color: teamAccent }}>{(avgs.ast_avg || 0).toFixed(1)}</div>
            <div className="text-xs text-gray-400 mt-2">Season Average: {(avgs.ast_avg || 0).toFixed(1)} APG</div>
          </div>
        </div>
      )}
    </div>
  );
}
