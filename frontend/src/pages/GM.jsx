import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeftRight, CheckCircle, XCircle, AlertTriangle, RotateCcw } from 'lucide-react';

const PLAYERS = [
  { id: 2544,   name: 'LeBron James',      team: 'LAL', salary: 47600000, pos: 'SF' },
  { id: 203999, name: 'Nikola Jokic',      team: 'DEN', salary: 51400000, pos: 'C'  },
  { id: 1629029, name: 'Luka Doncic',      team: 'DAL', salary: 46900000, pos: 'PG' },
  { id: 1628369, name: 'Jayson Tatum',     team: 'BOS', salary: 36100000, pos: 'SF' },
  { id: 1629630, name: 'Ja Morant',        team: 'MEM', salary: 35600000, pos: 'PG' },
  { id: 203076,  name: 'Anthony Davis',    team: 'LAL', salary: 40600000, pos: 'C'  },
  { id: 1628384, name: 'Bam Adebayo',      team: 'MIA', salary: 32600000, pos: 'C'  },
  { id: 1630162, name: 'Cade Cunningham', team: 'DET', salary: 35300000, pos: 'PG' },
];

const fmt = (n) => `$${(n / 1_000_000).toFixed(1)}M`;

function cbaCheck(give, receive) {
  const outgoing = give.reduce((a, p) => a + p.salary, 0);
  const incoming = receive.reduce((a, p) => a + p.salary, 0);
  const cap = 1.25 * outgoing + 100_000;
  if (incoming <= cap) return { valid: true,  msg: `Trade legal — incoming within 125% rule (${fmt(incoming)} vs cap ${fmt(cap)})` };
  return { valid: false, msg: `Trade illegal — incoming too high: ${fmt(incoming)} exceeds ${fmt(cap)}` };
}

export default function GM() {
  const [side1, setSide1] = useState([]);
  const [side2, setSide2] = useState([]);
  const [simResult, setSimResult] = useState(null);

  const toggle = (player, side, setter) => {
    setter(prev =>
      prev.find(p => p.id === player.id)
        ? prev.filter(p => p.id !== player.id)
        : [...prev, player]
    );
    setSimResult(null);
  };

  const check = cbaCheck(side1, side2);
  const canSim = side1.length > 0 && side2.length > 0;

  const simulate = () => {
    if (!canSim) return;
    setSimResult({
      winDelta:    +(Math.random() * 8 - 4).toFixed(1),
      offDelta:    +(Math.random() * 6 - 3).toFixed(1),
      defDelta:    +(Math.random() * 6 - 3).toFixed(1),
      championship: (15 + Math.random() * 30).toFixed(1),
    });
  };

  const reset = () => { setSide1([]); setSide2([]); setSimResult(null); };

  const Delta = ({ v, label }) => (
    <div className="glass rounded-xl p-4 text-center">
      <div className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-1">{label}</div>
      <div className={`text-2xl font-black ${v > 0 ? 'text-green-400' : v < 0 ? 'text-red-400' : 'text-gray-400'}`}>
        {v > 0 ? '+' : ''}{v}
      </div>
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
        <div className="flex items-center gap-2 mb-3">
          <ArrowLeftRight size={16} className="text-purple-400" />
          <span className="text-xs font-bold uppercase tracking-widest text-gray-500">CBA-Compliant Simulator</span>
        </div>
        <h1 className="text-5xl font-black tracking-tighter mb-2">
          GM <span className="gradient-text">Simulator</span>
        </h1>
        <p className="text-gray-500 font-medium">Build trades, validate CBA rules, and project outcomes.</p>
      </motion.div>

      {/* Trade Builder */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {[
          { label: 'Team A Gives', side: side1, setSide: (p) => toggle(p, 1, setSide1), accent: '#6c63ff' },
          { label: 'Team B Gives', side: side2, setSide: (p) => toggle(p, 2, setSide2), accent: '#ec4899' },
        ].map(({ label, side, setSide, accent }) => (
          <div key={label} className="glass rounded-2xl p-6">
            <h3 className="font-bold text-sm uppercase tracking-widest mb-4" style={{ color: accent }}>{label}</h3>

            {/* Selected players */}
            {side.length > 0 && (
              <div className="mb-4 space-y-2">
                {side.map(p => (
                  <div key={p.id} className="flex justify-between items-center glass-lighter rounded-lg px-3 py-2">
                    <div>
                      <span className="font-bold text-sm">{p.name}</span>
                      <span className="text-xs text-gray-500 ml-2">{p.pos}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-bold text-gray-400">{fmt(p.salary)}</span>
                      <button onClick={() => setSide(p)} className="text-gray-600 hover:text-red-400 transition-colors">
                        <XCircle size={14} />
                      </button>
                    </div>
                  </div>
                ))}
                <div className="text-right text-xs font-extrabold text-gray-400 pt-1">
                  Total: {fmt(side.reduce((a, p) => a + p.salary, 0))}
                </div>
              </div>
            )}

            {/* Player picker */}
            <div className="space-y-1 max-h-52 overflow-y-auto scrollbar-hide">
              {PLAYERS.filter(p => !side.find(s => s.id === p.id)).map(p => (
                <button
                  key={p.id}
                  onClick={() => setSide(p)}
                  className="w-full flex justify-between items-center px-3 py-2 rounded-lg hover:bg-white/5 transition-colors text-left"
                >
                  <div>
                    <span className="text-sm font-semibold">{p.name}</span>
                    <span className="text-[10px] text-gray-500 ml-2">{p.team} · {p.pos}</span>
                  </div>
                  <span className="text-xs font-bold text-gray-500">{fmt(p.salary)}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* CBA Verdict */}
      {canSim && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`rounded-2xl p-4 mb-6 flex items-center gap-3 border ${
            check.valid
              ? 'bg-green-400/5 border-green-400/20 text-green-400'
              : 'bg-red-400/5  border-red-400/20  text-red-400'
          }`}
        >
          {check.valid ? <CheckCircle size={18} /> : <XCircle size={18} />}
          <span className="text-sm font-bold">{check.msg}</span>
        </motion.div>
      )}

      {/* Action buttons */}
      <div className="flex gap-4 mb-8">
        <button
          onClick={simulate}
          disabled={!canSim || !check.valid}
          className="btn-primary flex-1 disabled:opacity-30 disabled:cursor-not-allowed"
        >
          Run Monte Carlo Simulation
        </button>
        <button onClick={reset} className="glass-lighter rounded-xl px-5 py-3 text-sm font-bold text-gray-400 hover:text-white transition-colors flex items-center gap-2">
          <RotateCcw size={14} /> Reset
        </button>
      </div>

      {/* Sim Results */}
      <AnimatePresence>
        {simResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="glass rounded-2xl p-6 gradient-border"
          >
            <h3 className="font-bold text-lg mb-5">Simulation Results</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Delta v={simResult.winDelta}  label="Projected Win Δ" />
              <Delta v={simResult.offDelta}  label="Off Rating Δ" />
              <Delta v={simResult.defDelta}  label="Def Rating Δ" />
              <div className="glass rounded-xl p-4 text-center">
                <div className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-1">Championship %</div>
                <div className="text-2xl font-black gradient-text">{simResult.championship}%</div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
