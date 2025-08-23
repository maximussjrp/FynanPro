import sqlite3
from werkzeug.security import check_password_hash

conn = sqlite3.connect('finance_planner_saas.db')
cursor = conn.cursor()

user = cursor.execute('SELECT * FROM users WHERE email = ?', ('admin@fynanpro.com',)).fetchone()

if user:
    print(f"✅ Usuário encontrado: ID {user[0]}, Email: {user[1]}")
    print(f"Password hash: {user[2][:50]}...")
    
    # Testar senha
    if check_password_hash(user[2], 'admin123'):
        print("✅ Senha admin123 está correta")
    else:
        print("❌ Senha admin123 está incorreta")
        
else:
    print("❌ Usuário admin@fynanpro.com não encontrado")

conn.close()
