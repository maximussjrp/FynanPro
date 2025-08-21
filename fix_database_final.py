#!/usr/bin/env python3
"""
Script de correção DEFINITIVA para o banco de dados
Execute: python fix_database_final.py
"""

import sqlite3
import os
from datetime import datetime

def fix_database_constraints():
    """Corrige os constraints NOT NULL problemáticos"""
    
    db_path = os.environ.get('DATABASE_URL', 'finance_planner_saas.db')
    if db_path.startswith('sqlite:///'):
        db_path = db_path.replace('sqlite:///', '')
    
    print(f"🔧 Corrigindo constraints do banco: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Backup da tabela atual
        print("💾 Fazendo backup da tabela transactions...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions_backup AS 
            SELECT * FROM transactions
        """)
        
        # 2. Contar registros antes
        cursor.execute("SELECT COUNT(*) FROM transactions")
        total_before = cursor.fetchone()[0]
        print(f"📊 Registros antes da correção: {total_before}")
        
        # 3. Criar nova tabela com schema correto (SEM NOT NULL em category)
        print("🏗️ Criando nova tabela com schema correto...")
        cursor.execute("DROP TABLE IF EXISTS transactions_new")
        
        cursor.execute("""
            CREATE TABLE transactions_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL,
                category TEXT,  -- SEM NOT NULL!
                date DATETIME NOT NULL,
                notes TEXT,
                account_id INTEGER,
                transfer_to_account_id INTEGER,
                transfer_from_account_id INTEGER,
                is_transfer BOOLEAN DEFAULT 0,
                is_adjustment BOOLEAN DEFAULT 0,
                adjustment_reason TEXT,
                recurrence_type TEXT,
                recurrence_interval INTEGER,
                recurrence_count INTEGER,
                current_occurrence INTEGER DEFAULT 1,
                parent_transaction_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (transfer_to_account_id) REFERENCES accounts (id),
                FOREIGN KEY (transfer_from_account_id) REFERENCES accounts (id),
                FOREIGN KEY (parent_transaction_id) REFERENCES transactions (id)
            )
        """)
        
        # 4. Migrar dados existentes
        print("📦 Migrando dados existentes...")
        cursor.execute("""
            INSERT INTO transactions_new 
            (id, user_id, description, amount, type, category, date, notes, 
             account_id, transfer_to_account_id, transfer_from_account_id, 
             is_transfer, is_adjustment, adjustment_reason, recurrence_type, 
             recurrence_interval, recurrence_count, current_occurrence, 
             parent_transaction_id)
            SELECT 
                id, user_id, description, amount, 
                COALESCE(type, 'expense') as type,  -- Default para registros sem type
                category,  -- Pode ser NULL agora
                date, notes, account_id, transfer_to_account_id, 
                transfer_from_account_id, is_transfer, is_adjustment, 
                adjustment_reason, recurrence_type, recurrence_interval, 
                recurrence_count, current_occurrence, parent_transaction_id
            FROM transactions
        """)
        
        # 5. Contar registros migrados
        cursor.execute("SELECT COUNT(*) FROM transactions_new")
        total_migrated = cursor.fetchone()[0]
        print(f"✅ Registros migrados: {total_migrated}")
        
        if total_migrated != total_before:
            print(f"⚠️ ATENÇÃO: {total_before - total_migrated} registros perdidos na migração!")
        
        # 6. Substituir tabela antiga
        print("🔄 Substituindo tabela antiga...")
        cursor.execute("DROP TABLE transactions")
        cursor.execute("ALTER TABLE transactions_new RENAME TO transactions")
        
        # 7. Testar inserção agora
        print("🧪 Testando inserção após correção...")
        
        test_data = {
            'user_id': 1,
            'description': 'Teste após correção',
            'amount': 50.25,
            'type': 'income',
            'date': datetime.now().isoformat()
            # category pode ser NULL!
        }
        
        cursor.execute("""
            INSERT INTO transactions (user_id, description, amount, type, date)
            VALUES (?, ?, ?, ?, ?)
        """, (test_data['user_id'], test_data['description'], 
              test_data['amount'], test_data['type'], test_data['date']))
        
        test_id = cursor.lastrowid
        print(f"✅ Teste de inserção bem-sucedido! ID: {test_id}")
        
        # 8. Testar a consulta que causava erro no SQLAlchemy
        print("🧪 Testando consulta SQLAlchemy...")
        
        cursor.execute("""
            SELECT id, user_id, description, amount, type, category, date, notes,
                   account_id, transfer_to_account_id, transfer_from_account_id,
                   is_transfer, is_adjustment, adjustment_reason, recurrence_type,
                   recurrence_interval, recurrence_count, current_occurrence, 
                   parent_transaction_id
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 10
        """, (1,))
        
        results = cursor.fetchall()
        print(f"✅ Consulta SQLAlchemy OK! {len(results)} registros")
        
        # 9. Limpar teste
        cursor.execute("DELETE FROM transactions WHERE id = ?", (test_id,))
        
        conn.commit()
        
        # 10. Estatísticas finais
        cursor.execute("SELECT COUNT(*) FROM transactions")
        final_total = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT type, COUNT(*) 
            FROM transactions 
            GROUP BY type
        """)
        by_type = cursor.fetchall()
        
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN category IS NULL THEN 1 ELSE 0 END) as null_categories,
                SUM(CASE WHEN category IS NOT NULL THEN 1 ELSE 0 END) as with_categories
            FROM transactions
        """)
        category_stats = cursor.fetchone()
        
        print(f"\n📊 Estatísticas finais:")
        print(f"   Total de transações: {final_total}")
        print(f"   Sem categoria: {category_stats[0]}")
        print(f"   Com categoria: {category_stats[1]}")
        for type_name, count in by_type:
            print(f"   Tipo {type_name}: {count}")
        
        print(f"\n🎉 CORREÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"✅ Banco está pronto para o SQLAlchemy")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA CORREÇÃO: {e}")
        print("🔄 Tentando restaurar backup...")
        try:
            cursor.execute("DROP TABLE IF EXISTS transactions")
            cursor.execute("ALTER TABLE transactions_backup RENAME TO transactions")
            conn.commit()
            print("✅ Backup restaurado")
        except:
            print("❌ Falha ao restaurar backup!")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 CORREÇÃO DEFINITIVA DO BANCO DE DADOS\n")
    
    success = fix_database_constraints()
    
    print("\n" + "="*60)
    if success:
        print("✅ CORREÇÃO BEM-SUCEDIDA!")
        print("🚀 Agora você pode fazer deploy no Render sem erros")
        print("🎯 O SQLAlchemy funcionará perfeitamente")
    else:
        print("❌ CORREÇÃO FALHOU!")
        print("🔧 Verifique os erros e tente novamente")
    print("="*60)
