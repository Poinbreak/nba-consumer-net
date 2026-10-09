import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { useTeam } from '../api';
import { Avatar, ErrorBox, Loading, Section, Table, money, pct } from '../ui/kit';

const ROSTER_COLS = [
  { key: 'full_name', label: 'Player', left: true, render: (r) => (
    <Link to={`/player/${r.player_id}`} className="row" style={{ gap: 10 }}>
      <Avatar src={r.headshot_url} /><span style={{ fontWeight: 700 }}>{r.full_name}</span>
      {r.injury && <span className="pill bad">{r.injury}</span>}
    </Link>) },
  { key: 'position', label: 'Pos' }, { key: 'age', label: 'Age' }, { key: 'mpg', label: 'MIN' },
  { key: 'pts', label: 'PTS', highlight: true }, { key: 'reb', label: 'REB' }, { key: 'ast', label: 'AST' },
  { key: 'salary', label: 'Salary', render: (r) => money(r.salary) },
];

export default function TeamPage() {
  const { id } = useParams();
  const { data, isLoading, error } = useTeam(id);
  if (error) return <ErrorBox error={error} />;
  if (isLoading || !data) return <Loading rows={4} />;
  if (!data.team) return <ErrorBox error={{ message: 'team not found' }} />;
  const { team: t, record: r, projection: pr, roster, schedule, history, season } = data;
  const payroll = roster.reduce((a, p) => a + (p.salary || 0), 0);
  return (
    <>
      <div style={{ borderLeft: `6px solid ${t.color}`, paddingLeft: 18 }}>
        <h1 className="t">{t.name}</h1>
        <div className="muted" style={{ fontSize: 16 }}>{t.conference}ern Conference · {t.division} Division</div>
      </div>

      <div className="grid g4 card" style={{ marginTop: 24 }}>
        <div className="stat"><b>{r.w}-{r.l}</b><span>Record {season}</span></div>
        <div className="stat"><b>{r.off_rating ?? '–'}</b><span>Off rating</span></div>
        <div className="stat"><b>{r.def_rating ?? '–'}</b><span>Def rating</span></div>
        <div className="stat"><b>{r.net_rating > 0 ? '+' : ''}{r.net_rating ?? '–'}</b><span>Net rating</span></div>
      </div>

      {pr && (
        <Section title={`Projection · ${pr.season_label}`}>
          <div className="grid g4 card">
            <div className="stat"><b>{Math.round(pr.exp_wins)}–{Math.round(pr.exp_losses)}</b><span>Proj. record ({pr.p10th_wins}–{pr.p90th_wins} wins)</span></div>
            <div className="stat"><b>{pct(pr.playoff_prob)}</b><span>Make playoffs</span></div>
            <div className="stat"><b>{pct(pr.finals_prob, 1)}</b><span>Reach Finals</span></div>
            <div className="stat"><b style={{ color: t.color }}>{pct(pr.title_prob, 1)}</b><span>Win title</span></div>
          </div>
        </Section>
      )}

      <Section title={`Roster · payroll ${money(payroll)}`}>
        <Table columns={ROSTER_COLS} rows={roster} />
      </Section>

      <Section title="Schedule">
        <div className="tbl-wrap"><table className="tbl"><tbody>
          {schedule.map((g) => (
            <tr key={g.game_id}>
              <td className="l">{g.game_date}</td>
              <td className="l">{g.is_home ? 'vs' : '@'} {g.opp_name}</td>
              <td>{g.status === 'Final' ? `${g.is_home ? g.home_score : g.away_score}–${g.is_home ? g.away_score : g.home_score}` : g.status}</td>
              <td>{g.win_prob != null && g.status !== 'Final' ? <span className="pill">{pct(g.win_prob)} to win</span> : ''}</td>
            </tr>
          ))}
        </tbody></table></div>
      </Section>

      <Section title="History">
        <div className="tbl-wrap"><table className="tbl">
          <thead><tr><th>Season</th><th>W</th><th>L</th><th>Net rtg</th></tr></thead>
          <tbody>{history.map((h) => <tr key={h.season}><td>{h.label}</td><td>{h.w}</td><td>{h.l}</td><td>{h.net_rating}</td></tr>)}</tbody>
        </table></div>
      </Section>
    </>
  );
}
