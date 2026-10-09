import React from 'react';
import { Link } from 'react-router-dom';
import { useTeams } from '../api';
import { Dot, ErrorBox, Loading, Table, pct } from '../ui/kit';

const COLS = [
  { key: 'name', label: 'Team', left: true, render: (r) => <Link to={`/team/${r.team_id}`} className="row" style={{ gap: 10, fontWeight: 700 }}><Dot color={r.color} />{r.name}</Link> },
  { key: 'w', label: 'W' }, { key: 'l', label: 'L' }, { key: 'pts', label: 'PTS' }, { key: 'opp_pts', label: 'OPP' },
  { key: 'net_rating', label: 'NET', highlight: true },
  { key: 'exp_wins', label: 'Proj W', render: (r) => (r.exp_wins != null ? Number(r.exp_wins).toFixed(1) : '–') },
  { key: 'playoff_prob', label: 'Playoffs', render: (r) => pct(r.playoff_prob) },
  { key: 'title_prob', label: 'Title', render: (r) => pct(r.title_prob, 1) },
];

export default function Teams() {
  const { data, isLoading, error } = useTeams();
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !data) return <Loading rows={4} />;
  return (
    <>
      <h1 className="t">Teams</h1>
      <p className="muted">Last completed season ({data.season}) results with next-season projections from 5,000 simulations.</p>
      {['East', 'West'].map((conf) => (
        <div key={conf}>
          <h2 className="s">{conf}ern Conference</h2>
          <Table columns={COLS} rows={data.teams.filter((t) => t.conference === conf)} />
        </div>
      ))}
    </>
  );
}
