CREATE TABLE IF NOT EXISTS snapshots (
  address TEXT NOT NULL, deployment TEXT NOT NULL, block_number INTEGER NOT NULL,
  queried_at TEXT NOT NULL, payload TEXT NOT NULL,
  PRIMARY KEY(address,deployment,block_number)
);
CREATE INDEX IF NOT EXISTS snapshots_address_block ON snapshots(address,block_number DESC);
CREATE TABLE IF NOT EXISTS reports (
  report_id TEXT PRIMARY KEY, address TEXT NOT NULL, created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL, payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS reports_expiry ON reports(expires_at);
CREATE TABLE IF NOT EXISTS quotas (
  bucket TEXT NOT NULL, window INTEGER NOT NULL, count INTEGER NOT NULL,
  PRIMARY KEY(bucket,window)
);
CREATE TABLE IF NOT EXISTS explanations (
  report_id TEXT NOT NULL, intent TEXT NOT NULL, expires_at TEXT NOT NULL, payload TEXT NOT NULL,
  PRIMARY KEY(report_id,intent)
);
