import React from 'react';

export default function SimFeed({ events }) {
  return (
    <div className="bg-surface border border-border rounded-xl p-6 max-h-[400px] overflow-y-auto">
      <h3 className="font-bold text-xl mb-4">Live Play-by-Play</h3>
      <div className="space-y-4">
        {events && events.length > 0 ? events.map((event, i) => (
          <div key={i} className="flex space-x-4 border-b border-border pb-3 last:border-0">
            <div className="text-sm font-bold text-gray-500 w-12">{event.clock}</div>
            <div className="text-sm font-semibold text-white">{event.description}</div>
          </div>
        )) : (
          <div className="text-gray-500 font-semibold italic text-sm">Waiting for simulation to start...</div>
        )}
      </div>
    </div>
  );
}
