import sqlite3

# Verificar estrutura da tabela transactions
conn = sqlite3.connect('finance_planner_saas.db')
cursor = conn.cursor()

print("🔍 ESTRUTURA DA TABELA TRANSACTIONS:")
print("=" * 50)

# Obter informações da tabela
cursor.execute("PRAGMA table_info(transactions)")
columns = cursor.fetchall()

print("Colunas:")
for col in columns:
    print(f"  {col[0]}: {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")

# Verificar uma transação existente
print("\n📄 EXEMPLO DE TRANSAÇÃO:")
cursor.execute("SELECT * FROM transactions LIMIT 1")
sample = cursor.fetchone()

if sample:
    print("Dados de exemplo:")
    for i, value in enumerate(sample):
        if i < len(columns):
            print(f"  {columns[i][1]}: {value}")

conn.close()
