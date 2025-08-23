DEFAULTS = [
  ("income",  "Salário"),
  ("income",  "Vendas"),
  ("expense", "Alimentação"),
  ("expense", "Moradia"),
  ("expense", "Transporte"),
  ("expense", "Lazer"),
  ("expense", "Saúde"),
  ("expense", "Educação"),
]

def migration_003(conn, table_exists, column_exists):
    if not table_exists(conn, "categories"):
        # 000 cria; se ainda faltar, cria agora para robustez
        conn.execute('''
        CREATE TABLE IF NOT EXISTS categories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('income','expense')),
            parent_id INTEGER NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );''')
    for t, name in DEFAULTS:
        conn.execute('''
        INSERT INTO categories(user_id, name, type)
        SELECT NULL, ?, ?
        WHERE NOT EXISTS (
          SELECT 1 FROM categories WHERE user_id IS NULL AND name=? AND type=?
        );''', (name, t, name, t))
