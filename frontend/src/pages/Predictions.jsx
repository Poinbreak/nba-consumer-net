import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, ChevronDown, ChevronUp, Zap, TrendingUp } from 'lucide-react';
import WinProbabilityGraph from '../components/WinProbabilityGraph';
import { useLiveScore, useGamePrediction, useOdds } from '../hooks/useLiveScore';

const SHAP_COLOR = (v) => (v > 0 ? '#22c55e' : v < 0 ? '#ef4444' : '#6b7280');

function ShapRow({ factor }) {
  const pct = Math.abs(factor.impact * 100);
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-white/5 last:border-0">
      <div className="flex-1">
        <div className="text-xs font-bold text-white/90 mb-0.5">{factor.feature.replace(/_/g, ' ').toUpperCase()}</div>
        <div className="text-[11px] text-gray-500">{factor.description}</div>
      </div>
      <div className="text-right">
        <span className="text-xs font-extrabold" style={{ color: SHAP_COLOR(factor.impact) }}>
          {factor.impact > 0 ? '+' : ''}{factor.impact.toFixed(3)}
        </span>
        <div className="w-20 h-1 rounded-full bg-white/5 mt-1 overflow-hidden">
          <div className="h-full rounded-full"
            style={{ width: `${Math.min(pct * 5, 100)}%`, background: SHAP_COLOR(factor.impact) }} />
        </div>
      </div>
    </div>
  );
}

// Find matching odds from The Odds API by team name fuzzy match
function findOdds(oddsData, homeAbbrev, awayAbbrev) {
  if (!oddsData?.length) return null;
  const ABBREV_TO_FULL = {
    LAL: 'lakers', BOS: 'celtics', DEN: 'nuggets', GSW: 'warriors',
    MIA: 'heat', PHI: '76ers', NYK: 'knicks', MIN: 'timberwolves',
    OKC: 'thunder', SAS: 'spurs', CLE: 'cavaliers', DET: 'pistons',
    TOR: 'raptors', ORL: 'magic',
  };
  const hkw = ABBREV_TO_FULL[homeAbbrev] || homeAbbrev.toLowerCase();
  const akw = ABBREV_TO_FULL[awayAbbrev] || awayAbbrev.toLowerCase();
  return oddsData.find(g =>
    g.home_team.toLowerCase().includes(hkw) &&
    g.away_team.toLowerCase().includes(akw)
  ) || null;
}

function OddsChip({ label, value }) {
  return (
    <div className="glass-lighter rounded-lg px-2.5 py-1.5 text-center">
      <div className="text-[9px] font-bold uppercase tracking-wider text-gray-600 mb-0.5">{label}</div>
      <div className="text-xs font-extrabold text-white">{value}</div>
    </div>
  );
}

