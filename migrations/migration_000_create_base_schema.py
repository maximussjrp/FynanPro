def migration_000(conn, table_exists, column_exists):
    # users
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );""")

    # accounts (sem balance inicialmente — virá na 001)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS accounts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        bank_name TEXT,
        account_type TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id);")

    # transactions – já com 'transaction_type' conforme seu código atual
    conn.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT,
        amount REAL NOT NULL,
        date DATE NOT NULL,
        transaction_type TEXT,            -- 'income' | 'expense'
        chart_account_id INTEGER,
        account_id INTEGER,
        notes TEXT,
        reference TEXT,
        tags TEXT,
        recurrence_type TEXT,
        recurrence_end_date DATE,
        parent_transaction_id INTEGER,
        transfer_account_id INTEGER,
        is_confirmed INTEGER DEFAULT 0,
        is_reconciled INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE SET NULL
    );""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_account ON transactions(account_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_type ON transactions(transaction_type);")

    # categories (usada pelos seeds)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS categories(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL CHECK (type IN ('income','expense')),
        parent_id INTEGER NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );""")
