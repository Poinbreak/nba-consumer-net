import React from 'react';
import { useOdds } from '../api';
import { Dot, ErrorBox, Loading, pct } from '../ui/kit';

const am = (n) => (n == null ? '–' : n > 0 ? `+${n}` : `${n}`);

export default function Odds() {
  const { data, isLoading, error } = useOdds();
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !data) return <Loading rows={4} />;
  return (
    <>
      <h1 className="t">Odds</h1>
      <p className="muted">Live US sportsbook moneylines. “Edge” is our model’s win probability minus the de-vigged market probability; informational only, not betting advice.</p>
      {data.error && <div className="card empty">{data.error}</div>}
      {!data.error && data.games.length === 0 && <div className="card empty">No lines posted yet. Books usually open a day or two before tip-off.</div>}
      <div className="grid g2">
        {data.games.map((g) => {
          const edge = g.edge_home;
          return (
            <div className="card" key={g.id}>
              <div className="row sp" style={{ marginBottom: 10 }}>
                <span className="muted" style={{ fontSize: 13 }}>{new Date(g.commence).toLocaleString([], { weekday: 'short', hour: 'numeric', minute: '2-digit' })}</span>
                {g.spread != null && <span className="pill">{g.home_abbr} {g.spread > 0 ? '+' : ''}{g.spread} · O/U {g.total ?? '–'}</span>}
              </div>
              {[['away', g.away, g.away_abbr, g.away_color], ['home', g.home, g.home_abbr, g.home_color]].map(([side, name, abbr, color]) => (
                <div className="tm" key={side} style={{ marginBottom: 6 }}>
                  <Dot color={color} />{name}
                  <span className="sc" style={{ fontSize: 18 }}>{am(g.best[side])}</span>
                </div>
              ))}
              <div className="row sp num" style={{ fontSize: 13, marginTop: 10 }}>
                <span className="muted">Market {g.home_abbr} {pct(g.market_home_prob)}</span>
                <span className="muted">Model {g.model_home_prob != null ? pct(g.model_home_prob) : '–'}</span>
                {edge != null && <span className={`pill ${edge > 0.03 ? 'good' : edge < -0.03 ? 'bad' : ''}`}>{edge > 0 ? '+' : ''}{(edge * 100).toFixed(1)} pt edge on {g.home_abbr}</span>}
              </div>
              <div className="faint" style={{ fontSize: 12, marginTop: 8 }}>Best price shown · {g.books.length} books</div>
            </div>
          );
        })}
      </div>
      {data.requests_remaining && <p className="faint" style={{ fontSize: 12 }}>Odds API quota remaining: {data.requests_remaining}</p>}
    </>
  );
}
