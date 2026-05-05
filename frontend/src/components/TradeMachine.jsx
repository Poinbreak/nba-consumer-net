import React, { useState } from 'react';

const PlayerCheckbox = ({ player, onToggle, isSelected }) => (
  <div 
    onClick={() => onToggle(player)}
    className={`flex items-center justify-between p-3 border-b border-border cursor-pointer transition-colors ${isSelected ? 'bg-border/50' : 'hover:bg-border/30'}`}
  >
    <div className="flex items-center space-x-3">
      <div className={`w-5 h-5 rounded border flex items-center justify-center ${isSelected ? 'bg-green-500 border-green-500' : 'border-gray-500'}`}>
        {isSelected && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" /></svg>}
      </div>
      <div>
        <div className="font-bold text-white">{player.name}</div>
        <div className="text-xs text-gray-500 font-semibold">{player.pos} • {player.age} yrs</div>
      </div>
    </div>
    <div className="font-bold tracking-tight text-gray-300">
      ${(player.salary / 1000000).toFixed(1)}M
    </div>
  </div>
);

export default function TradeMachine() {
  const [team1Players, setTeam1Players] = useState([
    { id: 1, name: 'D\'Angelo Russell', pos: 'PG', age: 28, salary: 17307693 },
    { id: 2, name: 'Rui Hachimura', pos: 'PF', age: 26, salary: 15740741 },
    { id: 3, name: 'Gabe Vincent', pos: 'PG', age: 27, salary: 10500000 },
  ]);
  const [team2Players, setTeam2Players] = useState([
    { id: 4, name: 'Zach LaVine', pos: 'SG', age: 29, salary: 40064220 },
    { id: 5, name: 'Alex Caruso', pos: 'SG', age: 30, salary: 9460000 },
  ]);

  const [selectedT1, setSelectedT1] = useState([]);
  const [selectedT2, setSelectedT2] = useState([]);

  const toggleT1 = (p) => setSelectedT1(prev => prev.find(x => x.id === p.id) ? prev.filter(x => x.id !== p.id) : [...prev, p]);
  const toggleT2 = (p) => setSelectedT2(prev => prev.find(x => x.id === p.id) ? prev.filter(x => x.id !== p.id) : [...prev, p]);

  const t1Outgoing = selectedT1.reduce((acc, p) => acc + p.salary, 0);
  const t2Outgoing = selectedT2.reduce((acc, p) => acc + p.salary, 0);

  // NBA Trade Rule logic (simplified)
  const isT1Valid = t1Outgoing > 0 && t2Outgoing <= t1Outgoing * 1.25 + 250000;
  const isT2Valid = t2Outgoing > 0 && t1Outgoing <= t2Outgoing * 1.25 + 250000;
  const isValid = (t1Outgoing > 0 || t2Outgoing > 0) && isT1Valid && isT2Valid;

  return (
    <div className="bg-surface border border-border rounded-2xl p-8 mb-12">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        
        {/* Team 1 Side */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-extrabold tracking-tighter text-[#552583]">LAL</h3>
            <div className="text-sm font-semibold text-gray-500">Outgoing: ${(t1Outgoing / 1000000).toFixed(1)}M</div>
          </div>
          <div className="border border-border rounded-xl overflow-hidden bg-court">
            {team1Players.map(p => (
              <PlayerCheckbox key={p.id} player={p} onToggle={toggleT1} isSelected={!!selectedT1.find(x => x.id === p.id)} />
            ))}
          </div>
        </div>

        {/* Team 2 Side */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-extrabold tracking-tighter text-[#CE1141]">CHI</h3>
            <div className="text-sm font-semibold text-gray-500">Outgoing: ${(t2Outgoing / 1000000).toFixed(1)}M</div>
          </div>
          <div className="border border-border rounded-xl overflow-hidden bg-court">
            {team2Players.map(p => (
              <PlayerCheckbox key={p.id} player={p} onToggle={toggleT2} isSelected={!!selectedT2.find(x => x.id === p.id)} />
            ))}
          </div>
        </div>
      </div>

      {/* Verification Bar */}
      <div className={`p-4 rounded-xl flex items-center justify-between font-bold border ${isValid ? 'bg-green-500/10 border-green-500 text-green-400' : 'bg-red-500/10 border-red-500 text-red-400'}`}>
        <div>
          {isValid ? 'Trade Successful (CBA Approved)' : 'Trade Failed (Salary Mismatch)'}
        </div>
        <button 
          disabled={!isValid}
          className={`px-6 py-2 rounded-lg text-white transition-colors ${isValid ? 'bg-green-500 hover:bg-green-600' : 'bg-gray-600 cursor-not-allowed opacity-50'}`}
        >
          Run Simulation
        </button>
      </div>
    </div>
  );
}
