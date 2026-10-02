"""MySQL data-access layer. Contains NO sample data."""
import ssl

import certifi
import pymysql
import pymysql.cursors

import config

FIELDS = ("title", "description", "research_area", "faculty_name",
          "department", "required_skills", "positions", "deadline", "status")

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS opportunities (
    id               INT UNSIGNED  NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title            VARCHAR(200)  NOT NULL,
    description      TEXT          NOT NULL,
    research_area    VARCHAR(100)  NOT NULL,
    faculty_name     VARCHAR(100)  NOT NULL,
    department       VARCHAR(100)  NOT NULL,
    required_skills  VARCHAR(500)  NOT NULL,
    positions        INT UNSIGNED  NOT NULL,
    deadline         DATE          NOT NULL,
    status           ENUM('Open','Closed') NOT NULL DEFAULT 'Open',
    created_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_deadline (deadline)
) ENGINE=InnoDB
"""


_table_ready = False  # per serverless instance: create the table only once


def _ssl_context():
    if not config.DB_SSL:
        return None
    return ssl.create_default_context(cafile=config.DB_SSL_CA or certifi.where())


def _connect(with_db=True):
    return pymysql.connect(
        host=config.DB_HOST, port=config.DB_PORT,
        user=config.DB_USER, password=config.DB_PASSWORD,
        database=config.DB_NAME if with_db else None,
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor, autocommit=True,
        ssl=_ssl_context(), connect_timeout=10,
    )


def init_db():
    """Create the database and table if they don't exist yet. Inserts no rows."""
    conn = _connect(with_db=False)
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}` "
                        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    finally:
        conn.close()
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE)
    finally:
        conn.close()


def ensure_table():
    """Create the table if missing (the database itself must already exist).
    Safe for cloud hosts where the user cannot CREATE DATABASE."""
    global _table_ready
    if _table_ready:
        return
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE)
    finally:
        conn.close()
    _table_ready = True


def _clean(row):
    """Convert date/datetime values to strings so they are JSON serialisable."""
    if row is None:
        return None
    row["deadline"] = row["deadline"].isoformat()
    row["created_at"] = row["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    row["updated_at"] = row["updated_at"].strftime("%Y-%m-%d %H:%M:%S")
    return row


def _run(sql, args=(), fetch=None):
    ensure_table()
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            if fetch == "all":
                return cur.fetchall()
            if fetch == "one":
                return cur.fetchone()
            return cur.lastrowid if sql.lstrip().upper().startswith("INSERT") else cur.rowcount
    finally:
        conn.close()


def get_all():
    rows = _run("SELECT * FROM opportunities ORDER BY id DESC", fetch="all")
    return [_clean(r) for r in rows]


def get_one(oid):
    return _clean(_run("SELECT * FROM opportunities WHERE id=%s", (oid,), fetch="one"))


def create(data):
    cols = ", ".join(FIELDS)
    marks = ", ".join(["%s"] * len(FIELDS))
    return _run(f"INSERT INTO opportunities ({cols}) VALUES ({marks})",
                tuple(data[f] for f in FIELDS))


def update(oid, data):
    sets = ", ".join(f"{f}=%s" for f in FIELDS)
    _run(f"UPDATE opportunities SET {sets} WHERE id=%s",
         tuple(data[f] for f in FIELDS) + (oid,))


def delete(oid):
    return _run("DELETE FROM opportunities WHERE id=%s", (oid,)) > 0
