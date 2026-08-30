"""Data model (SQLite). Raw samples -> ticks counted as an aggregate, so the
score can be recomputed from scratch during a dispute (auditability)."""
import sqlite3
import threading
import time

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS samples(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hill_id TEXT,
  team_token TEXT,          -- NULL = agent alive but no valid owner
  sig_valid INTEGER,
  nonce INTEGER,
  ts_agent REAL,
  ts_server REAL,
  source_ip TEXT,
  clock_skew_ms INTEGER
);
CREATE TABLE IF NOT EXISTS sla_checks(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hill_id TEXT, ts_server REAL, status TEXT, latency_ms INTEGER
);
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_server REAL, hill_id TEXT, type TEXT, details TEXT, points INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS ticks(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_second INTEGER, hill_id TEXT, team TEXT, points INTEGER DEFAULT 1,
  UNIQUE(ts_second, hill_id)         -- at most 1 tick per hill per second
);
CREATE TABLE IF NOT EXISTS flags(
  flag_id TEXT PRIMARY KEY, hill_id TEXT, kind TEXT, flag_hash TEXT
);
CREATE TABLE IF NOT EXISTS flag_submissions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_server REAL, team TEXT, flag_id TEXT, correct INTEGER
);
CREATE INDEX IF NOT EXISTS idx_samples_hill ON samples(hill_id, ts_server);
CREATE INDEX IF NOT EXISTS idx_sla_hill ON sla_checks(hill_id, ts_server);
"""


class DB:
    def __init__(self, path):
        self.path = path
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        try:
            self.conn.execute("ALTER TABLE ticks ADD COLUMN points INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass
        self.conn.commit()

    def _exec(self, sql, args=()):
        with _lock:
            cur = self.conn.execute(sql, args)
            self.conn.commit()
            return cur

    def _query(self, sql, args=()):
        with _lock:
            return self.conn.execute(sql, args).fetchall()

    # --- writes ---
    def insert_sample(self, hill_id, token, sig_valid, nonce, ts_agent, ts_server, ip, skew_ms):
        self._exec(
            "INSERT INTO samples(hill_id,team_token,sig_valid,nonce,ts_agent,ts_server,source_ip,clock_skew_ms)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (hill_id, token, int(sig_valid), nonce, ts_agent, ts_server, ip, skew_ms))

    def insert_sla(self, hill_id, status, latency_ms):
        self._exec("INSERT INTO sla_checks(hill_id,ts_server,status,latency_ms) VALUES(?,?,?,?)",
                   (hill_id, time.time(), status, latency_ms))

    def insert_event(self, hill_id, etype, details="", points=0):
        self._exec("INSERT INTO events(ts_server,hill_id,type,details,points) VALUES(?,?,?,?,?)",
                   (time.time(), hill_id, etype, details, points))

    def award_tick(self, ts_second, hill_id, team, points=1):
        try:
            self._exec("INSERT INTO ticks(ts_second,hill_id,team,points) VALUES(?,?,?,?)",
                       (ts_second, hill_id, team, points))
            return True
        except sqlite3.IntegrityError:
            return False  # this second was already awarded

    def load_flag(self, flag_id, hill_id, kind, flag_hash):
        self._exec("INSERT OR REPLACE INTO flags(flag_id,hill_id,kind,flag_hash) VALUES(?,?,?,?)",
                   (flag_id, hill_id, kind, flag_hash))

    def insert_submission(self, team, flag_id, correct):
        self._exec("INSERT INTO flag_submissions(ts_server,team,flag_id,correct) VALUES(?,?,?,?)",
                   (time.time(), team, flag_id, int(correct)))

    # --- reads ---
    def last_nonce(self, hill_id):
        r = self._query("SELECT MAX(nonce) n FROM samples WHERE hill_id=? AND sig_valid=1", (hill_id,))
        return r[0]["n"] if r and r[0]["n"] is not None else -1

    def latest_valid_owner(self, hill_id, since_ts):
        r = self._query(
            "SELECT team_token, ts_server FROM samples WHERE hill_id=? AND sig_valid=1 "
            "AND team_token IS NOT NULL AND ts_server>=? ORDER BY ts_server DESC LIMIT 1",
            (hill_id, since_ts))
        return r[0]["team_token"] if r else None

    def last_any_sample_ts(self, hill_id):
        r = self._query("SELECT MAX(ts_server) t FROM samples WHERE hill_id=? AND sig_valid=1", (hill_id,))
        return r[0]["t"] if r and r[0]["t"] is not None else 0

    def latest_sla(self, hill_id, since_ts):
        r = self._query("SELECT status FROM sla_checks WHERE hill_id=? AND ts_server>=? "
                        "ORDER BY ts_server DESC LIMIT 1", (hill_id, since_ts))
        return r[0]["status"] if r else None

    def flag_by_hash(self, h):
        r = self._query("SELECT flag_id,hill_id,kind FROM flags WHERE flag_hash=?", (h,))
        return r[0] if r else None

    def first_correct(self, flag_id):
        r = self._query("SELECT team,ts_server FROM flag_submissions WHERE flag_id=? AND correct=1 "
                        "ORDER BY ts_server ASC LIMIT 1", (flag_id,))
        return r[0] if r else None

    def recent_submissions(self, team, since_ts):
        r = self._query("SELECT COUNT(*) c FROM flag_submissions WHERE team=? AND ts_server>=?",
                        (team, since_ts))
        return r[0]["c"]

    def ticks_per_team(self):
        return self._query("SELECT team, COALESCE(SUM(points),0) n FROM ticks GROUP BY team")

    def ticks_per_team_hill(self):
        return self._query("SELECT team, hill_id, COALESCE(SUM(points),0) n FROM ticks GROUP BY team, hill_id")

    def adjustments_per_team(self):
        # SLA penalties + manual admin adjustments: team in details, points in points
        return self._query(
            "SELECT details AS team, COALESCE(SUM(points),0) pts FROM events "
            "WHERE type IN ('SLA_PENALTY','ADJUST') GROUP BY details")

    def all_events(self, limit=200):
        return self._query("SELECT ts_server,hill_id,type,details,points FROM events "
                           "ORDER BY id DESC LIMIT ?", (limit,))
