import React, { useEffect, useState } from 'react';

export default function WinMeter({ homeProb, homeColor, awayColor }) {
  const [offset, setOffset] = useState(0);
  const radius = 80;
  const circumference = Math.PI * radius; // Half circle

  useEffect(() => {
    // Calculate how much of the arc should be filled
    // SVG stroke-dashoffset: 0 means fully visible, circumference means fully hidden
    // We want to fill it based on homeProb (0 to 100)
    const fillPercentage = homeProb / 100;
    const offsetValue = circumference - (fillPercentage * circumference);
    // Add slight delay for animation
    setTimeout(() => {
      setOffset(offsetValue);
    }, 100);
  }, [homeProb, circumference]);

  return (
    <div className="relative w-[200px] h-[100px] flex items-end justify-center overflow-hidden">
      {/* Background Arc (Away Team) */}
      <svg className="absolute top-0 left-0" width="200" height="100" viewBox="0 0 200 100">
        <path
          d="M 10,100 A 90,90 0 0,1 190,100"
          fill="none"
          stroke={awayColor || "#555"}
          strokeWidth="16"
          strokeLinecap="round"
        />
      </svg>
      
      {/* Foreground Arc (Home Team) */}
      <svg className="absolute top-0 left-0" width="200" height="100" viewBox="0 0 200 100">
        <path
          d="M 10,100 A 90,90 0 0,1 190,100"
          fill="none"
          stroke={homeColor || "#fff"}
          strokeWidth="16"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
          style={{ strokeDashoffset: offset === 0 ? circumference : offset }}
        />
      </svg>
      
      <div className="text-center pb-2 z-10">
        <div className="text-4xl font-extrabold tracking-tighter leading-none">{homeProb}%</div>
        <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1">Home Win</div>
      </div>
    </div>
  );
}
