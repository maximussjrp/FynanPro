def migration_001(conn, table_exists, column_exists):
    if not table_exists(conn, "accounts"):
        raise RuntimeError("Tabela 'accounts' não existe; execute 000_create_base_schema antes.")
    if not column_exists(conn, "accounts", "balance"):
        conn.execute("ALTER TABLE accounts ADD COLUMN balance REAL NOT NULL DEFAULT 0;")
