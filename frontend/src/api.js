import { useQuery } from '@tanstack/react-query';

const BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

export async function get(path, params) {
  const clean = params ? Object.entries(params).filter(([, v]) => v != null && v !== '') : [];
  const qs = clean.length ? '?' + new URLSearchParams(clean) : '';
  const res = await fetch(`${BASE}/${path}${qs}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export async function post(path, body) {
  const res = await fetch(`${BASE}/${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

const q = (key, path, params, opts = {}) =>
  useQuery({ queryKey: [key, path, params], queryFn: () => get(path, params), staleTime: 60_000, ...opts });

export const useScoreboard = (date) => q('sb', 'v2/scoreboard/', { date }, { refetchInterval: 30_000 });
export const useUpcoming = () => q('up', 'v2/predictions/upcoming/', { limit: 60 });
export const useAwards = (season) => q('aw', 'v2/awards/', { season });
export const useTitleOdds = () => q('to', 'v2/title-odds/');
export const useOdds = () => q('odds', 'v2/odds/', null, { staleTime: 300_000 });
export const usePlayer = (id) => q('pl', `v2/players/${id}/`);
export const useTeam = (id) => q('tm', `v2/teams/${id}/`);
export const useTeams = () => q('tms', 'v2/teams/');
export const useAsk = (text) => q('ask', 'v2/ask/', { q: text }, { enabled: !!text });
export const useSearch = (text) =>
  q('srch', 'v2/players/search/', { q: text }, { enabled: (text || '').length >= 2, staleTime: 300_000 });

// GM Mode: POST endpoints keyed by the roster overrides so every roster change refetches its own view.
const gmq = (key, path, body, opts = {}) =>
  useQuery({ queryKey: [key, path, JSON.stringify(body)], queryFn: () => post(path, body), staleTime: 60_000, placeholderData: (prev) => prev, ...opts });
export const useGmLeague = (rosters) => gmq('gm', 'v2/gm/league/', { rosters });
export const useGmRoster = (teamId, rosters) => gmq('gmr', `v2/gm/roster/${teamId}/`, { rosters }, { enabled: !!teamId });
export const useGmTrade = (body, enabled) => gmq('gmt', 'v2/gm/trade/', body, { enabled, staleTime: 0 });
export const useGmSim = (rosters, enabled) => gmq('gms', 'v2/gm/simulate/', { rosters, sims: 800 }, { enabled, staleTime: 5 * 60_000 });
