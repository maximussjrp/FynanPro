#!/usr/bin/env python3
"""
Script de migração automática para adicionar coluna type
Execute: python migrate_add_type_column.py
"""

import sqlite3
import os
from datetime import datetime

def migrate_add_type_column():
    """Adiciona coluna type na tabela transactions"""
    
    # Caminho do banco de dados
    db_path = os.environ.get('DATABASE_URL', 'finance_planner_saas.db')
    if db_path.startswith('sqlite:///'):
        db_path = db_path.replace('sqlite:///', '')
    
    print(f"🔧 Conectando ao banco: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Verificar se a tabela transactions existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='transactions'
        """)
        
        if not cursor.fetchone():
            print("❌ Tabela 'transactions' não existe!")
            return False
        
        # 2. Verificar colunas existentes
        cursor.execute("PRAGMA table_info(transactions)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Colunas existentes: {column_names}")
        
        # 3. Verificar se coluna 'type' já existe
        if 'type' in column_names:
            print("✅ Coluna 'type' já existe!")
            
            # Verificar valores
            cursor.execute("SELECT DISTINCT type FROM transactions WHERE type IS NOT NULL")
            existing_types = cursor.fetchall()
            print(f"🏷️  Tipos existentes: {existing_types}")
            
            return True
        
        # 4. Backup da tabela (segurança)
        backup_table = f"transactions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cursor.execute(f"""
            CREATE TABLE {backup_table} AS 
            SELECT * FROM transactions
        """)
        print(f"💾 Backup criado: {backup_table}")
        
        # 5. Adicionar coluna type
        print("➕ Adicionando coluna 'type'...")
        cursor.execute("ALTER TABLE transactions ADD COLUMN type TEXT")
        
        # 6. Definir valores padrão baseado em lógica de negócio
        cursor.execute("""
            UPDATE transactions 
            SET type = CASE 
                WHEN amount > 0 THEN 'income'
                WHEN amount < 0 THEN 'expense' 
                ELSE 'adjustment'
            END
        """)
        
        # 7. Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE type IS NULL")
        null_count = cursor.fetchone()[0]
        
        if null_count == 0:
            print("✅ Migração concluída com sucesso!")
            
            # Estatísticas finais
            cursor.execute("""
                SELECT type, COUNT(*) 
                FROM transactions 
                GROUP BY type
            """)
            stats = cursor.fetchall()
            print("📊 Estatísticas por tipo:")
            for type_name, count in stats:
                print(f"   {type_name}: {count} registros")
                
        else:
            print(f"⚠️  Ainda existem {null_count} registros com type NULL")
        
        conn.commit()
        print("💾 Mudanças salvas!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando migração para adicionar coluna 'type'")
    success = migrate_add_type_column()
    
    if success:
        print("\n✅ Migração concluída! Você pode reiniciar sua aplicação.")
    else:
        print("\n❌ Migração falhou! Verifique os erros acima.")
