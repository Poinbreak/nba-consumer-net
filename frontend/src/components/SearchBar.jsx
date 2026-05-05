import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function SearchBar() {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      // In a real app, parse the query and redirect to the appropriate page
      navigate(`/player`);
    }
  };

  return (
    <form onSubmit={handleSearch} className="w-full max-w-[600px] relative">
      <input
        type="text"
        placeholder="Ask anything... 'LeBron points last 5 games'"
        className="w-full h-[52px] rounded-full bg-surface border border-border text-white px-6 text-lg placeholder-gray-500 focus:outline-none focus:border-gray-500 transition-colors"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button 
        type="submit" 
        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
      </button>
    </form>
  );
}
