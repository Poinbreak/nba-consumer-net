import { useMutation } from '@tanstack/react-query';
import axios from 'axios';

export function useTradeSimulation() {
  return useMutation({
    mutationFn: async (tradePayload) => {
      // const { data } = await axios.post('/api/gm/trade/simulate/', tradePayload);
      // return data;
      return null;
    }
  });
}
