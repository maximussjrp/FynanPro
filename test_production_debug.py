#!/usr/bin/env python3
"""
Teste de Debug para Produção - Diagnóstico de erro 500 no /transactions
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash

def test_production_environment():
    print("🔍 TESTE DE DEBUG - PRODUÇÃO")
    print("=" * 50)
    
    # Verificar se o banco existe
    db_path = 'finance_planner.db'
    if os.path.exists(db_path):
        print(f"✅ Database encontrado: {db_path}")
    else:
        print(f"❌ Database NÃO encontrado: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # 1. Verificar estrutura da tabela users
        print("\n📋 ESTRUTURA DA TABELA USERS:")
        users_info = conn.execute("PRAGMA table_info(users)").fetchall()
        for column in users_info:
            print(f"   - {column['name']}: {column['type']}")
        
        # 2. Verificar estrutura da tabela transactions
        print("\n📋 ESTRUTURA DA TABELA TRANSACTIONS:")
        transactions_info = conn.execute("PRAGMA table_info(transactions)").fetchall()
        for column in transactions_info:
            print(f"   - {column['name']}: {column['type']}")
        
        # 3. Verificar se existe usuário admin
        print("\n👤 VERIFICAR USUÁRIO ADMIN:")
        admin_user = conn.execute("SELECT * FROM users WHERE email = 'admin@fynanpro.com'").fetchone()
        if admin_user:
            print(f"✅ Usuário admin encontrado: ID {admin_user['id']}")
        else:
            print("❌ Usuário admin NÃO encontrado - criando...")
            # Criar usuário admin se não existir
            password_hash = generate_password_hash('admin123')
            conn.execute('''
                INSERT INTO users (name, email, password_hash, created_at)
                VALUES (?, ?, ?, datetime('now'))
            ''', ('Admin', 'admin@fynanpro.com', password_hash))
            conn.commit()
            print("✅ Usuário admin criado!")
        
        # 4. Contar transações
        print("\n💰 VERIFICAR TRANSAÇÕES:")
        transaction_count = conn.execute("SELECT COUNT(*) as count FROM transactions").fetchone()
        print(f"📊 Total de transações: {transaction_count['count']}")
        
        # 5. Verificar accounts
        print("\n🏦 VERIFICAR CONTAS:")
        account_count = conn.execute("SELECT COUNT(*) as count FROM accounts").fetchone()
        print(f"📊 Total de contas: {account_count['count']}")
        
        # 6. Teste da query principal do /transactions
        print("\n🧪 TESTE DA QUERY PRINCIPAL:")
        admin_user = conn.execute("SELECT * FROM users WHERE email = 'admin@fynanpro.com'").fetchone()
        if admin_user:
            user_id = admin_user['id']
            print(f"   Testando com user_id: {user_id}")
            
            # Query simplificada primeiro
            try:
                test_query = '''
                SELECT t.id, t.description, t.amount, t.type, t.date
                FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.id
                WHERE (a.user_id = ? OR t.user_id = ?)
                LIMIT 5
                '''
                results = conn.execute(test_query, (user_id, user_id)).fetchall()
                print(f"✅ Query básica funcionou - {len(results)} resultados")
                
                # Testar query complexa
                complex_query = '''
                SELECT 
                    t.id, t.description, t.amount, t.type, t.date, t.notes,
                    t.category, t.account_id, t.transfer_to_account_id,
                    t.transfer_from_account_id, t.is_transfer, t.recurrence_type,
                    a.name as account_name, a.bank_name,
                    ta.name as transfer_account_name
                FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.id
                LEFT JOIN accounts ta ON (t.transfer_to_account_id = ta.id OR t.transfer_from_account_id = ta.id)
                WHERE (a.user_id = ? OR t.user_id = ?)
                LIMIT 5
                '''
                complex_results = conn.execute(complex_query, (user_id, user_id)).fetchall()
                print(f"✅ Query complexa funcionou - {len(complex_results)} resultados")
                
            except Exception as e:
                print(f"❌ Erro na query: {str(e)}")
        
        conn.close()
        print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {str(e)}")

if __name__ == "__main__":
    test_production_environment()
