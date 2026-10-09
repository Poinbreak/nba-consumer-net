import React, { useState } from 'react';
import { useScoreboard } from '../api';
import { ErrorBox, Loading } from '../ui/kit';
import { GameCard } from './Home';

export default function Scores() {
  const [date, setDate] = useState(undefined);
  const { data, isLoading, error } = useScoreboard(date);
  return (
    <>
      <div className="row sp wrapx">
        <h1 className="t">Scores</h1>
        <div className="row">
          <button className="btn ghost" disabled={!data?.prev} onClick={() => setDate(data.prev)}>←</button>
          <input type="date" value={data?.date ?? ''} onChange={(e) => e.target.value && setDate(e.target.value)}
                 style={{ background: 'var(--panel)', color: 'var(--text)', border: '1px solid var(--line)', borderRadius: 10, padding: '8px 10px', font: 'inherit' }} />
          <button className="btn ghost" disabled={!data?.next} onClick={() => setDate(data.next)}>→</button>
        </div>
      </div>
      <p className="muted">{data?.date}</p>
      {error ? <ErrorBox error={error} /> : isLoading || !data ? <Loading rows={6} /> : data.games.length ? (
        <div className="grid g3">{data.games.map((g) => <GameCard key={g.game_id} g={g} />)}</div>
      ) : <div className="card empty">No games on this date.</div>}
    </>
  );
}
