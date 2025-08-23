def migration_002(conn, table_exists, column_exists):
    if not table_exists(conn, "transactions"):
        raise RuntimeError("Tabela 'transactions' não existe; execute 000_create_base_schema antes.")

    # Garante a coluna correta
    if not column_exists(conn, "transactions", "transaction_type"):
        conn.execute("ALTER TABLE transactions ADD COLUMN transaction_type TEXT;")

    # Se existir coluna antiga 'type', migre os dados para transaction_type (sem dropar 'type')
    cols = [r[1] for r in conn.execute("PRAGMA table_info(transactions);").fetchall()]
    if "type" in cols:
        conn.execute("UPDATE transactions SET transaction_type = COALESCE(transaction_type, type);")
