import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const http = axios.create({ baseURL: API, timeout: 10_000 });

export function useLiveScore() {
  return useQuery({
    queryKey: ['liveScores'],
    queryFn: async () => { const { data } = await http.get('/live-scoreboard/'); return data; },
    refetchInterval: 30_000, staleTime: 0, retry: 2, placeholderData: { games: [] },
  });
}

export function useGamePrediction(gameId) {
  return useQuery({
    queryKey: ['prediction', gameId],
    queryFn: async () => { const { data } = await http.get(`/predictions/game/${gameId}/`); return data; },
    enabled: !!gameId, staleTime: 60_000, retry: 1,
  });
}

export function usePlayerProps(gameId) {
  return useQuery({
    queryKey: ['playerProps', gameId],
    queryFn: async () => { const { data } = await http.get(`/predictions/player-props/${gameId}/`); return data; },
    enabled: !!gameId, staleTime: 60_000,
  });
}

export function useOdds() {
  return useQuery({
    queryKey: ['odds'],
    queryFn: async () => { const { data } = await http.get('/odds/'); return data; },
    staleTime: 5 * 60_000, retry: 1, placeholderData: [],
  });
}

export function useTeamStats(teamId) {
  return useQuery({
    queryKey: ['teamStats', teamId],
    queryFn: async () => { const { data } = await http.get(`/stats/team/${teamId}/`); return data; },
    enabled: !!teamId, staleTime: 5 * 60_000,
  });
}

export function usePlayerStats(playerId) {
  return useQuery({
    queryKey: ['playerStats', playerId],
    queryFn: async () => { const { data } = await http.get(`/stats/player/${playerId}/`); return data; },
    enabled: !!playerId, staleTime: 5 * 60_000,
  });
}

export function usePlayerSearch(query) {
  return useQuery({
    queryKey: ['playerSearch', query],
    queryFn: async () => { const { data } = await http.get(`/players/search/?q=${encodeURIComponent(query)}`); return data; },
    enabled: query?.length >= 2, staleTime: 30_000,
  });
}

export function useLeagueLeaders(stat = 'pts_avg') {
  return useQuery({
    queryKey: ['leaders', stat],
    queryFn: async () => { const { data } = await http.get(`/leaders/?stat=${stat}`); return data; },
    staleTime: 5 * 60_000,
  });
}
