import sqlite3

conn = sqlite3.connect('finance_planner_saas.db')
cursor = conn.cursor()

cursor.execute('SELECT name, email FROM users WHERE email LIKE "%admin%"')
admins = cursor.fetchall()

print('Admins encontrados:')
for admin in admins:
    print(f'Nome: {admin[0]}, Email: {admin[1]}')

conn.close()
