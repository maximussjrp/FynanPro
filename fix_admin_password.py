import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

conn = sqlite3.connect('finance_planner_saas.db')
cursor = conn.cursor()

# Atualizar senha do admin para admin123
new_password_hash = generate_password_hash('admin123')

cursor.execute(
    'UPDATE users SET password_hash = ? WHERE email = ?',
    (new_password_hash, 'admin@fynanpro.com')
)

conn.commit()

# Verificar se funcionou
user = cursor.execute('SELECT id, email, name, password_hash FROM users WHERE email = ?', ('admin@fynanpro.com',)).fetchone()
if user and check_password_hash(user[3], 'admin123'):  # password_hash está na posição 3
    print("✅ Senha atualizada com sucesso para admin123")
    print(f"User: ID {user[0]}, Email: {user[1]}, Nome: {user[2]}")
else:
    print("❌ Erro ao atualizar senha")
    if user:
        print(f"User encontrado: {user}")
    else:
        print("User não encontrado")

conn.close()
