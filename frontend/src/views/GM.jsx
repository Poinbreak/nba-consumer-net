import React, { useEffect, useMemo, useState } from 'react';
import { useGmLeague, useGmRoster, useGmSim, useGmTrade } from '../api';
import { Avatar, Dot, ErrorBox, Loading, Section, money, pct } from '../ui/kit';

const STORE = 'nbanet.gm.v1';
const load = () => { try { return JSON.parse(localStorage.getItem(STORE)) || {}; } catch { return {}; } };
const save = (s) => { try { localStorage.setItem(STORE, JSON.stringify(s)); } catch { /* private mode: game still works, just not saved */ } };

const ovrClass = (o) => (o >= 85 ? 'e' : o >= 75 ? 'g' : o >= 68 ? 'm' : o >= 60 ? 'l' : 'p');
export const Ovr = ({ v }) => <span className={`ovr ${ovrClass(v)}`}>{v}</span>;
const sign = (n, d = 1) => `${n > 0 ? '+' : ''}${n.toFixed(d)}`;
const Delta = ({ a, b, d = 1, invert = false }) => {
  const diff = b - a;
  if (Math.abs(diff) < 0.05) return <span className="faint">±0.0</span>;
  const good = invert ? diff < 0 : diff > 0;
  return <span className={`delta ${good ? 'up' : 'down'}`}>{sign(diff, d)}</span>;
};

