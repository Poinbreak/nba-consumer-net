import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

export function useSearch(query) {
  return useQuery({
    queryKey: ['search', query],
    queryFn: async () => {
      if (!query) return null;
      // const { data } = await axios.post('/api/search/nlq/', { query });
      // return data;
      return null;
    },
    enabled: !!query && query.length > 2,
  });
}
