import React, { useState, useCallback, useRef, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { useGameWebSocket } from '../hooks/useGameWebSocket';
import { motion, AnimatePresence } from 'framer-motion';

const MAX_POINTS = 40;

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="glass rounded-xl px-3 py-2 text-xs font-semibold shadow-xl">
      <div className="text-gray-400 mb-1">{d.label}</div>
      <div className="flex gap-3">
        <span style={{ color: d.homeColor }}>HOME {Math.round(d.prob * 100)}%</span>
        <span style={{ color: d.awayColor }}>AWAY {Math.round((1 - d.prob) * 100)}%</span>
      </div>
    </div>
  );
}

export default function WinProbabilityGraph({ gameId, homeAbbrev = 'HOME', awayAbbrev = 'AWAY', homeColor = '#6c63ff', awayColor = '#ff6b6b', initialProb = 0.5, isLive = false }) {
  const [history, setHistory] = useState(() =>
    Array.from({ length: 8 }, (_, i) => ({
      label: `Q1 ${(i + 1) * 2}:00`,
      prob: 0.5 + (Math.random() - 0.5) * 0.1,
      homeColor,
      awayColor,
    }))
  );
  const [liveData, setLiveData] = useState(null);
  const [connected, setConnected] = useState(false);
  const connectCountRef = useRef(0);

  const handleMessage = useCallback((data) => {
    setConnected(true);
    setLiveData(data);
    setHistory(prev => {
      const next = [
        ...prev,
        {
          label: data.time_remaining || 'Live',
          prob: data.home_win_prob,
          homeColor,
          awayColor,
        },
      ];
      return next.length > MAX_POINTS ? next.slice(-MAX_POINTS) : next;
    });
  }, [homeColor, awayColor]);

  useGameWebSocket(isLive ? gameId : null, handleMessage);

  const currentProb = liveData?.home_win_prob ?? history[history.length - 1]?.prob ?? initialProb;
  const homeWin = Math.round(currentProb * 100);
  const awayWin = 100 - homeWin;

  return (
    <div className="glass rounded-2xl p-6 overflow-hidden relative">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-400 live-dot" />
          <span className="text-xs font-bold uppercase tracking-widest text-gray-400">
            {connected ? 'Live Win Probability' : 'Win Probability'}
          </span>
        </div>
        {liveData && (
          <div className="text-xs font-semibold text-gray-500">
            {liveData.time_remaining} remaining
          </div>
        )}
      </div>

      {/* Win % Bar */}
      <div className="flex items-center gap-3 mb-6">
        <span className="text-sm font-extrabold w-12 text-left" style={{ color: awayColor }}>{awayAbbrev}</span>
        <div className="flex-1 prob-bar-track">
          <div
            className="prob-bar-fill"
            style={{
              width: `${homeWin}%`,
              background: `linear-gradient(90deg, ${awayColor}60 0%, ${homeColor} 100%)`,
            }}
          />
        </div>
        <span className="text-sm font-extrabold w-12 text-right" style={{ color: homeColor }}>{homeAbbrev}</span>
      </div>

      {/* Percentage labels */}
      <div className="flex justify-between text-xs font-bold text-gray-500 mb-6 px-[3.25rem]">
        <span style={{ color: awayColor }}>{awayWin}%</span>
        <span style={{ color: homeColor }}>{homeWin}%</span>
      </div>

      {/* Chart */}
      <div className="h-36">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={history} margin={{ top: 4, right: 0, left: -30, bottom: 0 }}>
            <defs>
              <linearGradient id={`grad-home-${gameId}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={homeColor} stopOpacity={0.35} />
                <stop offset="95%" stopColor={homeColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="label" hide />
            <YAxis domain={[0, 1]} hide />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={0.5} stroke="#2e2e3a" strokeDasharray="4 4" />
            <Area
              type="monotone"
              dataKey="prob"
              stroke={homeColor}
              strokeWidth={2}
              fill={`url(#grad-home-${gameId})`}
              dot={false}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Ambient glow */}
      <div
        className="absolute -bottom-12 -right-12 w-40 h-40 rounded-full blur-3xl opacity-10 pointer-events-none"
        style={{ background: homeColor }}
      />
    </div>
  );
}
