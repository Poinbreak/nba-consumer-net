import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

export function useLiveScore() {
  return useQuery({
    queryKey: ['liveScores'],
    queryFn: async () => {
      // const { data } = await axios.get('/api/scores/live/');
      // return data;
      return { games: [], isLive: false, lastUpdated: new Date() };
    },
    refetchInterval: 30000,
    staleTime: 0,
  });
}
