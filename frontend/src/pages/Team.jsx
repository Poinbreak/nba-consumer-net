import React from 'react';

export default function Team() {
  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <div className="flex flex-col md:flex-row justify-between items-center md:items-end mb-16 border-b border-border pb-8">
        <div className="flex items-center mb-8 md:mb-0">
          <div className="w-24 h-24 md:w-32 md:h-32 rounded-full bg-[#552583] flex items-center justify-center mr-6 md:mr-10">
            <span className="text-4xl font-bold text-white">LAL</span>
          </div>
          <div>
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tighter mb-2">Los Angeles Lakers</h1>
            <div className="text-xl md:text-2xl font-semibold text-gray-400">
              42-24 • 2nd in West
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2 bg-surface border border-border p-8 rounded-2xl">
          <h3 className="font-bold text-2xl mb-6">Roster</h3>
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-border text-gray-500 uppercase text-xs tracking-wider">
                <th className="p-4 font-semibold">Player</th>
                <th className="p-4 font-semibold">Pos</th>
                <th className="p-4 font-semibold text-right">Age</th>
                <th className="p-4 font-semibold text-right">Salary</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-border hover:bg-border/50">
                <td className="p-4 font-bold">LeBron James</td>
                <td className="p-4 text-gray-400 font-semibold">SF</td>
                <td className="p-4 text-right font-semibold">39</td>
                <td className="p-4 text-right font-bold text-gray-300">$47.6M</td>
              </tr>
              <tr className="border-b border-border hover:bg-border/50">
                <td className="p-4 font-bold">Anthony Davis</td>
                <td className="p-4 text-gray-400 font-semibold">C</td>
                <td className="p-4 text-right font-semibold">31</td>
                <td className="p-4 text-right font-bold text-gray-300">$40.6M</td>
              </tr>
              <tr className="border-b border-border hover:bg-border/50">
                <td className="p-4 font-bold">D'Angelo Russell</td>
                <td className="p-4 text-gray-400 font-semibold">PG</td>
                <td className="p-4 text-right font-semibold">28</td>
                <td className="p-4 text-right font-bold text-gray-300">$17.3M</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="space-y-8">
          <div className="bg-surface border border-border p-8 rounded-2xl">
            <h3 className="font-bold text-xl mb-6">Upcoming Schedule</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center border-b border-border pb-4">
                <div className="font-bold">vs DEN</div>
                <div className="text-gray-400 font-semibold text-sm">Tonight, 10:00 PM</div>
              </div>
              <div className="flex justify-between items-center border-b border-border pb-4">
                <div className="font-bold">@ PHX</div>
                <div className="text-gray-400 font-semibold text-sm">Mar 12, 9:00 PM</div>
              </div>
              <div className="flex justify-between items-center">
                <div className="font-bold">vs MIN</div>
                <div className="text-gray-400 font-semibold text-sm">Mar 14, 10:30 PM</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
