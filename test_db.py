#!/usr/bin/env python3
"""
Script para testar a estrutura do banco de dados
"""
import sqlite3
import os
from datetime import datetime, date

def test_database():
    """Testa se o banco de dados e suas tabelas estão corretos"""
    
    db_path = 'finance_planner_saas.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar estrutura da tabela transactions
        print("🔍 Verificando estrutura da tabela 'transactions'...")
        cursor.execute("PRAGMA table_info(transactions)")
        columns = cursor.fetchall()
        
        expected_columns = {
            'id': 'INTEGER',
            'user_id': 'INTEGER', 
            'account_id': 'INTEGER',
            'category_id': 'INTEGER',
            'amount': 'REAL',
            'description': 'TEXT',
            'transaction_date': 'DATE',
            'transaction_type': 'VARCHAR(20)',
            'created_at': 'DATETIME'
        }
        
        print("📋 Colunas encontradas:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
        # Verificar se existem transações
        cursor.execute("SELECT COUNT(*) FROM transactions")
        count = cursor.fetchone()[0]
        print(f"📊 Total de transações: {count}")
        
        # Verificar estrutura das outras tabelas
        tables = ['users', 'accounts', 'categories']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"📊 Total de registros em '{table}': {count}")
        
        print("\n✅ Teste do banco de dados concluído!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar banco de dados: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    test_database()
