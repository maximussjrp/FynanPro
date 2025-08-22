import sqlite3

conn = sqlite3.connect('fynanpro.db')
cursor = conn.cursor()

print("Verificando colunas da tabela transactions...")
cursor.execute("PRAGMA table_info(transactions)")
columns = [column[1] for column in cursor.fetchall()]
print("Colunas existentes:", columns)

if 'category' not in columns:
    print("Adicionando coluna category...")
    cursor.execute("ALTER TABLE transactions ADD COLUMN category VARCHAR(100)")

if 'transaction_type' not in columns:
    print("Adicionando coluna transaction_type...")
    cursor.execute("ALTER TABLE transactions ADD COLUMN transaction_type VARCHAR(20) DEFAULT 'expense'")

conn.commit()
conn.close()
print("Colunas adicionadas com sucesso!")
