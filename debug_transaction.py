#!/usr/bin/env python3
"""
Script de debug para testar inserção de transações
"""
import sqlite3
import os
from datetime import datetime

def test_transaction_insert():
    db_path = 'finance_planner_saas.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Banco {db_path} não existe")
        return
    
    print(f"✅ Banco {db_path} encontrado")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        # Verificar estrutura da tabela
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(transactions)")
        columns = cursor.fetchall()
        
        print("🔍 Estrutura da tabela transactions:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
        
        # Testar INSERT
        print("\n🧪 Testando INSERT...")
        
        data = {
            'user_id': 1,
            'description': 'Transação de Teste Python',
            'amount': 150.50,
            'date': '2025-08-23',
            'type': 'receita',
            'category': '5',
            'account_id': 1,
            'notes': 'Teste Python debug'
        }
        
        sql = '''
            INSERT INTO transactions (user_id, description, amount, date, type, category, account_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        print(f"SQL: {sql}")
        print(f"Data: {data}")
        
        cursor.execute(sql, (
            data['user_id'], data['description'], data['amount'], data['date'],
            data['type'], data['category'], data['account_id'], data['notes']
        ))
        
        transaction_id = cursor.lastrowid
        conn.commit()
        
        print(f"✅ Transação criada com ID: {transaction_id}")
        
        # Verificar se foi inserida
        result = cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,)).fetchone()
        if result:
            print("✅ Transação confirmada no banco:")
            print(f"  - ID: {result['id']}")
            print(f"  - Descrição: {result['description']}")
            print(f"  - Valor: {result['amount']}")
            print(f"  - Tipo: {result['type']}")
        else:
            print("❌ Transação não encontrada após inserção")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    test_transaction_insert()