function PlayerTag({ p }) {
  return (
    <div className="row" style={{ gap: 10, minWidth: 0 }}>
      <Avatar src={p.headshot} />
      <div style={{ minWidth: 0 }}>
        <div style={{ fontWeight: 800, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{p.name}</div>
        <div className="muted" style={{ fontSize: 12 }}>{[p.pos, p.age && `${p.age}y`, p.line && `${p.line.pts}/${p.line.reb}/${p.line.ast}`].filter(Boolean).join(' · ')}</div>
      </div>
    </div>
  );
}

function CapBar({ payroll, cap }) {
  const max = cap.apron2 * 1.12;
  const mark = (v, label) => (
    <>
      <b style={{ left: `${(v / max) * 100}%` }} />
      <span style={{ left: `${(v / max) * 100}%` }}>{label}</span>
    </>
  );
  const color = payroll > cap.apron2 ? 'var(--bad)' : payroll > cap.apron1 ? '#fb923c' : payroll > cap.tax ? '#fbbf24' : payroll > cap.cap ? 'var(--accent)' : 'var(--good)';
  return (
    <div className="cap">
      <i style={{ width: `${Math.min(100, (payroll / max) * 100)}%`, background: color }} />
      {mark(cap.cap, 'Cap')}{mark(cap.tax, 'Tax')}{mark(cap.apron1, '1st apron')}{mark(cap.apron2, '2nd apron')}
    </div>
  );
}

function TeamPicker({ league, onPick }) {
  return (
    <>
      <h1 className="t">GM Mode</h1>
      <p className="muted" style={{ fontSize: 17, maxWidth: 720 }}>
        Take over any franchise. Real rosters, real contracts, CBA-style trade rules. Every move updates your projected
        record and ratings, then simulate the season and the playoffs.
      </p>
      <h2 className="s">Choose your team</h2>
      <div className="grid g3">
        {league.teams.map((t) => (
          <button key={t.team_id} className="card teamcard" onClick={() => onPick(t.team_id)}>
            <div className="row sp">
              <div className="row" style={{ gap: 10 }}><Dot color={t.color} /><b>{t.name}</b></div>
              <Ovr v={t.ovr} />
            </div>
            <div className="muted num" style={{ fontSize: 13, marginTop: 10 }}>
              Proj. {Math.round(t.wins)}–{82 - Math.round(t.wins)} · {money(t.payroll)} · {t.cap_status}
            </div>
          </button>
        ))}
      </div>
    </>
  );
}

function RosterView({ data }) {
  return (
    <div className="tbl-wrap">
      <table className="tbl">
        <thead><tr><th className="l">Player</th><th>OVR</th><th>MPG</th><th>Salary</th><th>Yrs</th><th className="l">Status</th></tr></thead>
        <tbody>
          {data.players.map((p) => (
            <tr key={p.player_id}>
              <td className="l"><PlayerTag p={p} /></td>
              <td><Ovr v={p.ovr} /></td>
              <td>{p.mpg || '–'}</td>
              <td>{money(p.salary)}</td>
              <td>{p.years ?? '–'}</td>
              <td className="l">
                {p.injury && <span className="pill bad">{p.injury}</span>}{' '}
                {p.locked && <span className="pill" title="Recently signed: cannot be traded yet">Locked</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PickList({ team, picks, setPicks, label }) {
  const { data } = team;
  if (!data) return <Loading rows={4} />;
  const toggle = (id) => setPicks(picks.includes(id) ? picks.filter((x) => x !== id) : [...picks, id]);
  return (
    <div className="card" style={{ padding: 10 }}>
      <div className="row sp" style={{ padding: '6px 10px 10px' }}>
        <b>{label}</b><span className="muted num" style={{ fontSize: 13 }}>{money(data.players.filter((p) => picks.includes(p.player_id)).reduce((a, p) => a + p.salary, 0))} out</span>
      </div>
      <div style={{ maxHeight: 420, overflowY: 'auto' }}>
        {data.players.map((p) => (
          <label key={p.player_id} className={`pick${picks.includes(p.player_id) ? ' on' : ''}${p.locked ? ' off' : ''}`}>
            <input type="checkbox" checked={picks.includes(p.player_id)} disabled={p.locked} onChange={() => toggle(p.player_id)} />
            <div style={{ flex: 1, minWidth: 0 }}><PlayerTag p={p} /></div>
            <Ovr v={p.ovr} />
            <span className="num muted" style={{ width: 62, textAlign: 'right', fontSize: 13 }}>{money(p.salary)}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

function SideSummary({ side, name, color }) {
  const b = side.before, a = side.after;
  const rows = [
    ['Proj. wins', b.wins, a.wins, 1, false], ['Offense', b.off, a.off, 1, false], ['Defense (pts allowed)', b.def, a.def, 1, true],
    ['Net rating', b.net, a.net, 1, false], ['Team OVR', b.ovr, a.ovr, 0, false],
  ];
  return (
    <div className="card" style={{ borderTop: `3px solid ${color}` }}>
      <div className="row sp" style={{ marginBottom: 8 }}><b>{name}</b><span className={`pill${side.post_payroll > b.payroll ? '' : ' good'}`}>{money(b.payroll)} → {money(side.post_payroll)}</span></div>
      <table className="tbl"><tbody>
        {rows.map(([label, x, y, d, inv]) => (
          <tr key={label}><td className="l muted">{label}</td><td>{x.toFixed(d)}</td><td className="faint">→</td><td style={{ fontWeight: 800 }}>{y.toFixed(d)}</td><td><Delta a={x} b={y} d={d} invert={inv} /></td></tr>
        ))}
      </tbody></table>
    </div>
  );
}

function TradeView({ league, myId, rosters, onExecute }) {
  const partners = league.teams.filter((t) => t.team_id !== myId);
  const [partnerId, setPartnerId] = useState(partners[0]?.team_id);
  const [mine, setMine] = useState([]);
  const [theirs, setTheirs] = useState([]);
  const myTeam = useGmRoster(myId, rosters);
  const theirTeam = useGmRoster(partnerId, rosters);
  useEffect(() => { setTheirs([]); }, [partnerId]);
  const active = mine.length + theirs.length > 0;
  const body = { team_a: myId, team_b: partnerId, a_gives: mine, b_gives: theirs, rosters };
  const trade = useGmTrade(body, active && !!partnerId);
  const res = active ? trade.data : null;
  const a = league.teams.find((t) => t.team_id === myId), b = league.teams.find((t) => t.team_id === partnerId);

  return (
    <>
      <div className="row wrapx" style={{ marginBottom: 14 }}>
        <span className="muted">Trade with</span>
        <select className="sel" value={partnerId} onChange={(e) => setPartnerId(Number(e.target.value))}>
          {partners.map((t) => <option key={t.team_id} value={t.team_id}>{t.name}</option>)}
        </select>
        <span className="faint" style={{ fontSize: 13 }}>Tick the players each side sends. Validity and projections update live.</span>
      </div>
      <div className="grid g2">
        <PickList team={myTeam} picks={mine} setPicks={setMine} label={`You send · ${a.abbr}`} />
        <PickList team={theirTeam} picks={theirs} setPicks={setTheirs} label={`You get · ${b.abbr}`} />
      </div>

      {active && (
        <Section title="Trade analysis">
          {trade.isFetching && !res ? <Loading rows={2} /> : res && (
            <>
              <div className="grid g2">
                <SideSummary side={res.a} name={a.name} color={a.color} />
                <SideSummary side={res.b} name={b.name} color={b.color} />
              </div>
              {res.problems?.map((m) => <div key={m} className="msg bad">✕ {m}</div>)}
              {res.warnings?.map((m) => <div key={m} className="msg warn">! {m}</div>)}
              {res.valid && <div className="msg ok">✓ This trade works under the (simplified) CBA rules.</div>}
              <div className="row" style={{ marginTop: 14, gap: 12 }}>
                <button className="btn" disabled={!res.valid} onClick={() => {
                  onExecute(res.after_rosters, `Traded ${mine.length} for ${theirs.length} with ${b.name}`);
                  setMine([]); setTheirs([]);
                }}>Execute trade</button>
                <button className="btn ghost" onClick={() => { setMine([]); setTheirs([]); }}>Clear</button>
                <span className="faint" style={{ fontSize: 12 }}>The other team’s GM always accepts a legal trade in this version.</span>
              </div>
            </>
          )}
        </Section>
      )}
    </>
  );
}

function SeasonView({ league, myId, rosters, baseline }) {
  const [run, setRun] = useState(false);
  const now = useGmSim(rosters, run);
  const start = useGmSim({}, run && Object.keys(rosters).length > 0);   // league as it was before your moves
  const base = Object.keys(rosters).length ? start.data : now.data;
  const baseById = useMemo(() => Object.fromEntries((base?.teams ?? []).map((t) => [t.team_id, t])), [base]);
  const mine = now.data?.teams.find((t) => t.team_id === myId);
  const rank = now.data ? now.data.teams.findIndex((t) => t.team_id === myId) + 1 : null;
  return (
    <>
      {!run && (
        <div className="card empty">
          <p style={{ marginTop: 0 }}>Simulate the 2026–27 schedule and playoffs 800 times with your current rosters.</p>
          <button className="btn" onClick={() => setRun(true)}>Simulate season</button>
        </div>
      )}
      {run && (now.isLoading || !now.data) && <Loading rows={3} />}
      {run && now.error && <ErrorBox error={now.error} />}
      {mine && (
        <>
          <div className="grid g4 card">
            <div className="stat"><b>{mine.exp_wins}–{(82 - mine.exp_wins).toFixed(1)}</b><span>Proj. record ({mine.p10}–{mine.p90} wins)</span></div>
            <div className="stat"><b>{pct(mine.playoffs)}</b><span>Make playoffs</span></div>
            <div className="stat"><b>{pct(mine.finals, 1)}</b><span>Reach Finals</span></div>
            <div className="stat"><b style={{ color: mine.color }}>{pct(mine.title, 1)}</b><span>Win title</span></div>
          </div>
          <p className="muted" style={{ fontSize: 13 }}>You rank #{rank} of 30 in projected wins.{Object.keys(rosters).length > 0 && baseById[myId] && <> Before your trades: {baseById[myId].exp_wins} wins, {pct(baseById[myId].title, 1)} title odds.</>}</p>
          <Section title="League projection">
            <div className="tbl-wrap"><table className="tbl">
              <thead><tr><th className="l">Team</th><th>Proj W</th><th>Δ vs start</th><th>Playoffs</th><th>Finals</th><th>Title</th></tr></thead>
              <tbody>{now.data.teams.map((t) => (
                <tr key={t.team_id} style={t.team_id === myId ? { background: 'var(--panel2)' } : undefined}>
                  <td className="l"><span className="row" style={{ gap: 10, fontWeight: 700 }}><Dot color={t.color} />{t.name}</span></td>
                  <td>{t.exp_wins}</td>
                  <td>{baseById[t.team_id] ? <Delta a={baseById[t.team_id].exp_wins} b={t.exp_wins} /> : '–'}</td>
                  <td>{pct(t.playoffs)}</td><td>{pct(t.finals, 1)}</td><td className="hl">{pct(t.title, 1)}</td>
                </tr>))}</tbody>
            </table></div>
          </Section>
        </>
      )}
    </>
  );
}

const TABS = [['roster', 'Roster'], ['trade', 'Trade machine'], ['season', 'Season sim'], ['log', 'Moves']];

export default function GM() {
  const [state, setState] = useState(load);
  const [tab, setTab] = useState('roster');
  useEffect(() => save(state), [state]);
  const rosters = state.rosters || {};
  const league = useGmLeague(rosters);
  const myId = state.teamId;
  const myRoster = useGmRoster(myId, rosters);

  if (league.error) return <ErrorBox error={league.error} />;
  if (!league.data) return <Loading rows={4} />;
  if (!myId) return <TeamPicker league={league.data} onPick={(id) => setState({ teamId: id, rosters: {}, log: [] })} />;

  const me = league.data.teams.find((t) => t.team_id === myId);
  const execute = (afterRosters, text) => setState((s) => ({ ...s, rosters: { ...(s.rosters || {}), ...afterRosters }, log: [{ text, at: new Date().toISOString() }, ...(s.log || [])] }));

  return (
    <>
      <div className="row sp wrapx">
        <div style={{ borderLeft: `6px solid ${me.color}`, paddingLeft: 16 }}>
          <h1 className="t" style={{ marginBottom: 2 }}>{me.name}</h1>
          <div className="muted">GM Mode · {league.data.season} · {me.cap_status}</div>
        </div>
        <div className="row">
          <button className="btn ghost" onClick={() => setState({ rosters: state.rosters, log: state.log })}>Change team</button>
          <button className="btn ghost" onClick={() => { if (window.confirm('Undo every trade and start over?')) setState({ teamId: myId, rosters: {}, log: [] }); }}>Reset league</button>
        </div>
      </div>

      <div className="grid g4 card" style={{ marginTop: 20 }}>
        <div className="stat"><b>{Math.round(me.wins)}–{82 - Math.round(me.wins)}</b><span>Projected record</span></div>
        <div className="stat"><b>{me.off.toFixed(1)}</b><span>Offense (pts/100)</span></div>
        <div className="stat"><b>{me.def.toFixed(1)}</b><span>Defense (pts allowed/100)</span></div>
        <div className="stat"><b>{sign(me.net)}</b><span>Net rating · OVR {me.ovr}</span></div>
      </div>
      <div className="card" style={{ marginTop: 14, paddingBottom: 6 }}>
        <div className="row sp"><b>Payroll {money(me.payroll)}</b><span className="muted" style={{ fontSize: 13 }}>{league.data.cap.label}</span></div>
        <CapBar payroll={me.payroll} cap={league.data.cap} />
      </div>
      <p className="faint" style={{ fontSize: 12, margin: '10px 0 0' }}>
        Ratings project next season from each player’s past production (backtested correlation with real results: 0.52 on net rating). Trade
        <i> changes</i> are more reliable than absolute numbers. Box scores can’t see defense, so defensive projections vary little between teams.
      </p>

      <div className="tabs" style={{ marginTop: 20 }}>
        {TABS.map(([k, label]) => <button key={k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{label}</button>)}
      </div>
      {tab === 'roster' && (myRoster.data ? <RosterView data={myRoster.data} /> : <Loading rows={4} />)}
      {tab === 'trade' && <TradeView league={league.data} myId={myId} rosters={rosters} onExecute={execute} />}
      {tab === 'season' && <SeasonView league={league.data} myId={myId} rosters={rosters} />}
      {tab === 'log' && (
        (state.log || []).length ? (
          <div className="card">{state.log.map((l, i) => <div key={i} className="row sp" style={{ padding: '8px 0', borderBottom: '1px solid var(--line)' }}><span>{l.text}</span><span className="faint" style={{ fontSize: 12 }}>{new Date(l.at).toLocaleString()}</span></div>)}</div>
        ) : <div className="card empty">No moves yet. Make a trade to see it here.</div>
      )}
    </>
  );
}
