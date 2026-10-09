import React from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAwards, useTitleOdds, useUpcoming } from '../api';
import { Avatar, Dot, ErrorBox, Loading, ProbBar, Table, pct } from '../ui/kit';

const TABS = [['games', 'Games'], ['awards', 'Awards'], ['title', 'Title odds']];
const AWARD_NAMES = { MVP: 'Most Valuable Player', DPOY: 'Defensive Player', ROY: 'Rookie of the Year', SMOY: 'Sixth Man', MIP: 'Most Improved' };

function Games() {
  const { data, isLoading, error } = useUpcoming();
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !data) return <Loading rows={4} />;
  const byDay = data.games.reduce((m, g) => ((m[g.game_date] ||= []).push(g), m), {});
  return Object.entries(byDay).map(([day, games]) => (
    <div key={day}>
      <h2 className="s">{day}</h2>
      <div className="grid g2">
        {games.map((g) => {
          const fav = g.home_win_prob >= 0.5 ? g.home_abbr : g.away_abbr;
          const fp = Math.max(g.home_win_prob, 1 - g.home_win_prob);
          return (
            <div className="card" key={g.game_id}>
              <div className="row sp" style={{ marginBottom: 12 }}>
                <span style={{ fontWeight: 800 }}>{g.away_name} @ {g.home_name}</span>
                <span className="pill">{fav} {pct(fp)}</span>
              </div>
              <ProbBar homeProb={g.home_win_prob} homeColor={g.home_color} awayColor={g.away_color} homeAbbr={g.home_abbr} awayAbbr={g.away_abbr} />
              {g.predicted_score && <div className="muted num" style={{ fontSize: 13, marginTop: 10 }}>Projected: {g.away_abbr} {Math.round(g.predicted_score.away)}, {g.home_abbr} {Math.round(g.predicted_score.home)}</div>}
              <div className="faint" style={{ fontSize: 12, marginTop: 6 }}>{(g.drivers ?? []).slice(0, 3).map((d) => d.text).join(' · ')}</div>
            </div>
          );
        })}
      </div>
    </div>
  ));
}

function Awards() {
  const [season, setSeason] = React.useState();
  const { data, isLoading, error } = useAwards(season);
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !data) return <Loading rows={4} />;
  return (
    <>
      <div className="row" style={{ marginBottom: 6 }}>
        <span className="muted">Season</span>
        <select value={data.season} onChange={(e) => setSeason(e.target.value)} style={{ background: 'var(--panel)', color: 'var(--text)', border: '1px solid var(--line)', borderRadius: 8, padding: '6px 10px', font: 'inherit' }}>
          {data.seasons.map((s) => <option key={s}>{s}</option>)}
        </select>
      </div>
      <div className="grid g2">
        {Object.keys(AWARD_NAMES).filter((a) => data.awards[a]).map((a) => (
          <div className="card" key={a}>
            <div style={{ fontWeight: 800, marginBottom: 10 }}>{AWARD_NAMES[a]}</div>
            {data.awards[a].slice(0, 6).map((p) => (
              <Link to={`/player/${p.player_id}`} className="row" key={p.player_id} style={{ padding: '6px 0' }}>
                <span className="faint num" style={{ width: 16 }}>{p.rank}</span>
                <Avatar src={p.headshot_url} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{p.player}</div>
                  <div className="bar" style={{ height: 5, marginTop: 4 }}><i style={{ width: `${Math.min(100, p.share * 100)}%`, background: p.team_color }} /></div>
                </div>
                <span className="num" style={{ fontWeight: 800 }}>{pct(p.share)}</span>
              </Link>
            ))}
          </div>
        ))}
      </div>
      <p className="faint" style={{ fontSize: 12 }}>Projected vote share. Models trained on 40 years of Basketball-Reference voting; backtest picks the MVP winner at #1 in 4 of the last 6 seasons.</p>
    </>
  );
}

function Title() {
  const { data, isLoading, error } = useTitleOdds();
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !data) return <Loading rows={5} />;
  const cols = [
    { key: 'name', label: 'Team', left: true, render: (r) => <Link to={`/team/${r.team_id}`} className="row" style={{ gap: 10, fontWeight: 700 }}><Dot color={r.color} />{r.name}</Link> },
    { key: 'exp_wins', label: 'Proj W' }, { key: 'playoff_prob', label: 'Playoffs', render: (r) => pct(r.playoff_prob) },
    { key: 'conf_finals_prob', label: 'Conf finals', render: (r) => pct(r.conf_finals_prob) },
    { key: 'finals_prob', label: 'Finals', render: (r) => pct(r.finals_prob) },
    { key: 'title_prob', label: 'Champion', highlight: true, render: (r) => pct(r.title_prob, 1) },
  ];
  return (
    <>
      <p className="muted">{data.season}: 5,000 simulated seasons plus playoffs. Team strength comes from our game model, so injuries and offseason moves are not yet included.</p>
      <Table columns={cols} rows={data.teams} />
    </>
  );
}

export default function Predict() {
  const [params, setParams] = useSearchParams();
  const tab = params.get('tab') || 'games';
  return (
    <>
      <h1 className="t">Predictions</h1>
      <div className="tabs">
        {TABS.map(([k, label]) => <button key={k} className={tab === k ? 'on' : ''} onClick={() => setParams({ tab: k })}>{label}</button>)}
      </div>
      {tab === 'games' && <Games />}
      {tab === 'awards' && <Awards />}
      {tab === 'title' && <Title />}
    </>
  );
}
