import sqlite3

# Conectar ao banco
conn = sqlite3.connect('finance_planner_saas.db')
cursor = conn.cursor()

# Verificar estrutura da tabela categories
print("Estrutura da tabela categories:")
result = cursor.execute('PRAGMA table_info(categories)').fetchall()
for row in result:
    print(f"  {row[1]} ({row[2]}) - {row}")

# Verificar se coluna icon existe
columns = [row[1] for row in result]
if 'icon' not in columns:
    print("\nAdicionando coluna 'icon' à tabela categories...")
    cursor.execute('ALTER TABLE categories ADD COLUMN icon TEXT')
    conn.commit()
    print("✅ Coluna 'icon' adicionada!")
else:
    print("\n✅ Coluna 'icon' já existe!")

# Fechar conexão
conn.close()
print("Verificação concluída.")
