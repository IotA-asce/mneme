PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS memory_review (
  review_id TEXT PRIMARY KEY,
  proposal_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'proposed',
  source_turn_text TEXT NOT NULL,
  related_memory_refs_json TEXT NOT NULL,
  created_ts INTEGER NOT NULL,
  applied_ts INTEGER,
  action_result_json TEXT NOT NULL DEFAULT '{}',
  reason TEXT NOT NULL DEFAULT '',
  provenance_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_memory_review_status ON memory_review(status);
CREATE INDEX IF NOT EXISTS idx_memory_review_type ON memory_review(proposal_type);
CREATE INDEX IF NOT EXISTS idx_memory_review_created ON memory_review(created_ts DESC);
