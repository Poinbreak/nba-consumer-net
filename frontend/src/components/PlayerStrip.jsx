import React from 'react';

export default function PlayerStrip({ player, stats }) {
  return (
    <div className="flex items-center justify-between p-4 bg-surface border border-border rounded-xl mb-4 hover:bg-border/50 transition-colors cursor-pointer">
      <div className="flex items-center space-x-4">
        <div className="w-12 h-12 rounded-full bg-gray-800 flex items-center justify-center text-white font-bold">
          {player.name.charAt(0)}
        </div>
        <div>
          <div className="font-bold text-lg">{player.name}</div>
          <div className="text-sm font-semibold text-gray-500">{player.team} • {player.pos}</div>
        </div>
      </div>
      <div className="flex space-x-8 text-right">
        {stats.map((stat, i) => (
          <div key={i} className="hidden md:block">
            <div className="font-extrabold text-xl">{stat.value}</div>
            <div className="text-[10px] font-bold text-gray-500 uppercase">{stat.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
