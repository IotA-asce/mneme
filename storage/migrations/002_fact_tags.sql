PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS fact_tag (
  fact_id TEXT NOT NULL,
  tag TEXT NOT NULL COLLATE NOCASE,
  PRIMARY KEY (fact_id, tag),
  FOREIGN KEY (fact_id) REFERENCES fact(fact_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_tag_tag ON fact_tag(tag);
