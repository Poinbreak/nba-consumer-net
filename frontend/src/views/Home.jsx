import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAwards, useScoreboard, useTitleOdds } from '../api';
import { Avatar, Dot, Loading, ProbBar, SearchBox, Section, pct } from '../ui/kit';

const EXAMPLES = [
  'Luka Doncic last 10 games', 'most assists this season', 'SGA points per game', 'Thunder record',
  'Wemby blocks career', 'Jokic vs Lakers', 'highest 3P% last season',
];

export function GameCard({ g }) {
  const live = g.status === 'Live';
  const final = g.status === 'Final';
  const hw = final && g.home_score > g.away_score;
  const aw = final && g.away_score > g.home_score;
  const when = !live && !final ? 'Upcoming' : final ? 'Final' : `Q${g.quarter} ${g.time_remaining}`;
  return (
    <Link to={`/team/${g.home_id}`} className="card game">
      <div className="row sp" style={{ marginBottom: 12 }}>
        <span className={`pill${live ? ' live' : ''}`}>{live && '● '}{when}</span>
        {g.predicted_score && <span className="faint num" style={{ fontSize: 12 }}>Proj {Math.round(g.predicted_score.away)}–{Math.round(g.predicted_score.home)}</span>}
      </div>
      <div className={`tm${final && !aw ? ' lose' : ''}`}><Dot color={g.away_color} />{g.away_name}<span className="sc">{g.away_score ?? ''}</span></div>
      <div className={`tm${final && !hw ? ' lose' : ''}`} style={{ marginTop: 8 }}><Dot color={g.home_color} />{g.home_name}<span className="sc">{g.home_score ?? ''}</span></div>
      {g.home_win_prob != null && (
        <div style={{ marginTop: 14 }}>
          <ProbBar homeProb={g.home_win_prob} homeColor={g.home_color} awayColor={g.away_color} homeAbbr={g.home_abbr} awayAbbr={g.away_abbr} />
        </div>
      )}
    </Link>
  );
}

export default function Home() {
  const nav = useNavigate();
  const sb = useScoreboard();
  const odds = useTitleOdds();
  const awards = useAwards();
  const mvp = awards.data?.awards?.MVP?.slice(0, 3);
  return (
    <>
      <h1 className="t" style={{ fontSize: 'clamp(32px, 5vw, 56px)', marginTop: 20 }}>Ask anything about the NBA.</h1>
      <p className="muted" style={{ fontSize: 18, margin: '0 0 24px' }}>Stats, leaders, trends and model predictions, in plain English.</p>
      <SearchBox big placeholder="e.g. Luka Doncic last 10 games" />
      <div className="chips">
        {EXAMPLES.map((e) => <button key={e} className="chip" onClick={() => nav(`/ask?q=${encodeURIComponent(e)}`)}>{e}</button>)}
      </div>

      <Section title={sb.data?.date ? `Games · ${sb.data.date}` : 'Games'} more={{ to: '/scores', label: 'All scores' }}>
        {sb.isLoading ? <Loading /> : sb.data?.games?.length ? (
          <div className="grid g3">{sb.data.games.slice(0, 6).map((g) => <GameCard key={g.game_id} g={g} />)}</div>
        ) : <div className="card empty">No games scheduled.</div>}
      </Section>

      <div className="grid g2" style={{ marginTop: 8 }}>
        <div>
          <Section title={`Title odds · ${odds.data?.season ?? ''}`} more={{ to: '/predict?tab=title', label: 'Full table' }}>
            <div className="card">
              {odds.isLoading ? <Loading rows={4} /> : (odds.data?.teams ?? []).slice(0, 8).map((t) => (
                <Link to={`/team/${t.team_id}`} key={t.team_id} className="row" style={{ padding: '7px 0' }}>
                  <Dot color={t.color} /><span style={{ fontWeight: 700, width: 44 }}>{t.abbr}</span>
                  <div className="bar" style={{ flex: 1 }}><i style={{ width: `${Math.min(100, t.title_prob * 300)}%`, background: t.color }} /></div>
                  <span className="num" style={{ width: 52, textAlign: 'right', fontWeight: 800 }}>{pct(t.title_prob, 1)}</span>
                </Link>
              ))}
            </div>
          </Section>
        </div>
        <div>
          <Section title={`MVP race · ${awards.data?.season ?? ''}`} more={{ to: '/predict?tab=awards', label: 'All awards' }}>
            <div className="card">
              {awards.isLoading ? <Loading rows={3} /> : (mvp ?? []).map((p) => (
                <Link to={`/player/${p.player_id}`} key={p.player_id} className="row" style={{ padding: '8px 0' }}>
                  <span className="faint num" style={{ width: 16 }}>{p.rank}</span>
                  <Avatar src={p.headshot_url} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 800 }}>{p.player}</div>
                    <div className="muted" style={{ fontSize: 12 }}>{p.team} · {p.stats?.pts}/{p.stats?.trb}/{p.stats?.ast}</div>
                  </div>
                  <span className="num" style={{ fontWeight: 800, color: p.team_color }}>{pct(p.share, 0)}</span>
                </Link>
              ))}
              <div className="faint" style={{ fontSize: 12, marginTop: 8 }}>Projected vote share from our XGBoost award model.</div>
            </div>
          </Section>
        </div>
      </div>
    </>
  );
}
