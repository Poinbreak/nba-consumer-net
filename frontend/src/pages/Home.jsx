import React from 'react';
import { motion } from 'framer-motion';
import { Activity, Zap } from 'lucide-react';
import GameTile from '../components/GameTile';
import SearchBar from '../components/SearchBar';
import { useLiveScore } from '../hooks/useLiveScore';

const HERO_STATS = [
  { label: 'Games Today',    value: '8' },
  { label: 'ML Predictions', value: '99.2%', sub: 'accuracy' },
  { label: 'Live Games',     value: '3' },
  { label: 'Players Tracked', value: '450+' },
];

const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const item      = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

export default function Home() {
  const { data, isLoading } = useLiveScore();
  const games = data?.games ?? [];

  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col">
      {/* ── Hero ────────────────────────────────── */}
      <section className="relative flex flex-col items-center justify-center py-24 px-6 overflow-hidden">
        {/* Background blobs */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full blur-[120px] opacity-[0.07] pointer-events-none"
          style={{ background: 'radial-gradient(circle, #6c63ff 0%, #a855f7 50%, #ec4899 100%)' }} />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-4xl"
        >
          <div className="inline-flex items-center gap-2 glass-lighter px-4 py-1.5 rounded-full text-xs font-bold text-gray-400 mb-6 uppercase tracking-widest">
            <Zap size={12} className="text-yellow-400" />
            Powered by XGBoost · Real-time WebSockets
          </div>
          <h1 className="text-6xl md:text-8xl font-black tracking-tighter leading-none mb-6">
            The NBA,{' '}
            <span className="gradient-text">Decoded.</span>
          </h1>
          <p className="text-lg md:text-xl text-gray-500 font-medium mb-10 max-w-xl mx-auto">
            AI-powered win probabilities, player props, and trade simulation — all in one platform.
          </p>

          <SearchBar />
        </motion.div>

        {/* Hero stats */}
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="mt-14 grid grid-cols-2 md:grid-cols-4 gap-4 w-full max-w-3xl"
        >
          {HERO_STATS.map(s => (
            <motion.div key={s.label} variants={item}
              className="glass rounded-xl p-4 text-center card-hover"
            >
              <div className="text-2xl font-black gradient-text mb-1">{s.value}</div>
              <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider">{s.label}</div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ── Live Scoreboard ──────────────────────── */}
      <section className="px-6 pb-16">
        <div className="flex items-center gap-3 mb-6">
          <Activity size={16} className="text-green-400" />
          <h2 className="text-sm font-bold uppercase tracking-widest text-gray-400">Live &amp; Upcoming</h2>
        </div>

        {isLoading ? (
          <div className="flex gap-6 overflow-x-auto scrollbar-hide pb-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="skeleton rounded-2xl min-w-[260px] h-48" />
            ))}
          </div>
        ) : games.length === 0 ? (
          <div className="glass rounded-2xl p-12 text-center text-gray-500">
            <Activity size={32} className="mx-auto mb-3 opacity-30" />
            <p className="font-semibold">No games scheduled today.</p>
          </div>
        ) : (
          <motion.div
            variants={container} initial="hidden" animate="show"
            className="flex gap-5 overflow-x-auto scrollbar-hide pb-4"
          >
            {games.map(game => (
              <motion.div key={game.game_id} variants={item} className="shrink-0">
                <GameTile game={game} />
              </motion.div>
            ))}
          </motion.div>
        )}
      </section>
    </div>
  );
}
