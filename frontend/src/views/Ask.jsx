import React from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAsk } from '../api';
import { Avatar, ErrorBox, Loading, SearchBox, Table } from '../ui/kit';

/** Renders the first number-ish chunk of the answer in the accent colour, StatMuse style. */
function Answer({ text }) {
  const parts = text.split(/(\d+(?:\.\d+)?(?:-\d+)?%?)/);
  return <p className="answer">{parts.map((p, i) => (i % 2 ? <em key={i}>{p}</em> : p))}</p>;
}

export default function Ask() {
  const [params] = useSearchParams();
  const text = params.get('q') || '';
  const nav = useNavigate();
  const { data, isLoading, error } = useAsk(text);

  React.useEffect(() => {
    if (data?.kind === 'redirect' && data.link) nav(data.link, { replace: true });
  }, [data, nav]);

  const cols = (data?.columns ?? []).map((c) =>
    c.key === 'player'
      ? { ...c, left: true, render: (r) => <Link to={r.link || '#'} style={{ fontWeight: 700 }}>{r.player}</Link> }
      : c);

  return (
    <>
      <SearchBox big initial={text} placeholder="Ask another question…" key={text} />
      <div style={{ height: 28 }} />
      {isLoading ? <Loading rows={3} /> : error ? <ErrorBox error={error} /> : data && (
        <>
          {data.player && (
            <Link to={data.link} className="row" style={{ marginBottom: 12 }}>
              <Avatar src={data.player.headshot_url} />
              <span className="muted" style={{ fontWeight: 700 }}>{data.player.team} {data.player.position && `· ${data.player.position}`}</span>
            </Link>
          )}
          <Answer text={data.answer} />
          {data.rows?.length > 0 && (
            <>
              {data.title && <h2 className="s">{data.title}</h2>}
              <Table columns={cols} rows={data.rows} summary={data.summary} />
            </>
          )}
          {data.link && data.kind !== 'leaders' && <p style={{ marginTop: 20 }}><Link to={data.link} style={{ color: 'var(--accent)', fontWeight: 700 }}>Full profile →</Link></p>}
        </>
      )}
    </>
  );
}
