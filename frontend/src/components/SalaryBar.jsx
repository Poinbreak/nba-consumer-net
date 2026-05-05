import React from 'react';

export default function SalaryBar({ used, cap, tax }) {
  const capPercentage = Math.min((used / cap) * 100, 100);
  const taxPercentage = Math.min((used / tax) * 100, 100);
  
  const isOverTax = used > tax;
  const isOverCap = used > cap;

  return (
    <div className="w-full">
      <div className="flex justify-between text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">
        <span>Cap Space</span>
        <span>${(used / 1000000).toFixed(1)}M / ${(cap / 1000000).toFixed(1)}M</span>
      </div>
      <div className="relative h-4 bg-gray-800 rounded-full overflow-hidden flex">
        <div 
          className={`h-full transition-all duration-500 ${isOverTax ? 'bg-red-500' : isOverCap ? 'bg-yellow-500' : 'bg-green-500'}`}
          style={{ width: `${capPercentage}%` }}
        />
      </div>
    </div>
  );
}