function PredictionCard({ game, oddsData }) {
  const [expanded, setExpanded] = useState(false);
  const { data: pred } = useGamePrediction(game.game_id);

  const homeWin = pred ? Math.round(pred.home_win_probability * 100) : game.home_win_prob ?? 50;
  const awayWin = 100 - homeWin;

  // Extract best bookmaker odds (prefer FanDuel)
  const match = findOdds(oddsData, game.home_team_abbrev, game.away_team_abbrev);
  const bookmaker = match?.bookmakers?.find(b => b.key === 'fanduel') || match?.bookmakers?.[0];
  const h2h = bookmaker?.markets?.find(m => m.key === 'h2h');
  const spread = bookmaker?.markets?.find(m => m.key === 'spreads');
  const totals = bookmaker?.markets?.find(m => m.key === 'totals');
  const homeH2H   = h2h?.outcomes?.find(o => o.name === match?.home_team)?.price;
  const awayH2H   = h2h?.outcomes?.find(o => o.name === match?.away_team)?.price;
  const homeSprd  = spread?.outcomes?.find(o => o.name === match?.home_team);
  const overLine  = totals?.outcomes?.find(o => o.name === 'Over');

  return (
    <motion.div layout className="glass rounded-2xl overflow-hidden card-hover gradient-border">
      {/* Status + odds line */}
      <div className="px-6 pt-5 pb-4 border-b border-white/5">
        <div className="flex justify-between items-center mb-4">
          <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
            {game.status === 'Live'
              ? `🔴 Live · Q${game.quarter} ${game.time_remaining}`
              : game.status === 'Final'
              ? `✅ Final · ${game.game_date}`
              : `🗓 Upcoming · ${new Date(game.game_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`
            }
          </span>
          {bookmaker && (
            <span className="text-[9px] font-bold text-gray-600 uppercase tracking-widest">
              via {bookmaker.title}
            </span>
          )}
        </div>

        {/* Teams */}
        <div className="flex items-center justify-between gap-4">
          <div className="text-center flex-1">
            <div className="w-14 h-14 rounded-xl mx-auto mb-2 flex items-center justify-center text-xl font-black"
              style={{ background: (game.away_team_accent || '#ff6b6b') + '22', color: game.away_team_accent, border: `1px solid ${game.away_team_accent}44` }}>
              {game.away_team_abbrev}
            </div>
            <div className="text-2xl font-black">{awayWin}%</div>
            <div className="text-[10px] text-gray-500 font-bold">WIN PROB</div>
            {game.away_score != null && (
              <div className="text-3xl font-black mt-1">{game.away_score}</div>
            )}
          </div>

          <div className="text-center">
            {pred?.predicted_score && game.status !== 'Final' ? (
              <div className="glass-lighter rounded-lg px-3 py-1.5 text-xs font-bold text-gray-400">
                Pred {pred.predicted_score.away}–{pred.predicted_score.home}
              </div>
            ) : <div className="text-xs font-bold text-gray-700">vs</div>}
          </div>

          <div className="text-center flex-1">
            <div className="w-14 h-14 rounded-xl mx-auto mb-2 flex items-center justify-center text-xl font-black"
              style={{ background: (game.home_team_accent || '#6c63ff') + '22', color: game.home_team_accent, border: `1px solid ${game.home_team_accent}44` }}>
              {game.home_team_abbrev}
            </div>
            <div className="text-2xl font-black">{homeWin}%</div>
            <div className="text-[10px] text-gray-500 font-bold">WIN PROB</div>
            {game.home_score != null && (
              <div className="text-3xl font-black mt-1">{game.home_score}</div>
            )}
          </div>
        </div>

        {/* Real betting odds chips */}
        {bookmaker && (
          <div className="flex gap-2 mt-4 justify-center flex-wrap">
            {awayH2H   && <OddsChip label={`${game.away_team_abbrev} ML`} value={awayH2H > 0 ? `+${awayH2H}` : awayH2H} />}
            {homeH2H   && <OddsChip label={`${game.home_team_abbrev} ML`} value={homeH2H > 0 ? `+${homeH2H}` : homeH2H} />}
            {homeSprd  && <OddsChip label="Spread" value={`${homeSprd.point > 0 ? '+' : ''}${homeSprd.point}`} />}
            {overLine  && <OddsChip label="O/U" value={overLine.point} />}
          </div>
        )}
      </div>

      {/* Win prob graph */}
      <div className="p-4">
        <WinProbabilityGraph
          gameId={game.game_id}
          homeAbbrev={game.home_team_abbrev}
          awayAbbrev={game.away_team_abbrev}
          homeColor={game.home_team_accent || '#6c63ff'}
          awayColor={game.away_team_accent || '#ff6b6b'}
          initialProb={homeWin / 100}
          isLive={game.status === 'Live'}
        />
      </div>

      {/* SHAP factors accordion */}
      {pred?.shap_factors?.length > 0 && (
        <>
          <button
            onClick={() => setExpanded(v => !v)}
            className="w-full flex items-center justify-center gap-2 py-3 text-xs font-bold text-gray-500 hover:text-white transition-colors border-t border-white/5"
          >
            <Zap size={12} className="text-yellow-400" />
            AI Key Factors
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden px-6 pb-4"
              >
                {pred.shap_factors.map(f => <ShapRow key={f.feature} factor={f} />)}
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </motion.div>
  );
}

export default function Predictions() {
  const { data: scoreData, isLoading: scoresLoading } = useLiveScore();
  const { data: oddsData } = useOdds();
  const games = scoreData?.games ?? [];

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
        <div className="flex items-center gap-2 mb-3">
          <Cpu size={16} className="text-purple-400" />
          <span className="text-xs font-bold uppercase tracking-widest text-gray-500">
            XGBoost · SHAP · Live Odds via FanDuel
          </span>
        </div>
        <h1 className="text-5xl md:text-6xl font-black tracking-tighter mb-3">
          Game <span className="gradient-text">Predictions</span>
        </h1>
        <p className="text-gray-500 font-medium text-lg">
          AI win probabilities, predicted scores, and real-time betting lines.
        </p>
        {oddsData?.length > 0 && (
          <div className="mt-3 flex items-center gap-2 text-xs text-green-400 font-bold">
            <TrendingUp size={12} />
            {oddsData.length} game{oddsData.length > 1 ? 's' : ''} with live betting odds
          </div>
        )}
      </motion.div>

      {scoresLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[0, 1].map(i => <div key={i} className="skeleton h-96 rounded-2xl" />)}
        </div>
      ) : games.length === 0 ? (
        <div className="glass rounded-2xl p-16 text-center text-gray-500">
          <Cpu size={40} className="mx-auto mb-4 opacity-20" />
          <p className="font-semibold text-lg">No recent games found.</p>
        </div>
      ) : (
        <motion.div
          initial="hidden"
          animate="show"
          variants={{ show: { transition: { staggerChildren: 0.1 } } }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6"
        >
          {games.map(game => (
            <motion.div key={game.game_id}
              variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }}
            >
              <PredictionCard game={game} oddsData={oddsData} />
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
