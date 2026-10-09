import React, { useEffect, useRef, useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useSearch } from '../api';

export const pct = (x, d = 0) => (x == null ? '–' : `${(x * 100).toFixed(d)}%`);
export const money = (n) => (!n ? '–' : `$${(n / 1e6).toFixed(1)}M`);
export const ordinal = (n) => `${n}${['th', 'st', 'nd', 'rd'][(n % 100 > 10 && n % 100 < 14) || n % 10 > 3 ? 0 : n % 10]}`;
export const height = (inches) => (inches ? `${Math.floor(inches / 12)}'${Math.round(inches % 12)}"` : '–');

export function Dot({ color }) {
  return <span className="dot" style={{ background: color || 'var(--faint)' }} />;
}

export function Avatar({ src, size, color, alt = '' }) {
  const [bad, setBad] = useState(false);
  const cls = `avatar${size === 'xl' ? ' xl' : ''}`;
  if (!src || bad) return <span className={cls} style={{ '--tc': color }} />;
  return <img className={cls} style={{ '--tc': color }} src={src} alt={alt} loading="lazy" onError={() => setBad(true)} />;
}

export function Section({ title, more, children }) {
  return (
    <>
      <h2 className="s">
        {title}
        {more && <Link className="more" to={more.to}>{more.label} →</Link>}
      </h2>
      {children}
    </>
  );
}

export function Loading({ rows = 3 }) {
  return (
    <div className="grid">
      {Array.from({ length: rows }).map((_, i) => <div key={i} className="skeleton" />)}
    </div>
  );
}

export function ErrorBox({ error }) {
  return (
    <div className="card empty">
      Couldn’t load this. {error?.message && <span className="faint">({error.message})</span>}
      <div className="faint" style={{ marginTop: 6, fontSize: 13 }}>Is the API running on port 8000?</div>
    </div>
  );
}

/** Home-team win probability bar, coloured by each side's team colour. */
export function ProbBar({ homeProb, homeColor, awayColor, homeAbbr, awayAbbr }) {
  if (homeProb == null) return null;
  const h = homeProb * 100;
  return (
    <div>
      <div className="bar">
        <i style={{ width: `${100 - h}%`, background: awayColor }} />
        <i style={{ width: `${h}%`, background: homeColor }} />
      </div>
      <div className="row sp num" style={{ fontSize: 12, marginTop: 6, fontWeight: 700 }}>
        <span>{awayAbbr} {(100 - h).toFixed(0)}%</span>
        <span>{homeAbbr} {h.toFixed(0)}%</span>
      </div>
    </div>
  );
}

/** columns: [{key,label,highlight?,left?,render?}]; rows: objects. Rows with `link` become clickable names. */
export function Table({ columns, rows, summary, onRow }) {
  return (
    <div className="tbl-wrap">
      <table className="tbl">
        <thead>
          <tr>{columns.map((c) => <th key={c.key} className={c.left ? 'l' : ''}>{c.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.id ?? r.player_id ?? i} onClick={onRow ? () => onRow(r) : undefined} style={onRow ? { cursor: 'pointer' } : undefined}>
              {columns.map((c) => (
                <td key={c.key} className={`${c.highlight ? 'hl' : ''} ${c.left ? 'l' : ''}`}>
                  {c.render ? c.render(r) : (r[c.key] ?? '–')}
                </td>
              ))}
            </tr>
          ))}
          {summary && (
            <tr className="sum">
              {columns.map((c) => <td key={c.key} className={c.left ? 'l' : ''}>{summary[c.key] ?? ''}</td>)}
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

/** One input for both: pick a player from the dropdown, or press Enter to ask a free-text question. */
export function SearchBox({ big = false, placeholder = 'Search players or ask a question…', initial = '' }) {
  const [text, setText] = useState(initial);
  const [debounced, setDebounced] = useState('');
  const [open, setOpen] = useState(false);
  const [sel, setSel] = useState(-1);
  const nav = useNavigate();
  const box = useRef(null);
  useEffect(() => { const t = setTimeout(() => setDebounced(text.trim()), 180); return () => clearTimeout(t); }, [text]);
  useEffect(() => {
    const close = (e) => { if (!box.current?.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);
  const { data } = useSearch(debounced);
  const results = open && debounced.length >= 2 ? data?.results ?? [] : [];

  const ask = () => { if (text.trim()) { setOpen(false); nav(`/ask?q=${encodeURIComponent(text.trim())}`); } };
  const go = (p) => { setOpen(false); setText(''); nav(`/player/${p.player_id}`); };
  const onKey = (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setSel((s) => Math.min(s + 1, results.length - 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setSel((s) => Math.max(s - 1, -1)); }
    else if (e.key === 'Enter') { sel >= 0 && results[sel] ? go(results[sel]) : ask(); }
    else if (e.key === 'Escape') setOpen(false);
  };
  return (
    <div className={`sbox${big ? ' big' : ''}`} ref={box}>
      <input
        value={text} placeholder={placeholder} aria-label="Search players or ask a question"
        onChange={(e) => { setText(e.target.value); setOpen(true); setSel(-1); }}
        onFocus={() => setOpen(true)} onKeyDown={onKey}
      />
      {results.length > 0 && (
        <div className="sdrop">
          {results.map((p, i) => (
            <a key={p.player_id} href={`/player/${p.player_id}`} className={i === sel ? 'sel' : ''}
               onClick={(e) => { e.preventDefault(); go(p); }}>
              <Avatar src={p.headshot_url} />
              <span style={{ fontWeight: 700 }}>{p.full_name}</span>
              <span className="muted" style={{ marginLeft: 'auto', fontSize: 12 }}>{[p.team, p.position].filter(Boolean).join(' · ')}</span>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

const NAV = [
  ['/', 'Home', true], ['/scores', 'Scores'], ['/predict', 'Predict'], ['/teams', 'Teams'], ['/odds', 'Odds'], ['/gm', 'GM Mode'],
];

export function Shell({ children }) {
  return (
    <div className="app">
      <header className="hdr">
        <div className="wrap hdr-in">
          <Link to="/" className="logo">NBA<b>·</b>NET</Link>
          <nav className="nav">
            {NAV.map(([to, label, end]) => <NavLink key={to} to={to} end={end}>{label}</NavLink>)}
          </nav>
          <div className="hdr-search"><SearchBox /></div>
        </div>
      </header>
      <div className="tabbar">
        {NAV.map(([to, label, end]) => <NavLink key={to} to={to} end={end}>{label}</NavLink>)}
      </div>
      <main className="wrap page">{children}</main>
    </div>
  );
}
