-- Migration 005: conference/division data + season projection output

UPDATE teams t SET conference = v.conf, division = v.div
FROM (VALUES
 ('ATL','East','Southeast'),('BOS','East','Atlantic'),('BKN','East','Atlantic'),('CHA','East','Southeast'),
 ('CHI','East','Central'),('CLE','East','Central'),('DET','East','Central'),('IND','East','Central'),
 ('MIA','East','Southeast'),('MIL','East','Central'),('NYK','East','Atlantic'),('ORL','East','Southeast'),
 ('PHI','East','Atlantic'),('TOR','East','Atlantic'),('WAS','East','Southeast'),
 ('DAL','West','Southwest'),('DEN','West','Northwest'),('GSW','West','Pacific'),('HOU','West','Southwest'),
 ('LAC','West','Pacific'),('LAL','West','Pacific'),('MEM','West','Southwest'),('MIN','West','Northwest'),
 ('NOP','West','Southwest'),('OKC','West','Northwest'),('PHX','West','Pacific'),('POR','West','Northwest'),
 ('SAC','West','Pacific'),('SAS','West','Southwest'),('UTA','West','Northwest')
) AS v(abbr, conf, div)
WHERE t.abbreviation = v.abbr AND t.team_id BETWEEN 1610612737 AND 1610612766;

CREATE TABLE IF NOT EXISTS season_projections (
    season_label  VARCHAR(10),
    team_id       INT REFERENCES teams(team_id),
    exp_wins      NUMERIC(5,2),
    exp_losses    NUMERIC(5,2),
    p10th_wins    INT,
    p90th_wins    INT,
    playoff_prob  NUMERIC(5,4),
    top_seed_prob NUMERIC(5,4),
    conf_finals_prob NUMERIC(5,4),
    finals_prob   NUMERIC(5,4),
    title_prob    NUMERIC(5,4),
    rating        NUMERIC(6,3),
    sims          INT,
    updated_at    TIMESTAMP DEFAULT now(),
    PRIMARY KEY (season_label, team_id)
);
