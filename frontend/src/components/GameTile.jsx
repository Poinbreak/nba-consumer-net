import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useGamePrediction } from '../hooks/useLiveScore';

const STATUS_STYLES = {
  Live:      'bg-green-400/10 text-green-400 border border-green-400/20',
  Scheduled: 'bg-blue-400/10  text-blue-400  border border-blue-400/20',
  Final:     'bg-gray-400/10  text-gray-400  border border-gray-400/20',
};

export default function GameTile({ game }) {
  const {
    game_id, home_team_abbrev, away_team_abbrev,
    home_team_accent = '#6c63ff', away_team_accent = '#ff6b6b',
    home_score, away_score, status, quarter, time_remaining,
    home_win_prob: baseHomeProb = 50,
  } = game;

  // Fetch real prediction for this game
  const { data: pred } = useGamePrediction(game_id);
  const home_win_prob = pred ? Math.round(pred.home_win_probability * 100) : baseHomeProb;
  const away_win_prob = 100 - home_win_prob;

  const isLive      = status === 'Live';
  const isFinal     = status === 'Final';
  const isScheduled = status === 'Scheduled';

  return (
    <motion.div
      whileHover={{ y: -4, boxShadow: '0 16px 48px rgba(0,0,0,0.4)' }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      className="shrink-0"
    >
      <Link to={`/predictions`} className="block">
        <div className="glass card-hover rounded-2xl p-5 min-w-[260px] max-w-[300px] relative overflow-hidden cursor-pointer">
          {/* Ambient glow */}
          <div className="absolute -top-8 -left-8 w-32 h-32 rounded-full blur-3xl opacity-10 pointer-events-none"
            style={{ background: home_team_accent }} />

          {/* Status badge */}
          <div className="flex items-center justify-between mb-5">
            <span className={`text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded-full ${STATUS_STYLES[status] || STATUS_STYLES.Final}`}>
              {isLive ? (
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400 live-dot inline-block" />
                  Live Q{quarter} {time_remaining}
                </span>
              ) : isScheduled ? 'Upcoming' : `Final`}
            </span>
          </div>

          {/* Teams & Scores */}
          <div className="space-y-3 mb-5">
            {/* Away */}
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-extrabold shadow-lg"
                  style={{ background: away_team_accent + '33', color: away_team_accent, border: `1px solid ${away_team_accent}44` }}>
                  {away_team_abbrev?.[0]}
                </div>
                <span className="font-bold text-base">{away_team_abbrev}</span>
              </div>
              {!isScheduled && (
                <span className={`font-extrabold text-2xl ${isFinal && away_score > home_score ? 'text-white' : 'text-gray-400'}`}>
                  {away_score ?? '–'}
                </span>
              )}
            </div>

            {/* Home */}
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-extrabold shadow-lg"
                  style={{ background: home_team_accent + '33', color: home_team_accent, border: `1px solid ${home_team_accent}44` }}>
                  {home_team_abbrev?.[0]}
                </div>
                <span className="font-bold text-base">{home_team_abbrev}</span>
              </div>
              {!isScheduled && (
                <span className={`font-extrabold text-2xl ${isFinal && home_score > away_score ? 'text-white' : 'text-gray-400'}`}>
                  {home_score ?? '–'}
                </span>
              )}
            </div>
          </div>

          {/* Win Probability Bar */}
          <div className="mt-1">
            <div className="prob-bar-track">
              <div className="prob-bar-fill"
                style={{
                  width: `${home_win_prob}%`,
                  background: `linear-gradient(90deg, ${away_team_accent} 0%, ${home_team_accent} 100%)`,
                }} />
            </div>
            <div className="flex justify-between mt-1.5 text-[10px] font-bold text-gray-600 uppercase tracking-widest">
              <span>{away_team_abbrev} {away_win_prob}%</span>
              <span>{home_win_prob}% {home_team_abbrev}</span>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
