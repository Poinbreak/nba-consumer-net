import React from 'react';

export default function StatCard({ label, value, trend }) {
  return (
    <div className="bg-surface border border-border p-6 rounded-2xl flex flex-col items-center justify-center text-center">
      <div className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-2">{label}</div>
      <div className="text-5xl font-extrabold tracking-tighter text-white">{value}</div>
      {trend && (
        <div className={`mt-2 text-sm font-bold ${trend.startsWith('+') ? 'text-green-400' : 'text-red-400'}`}>
          {trend}
        </div>
      )}
    </div>
  );
}
