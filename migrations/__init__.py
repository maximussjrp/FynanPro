import sqlite3, logging, os

DB_PATH = os.getenv("DB_PATH", "finance_planner_saas.db")

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def table_exists(conn, table):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?;", (table,)
    ).fetchone() is not None

def column_exists(conn, table, column):
    return any(r[1] == column for r in conn.execute(f"PRAGMA table_info({table});"))

def ensure_schema_migrations(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS schema_migrations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

def applied_set(conn):
    rows = conn.execute("SELECT name FROM schema_migrations;").fetchall()
    return {r[0] for r in rows}

def mark_applied(conn, name):
    conn.execute("INSERT OR IGNORE INTO schema_migrations(name) VALUES (?);", (name,))

# ---- import das migrações reais ----
from .migration_000_create_base_schema import migration_000
from .migration_001_add_accounts_balance import migration_001
from .migration_002_fix_transactions_type_column import migration_002
from .migration_003_seed_categories import migration_003

MIGRATIONS = [
    ("000_create_base_schema", migration_000),
    ("001_add_accounts_balance", migration_001),
    ("002_fix_transactions_type_column", migration_002),
    ("003_seed_categories", migration_003),
]

def run_all_migrations(db_path=None):
    global DB_PATH
    if db_path:
        DB_PATH = db_path

    logging.getLogger("migrations").info(" Iniciando sistema de migrações...")
    conn = _get_conn()
    try:
        ensure_schema_migrations(conn)
        done = applied_set(conn)
        for name, fn in MIGRATIONS:
            if name in done:
                logging.getLogger("migrations").info(f" Migração já aplicada: {name}")
                continue
            logging.getLogger("migrations").info(f" Executando migração: {name}")
            try:
                fn(conn, table_exists=table_exists, column_exists=column_exists)
                mark_applied(conn, name)
                conn.commit()
            except Exception as e:
                logging.getLogger("migrations").error(f" Erro na migração {name}: {e}")
                conn.rollback()
                return False
        return True
    finally:
        conn.close()
