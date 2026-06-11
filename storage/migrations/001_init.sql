PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migration (
  migration_id TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  checksum_sha256 TEXT NOT NULL,
  applied_ts INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_trace (
  trace_id TEXT PRIMARY KEY,
  created_ts INTEGER NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT,
  summary TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.5,
  salience REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS episode (
  episode_id TEXT PRIMARY KEY,
  start_ts INTEGER NOT NULL,
  end_ts INTEGER NOT NULL,
  context_json TEXT NOT NULL,
  summary TEXT NOT NULL,
  salience REAL NOT NULL,
  confidence REAL NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  created_ts INTEGER NOT NULL,
  updated_ts INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS episode_entity (
  episode_id TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  role TEXT,
  PRIMARY KEY (episode_id, entity_id),
  FOREIGN KEY (episode_id) REFERENCES episode(episode_id)
);

CREATE TABLE IF NOT EXISTS fact (
  fact_id TEXT PRIMARY KEY,
  subject TEXT NOT NULL,
  predicate TEXT NOT NULL,
  object_json TEXT NOT NULL,
  confidence REAL NOT NULL,
  source_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  first_seen_ts INTEGER NOT NULL,
  last_confirmed_ts INTEGER,
  supersedes_fact_id TEXT
);

CREATE TABLE IF NOT EXISTS fact_support (
  fact_id TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 1.0,
  PRIMARY KEY (fact_id, episode_id),
  FOREIGN KEY (fact_id) REFERENCES fact(fact_id),
  FOREIGN KEY (episode_id) REFERENCES episode(episode_id)
);

CREATE TABLE IF NOT EXISTS memory_summary (
  summary_id TEXT PRIMARY KEY,
  summary_type TEXT NOT NULL,
  scope_key TEXT NOT NULL,
  summary TEXT NOT NULL,
  confidence REAL NOT NULL,
  start_ts INTEGER,
  end_ts INTEGER,
  created_ts INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS meta_memory (
  memory_id TEXT NOT NULL,
  memory_kind TEXT NOT NULL,
  source_type TEXT NOT NULL,
  provenance_json TEXT NOT NULL,
  last_retrieved_ts INTEGER,
  retrieval_count INTEGER NOT NULL DEFAULT 0,
  contradiction_score REAL NOT NULL DEFAULT 0.0,
  speakability TEXT NOT NULL DEFAULT 'normal',
  PRIMARY KEY (memory_id, memory_kind)
);

CREATE TABLE IF NOT EXISTS working_context_snapshot (
  snapshot_id TEXT PRIMARY KEY,
  created_ts INTEGER NOT NULL,
  context_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_episode_time ON episode(start_ts, end_ts);
CREATE INDEX IF NOT EXISTS idx_episode_salience ON episode(salience DESC);
CREATE INDEX IF NOT EXISTS idx_fact_spo ON fact(subject, predicate);
CREATE INDEX IF NOT EXISTS idx_fact_status ON fact(status);
CREATE INDEX IF NOT EXISTS idx_raw_trace_created ON raw_trace(created_ts);
