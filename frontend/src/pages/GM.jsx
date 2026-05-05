import React from 'react';
import TradeMachine from '../components/TradeMachine';

export default function GM() {
  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <div className="mb-12">
        <h1 className="text-5xl font-extrabold tracking-tighter mb-4">GM Simulator</h1>
        <p className="text-xl text-gray-400 font-semibold">Test CBA-approved trades and simulate outcomes.</p>
      </div>

      <TradeMachine />

      <div className="bg-surface border border-border rounded-2xl p-8">
        <h3 className="font-bold text-2xl mb-6">Simulation Dashboard</h3>
        <p className="text-gray-400 mb-6 font-semibold">Run a trade to see Monte Carlo simulation results here.</p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 opacity-30 pointer-events-none">
          <div className="border border-border rounded-xl p-6 bg-court">
            <div className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-2">Projected Wins</div>
            <div className="text-4xl font-extrabold text-white">45.2 <span className="text-lg text-green-400">+2.1</span></div>
          </div>
          <div className="border border-border rounded-xl p-6 bg-court">
            <div className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-2">Offensive Rating</div>
            <div className="text-4xl font-extrabold text-white">114.5 <span className="text-lg text-green-400">+3.4</span></div>
          </div>
          <div className="border border-border rounded-xl p-6 bg-court">
            <div className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-2">Defensive Rating</div>
            <div className="text-4xl font-extrabold text-white">112.8 <span className="text-lg text-red-400">+1.2</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
