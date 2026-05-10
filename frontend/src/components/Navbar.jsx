import React from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Activity, BarChart2, TrendingUp, DollarSign, Cpu } from 'lucide-react';

const NAV_ITEMS = [
  { to: '/',            label: 'Scoreboard', icon: Activity },
  { to: '/team',        label: 'Teams',      icon: BarChart2 },
  { to: '/player',      label: 'Players',    icon: TrendingUp },
  { to: '/predictions', label: 'Predict',    icon: Cpu },
  { to: '/bets',        label: 'Betting',    icon: DollarSign },
  { to: '/gm',          label: 'GM Mode',    icon: BarChart2 },
];

export default function Navbar() {
  const { pathname } = useLocation();

  return (
    <header className="glass border-b border-white/5 sticky top-0 z-50">
      <nav className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#6c63ff] to-[#a855f7] flex items-center justify-center">
            <span className="text-white font-black text-sm">N</span>
          </div>
          <span className="font-black text-xl tracking-tighter">
            NBA<span className="gradient-text">NET</span>
          </span>
        </Link>

        {/* Nav links */}
        <div className="hidden md:flex items-center gap-1">
          {NAV_ITEMS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `nav-link px-4 py-2 rounded-lg transition-colors text-sm ${isActive ? 'active text-white bg-white/5' : ''}`
              }
            >
              {label}
            </NavLink>
          ))}
        </div>

        {/* Right: Live indicator */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 glass-lighter px-3 py-1.5 rounded-full text-xs font-bold text-green-400">
            <span className="w-1.5 h-1.5 bg-green-400 rounded-full live-dot" />
            Live
          </div>
        </div>
      </nav>
    </header>
  );
}
