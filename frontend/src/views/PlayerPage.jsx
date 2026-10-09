import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { usePlayer } from '../api';
import { Avatar, ErrorBox, Loading, Section, Table, height, money, pct } from '../ui/kit';

const SEASON_COLS = [
  { key: 'label', label: 'Season', left: true }, { key: 'team', label: 'Team', left: true },
  { key: 'g', label: 'GP' }, { key: 'mpg', label: 'MIN' },
  { key: 'pts', label: 'PTS', highlight: true }, { key: 'reb', label: 'REB' }, { key: 'ast', label: 'AST' },
  { key: 'stl', label: 'STL' }, { key: 'blk', label: 'BLK' }, { key: 'tov', label: 'TOV' },
  { key: 'fg_pct', label: 'FG%' }, { key: 'fg3_pct', label: '3P%' }, { key: 'ft_pct', label: 'FT%' }, { key: 'ts_pct', label: 'TS%' },
];
const LOG_COLS = [
  { key: 'game_date', label: 'Date', left: true }, { key: 'opp', label: 'Opp', left: true },
  { key: 'res', label: 'W/L', render: (r) => <span className={r.win ? 'pill good' : 'pill bad'}>{r.win ? 'W' : 'L'}</span> },
  { key: 'min', label: 'MIN' }, { key: 'pts', label: 'PTS', highlight: true }, { key: 'reb', label: 'REB' }, { key: 'ast', label: 'AST' },
  { key: 'stl', label: 'STL' }, { key: 'blk', label: 'BLK' }, { key: 'fg', label: 'FG', render: (r) => `${r.fgm}-${r.fga}` },
  { key: 'fg3', label: '3P', render: (r) => `${r.fg3m}-${r.fg3a}` }, { key: 'plus_minus', label: '+/-' },
];

export default function PlayerPage() {
  const { id } = useParams();
  const { data, isLoading, error } = usePlayer(id);
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !data) return <Loading rows={4} />;
  if (!data.player) return <ErrorBox error={{ message: 'player not found' }} />;
  const { player: p, seasons, career, game_log: log, contract, injury, awards } = data;
  const latest = seasons[0];
  const meta = [p.position, p.jersey_number && `#${p.jersey_number}`, height(p.height_in), p.weight_lb && `${p.weight_lb} lb`, p.age && `Age ${p.age}`].filter(Boolean);
  return (
    <>
      <div className="row wrapx" style={{ gap: 24, alignItems: 'center' }}>
        <Avatar src={p.headshot_url} size="xl" color={p.team_color} alt={p.full_name} />
        <div style={{ flex: 1, minWidth: 240 }}>
          <h1 className="t" style={{ marginBottom: 6 }}>{p.full_name}</h1>
          <div className="muted" style={{ fontSize: 16 }}>
            {p.team_id ? <Link to={`/team/${p.team_id}`} style={{ color: p.team_color, fontWeight: 800 }}>{p.team_name}</Link> : 'Not on a roster'}
            {meta.length > 0 && <> · {meta.join(' · ')}</>}
          </div>
          <div className="row wrapx" style={{ marginTop: 10, gap: 8 }}>
            {injury && <span className="pill bad">{injury.status}{injury.reason ? `: ${injury.reason.slice(0, 60)}` : ''}</span>}
            {contract && <span className="pill">{money(contract.salary)} · {contract.years_remaining ?? '?'} yr left</span>}
            {p.college && <span className="pill">{p.college}</span>}
            {awards.map((a) => <span key={a.award + a.season_label} className="pill good">#{a.rank} {a.award} {a.season_label}</span>)}
          </div>
        </div>
      </div>

      {latest && (
        <div className="grid g4 card" style={{ marginTop: 28 }}>
          {[['PTS', latest.pts], ['REB', latest.reb], ['AST', latest.ast], ['TS%', latest.ts_pct]].map(([k, v]) => (
            <div className="stat" key={k}><b>{v ?? '–'}</b><span>{k} · {latest.label}</span></div>
          ))}
        </div>
      )}

      <Section title="Season by season">
        <Table columns={SEASON_COLS} rows={seasons} summary={career && { label: 'Career', team: '', g: career.g, mpg: career.mpg, pts: career.pts, reb: career.reb, ast: career.ast, stl: career.stl, blk: career.blk, tov: '', fg_pct: career.fg_pct, fg3_pct: career.fg3_pct, ft_pct: '', ts_pct: career.ts_pct }} />
      </Section>
      <Section title="Recent games">
        <Table columns={LOG_COLS} rows={log} />
      </Section>
    </>
  );
}
