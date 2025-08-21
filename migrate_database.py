"""
Script de migração para corrigir o banco de dados em produção
Adiciona colunas faltantes na tabela transactions
"""
import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Migração para adicionar colunas faltantes"""
    try:
        # Caminho do banco em produção
        db_path = os.environ.get('DATABASE_URL', 'finance_planner_saas.db')
        if db_path.startswith('sqlite:///'):
            db_path = db_path.replace('sqlite:///', '')
        
        logger.info(f"Migrando banco de dados: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar estrutura atual da tabela transactions
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"Colunas atuais da tabela transactions: {columns}")
        
        # Adicionar colunas faltantes se não existirem
        if 'type' not in columns:
            logger.info("Adicionando coluna 'type'")
            cursor.execute("ALTER TABLE transactions ADD COLUMN type TEXT DEFAULT 'expense'")
        
        if 'category' not in columns:
            logger.info("Adicionando coluna 'category'")
            cursor.execute("ALTER TABLE transactions ADD COLUMN category TEXT")
        
        if 'notes' not in columns:
            logger.info("Adicionando coluna 'notes'")
            cursor.execute("ALTER TABLE transactions ADD COLUMN notes TEXT")
        
        if 'account_id' not in columns:
            logger.info("Adicionando coluna 'account_id'")
            cursor.execute("ALTER TABLE transactions ADD COLUMN account_id INTEGER")
        
        if 'transfer_to_account_id' not in columns:
            logger.info("Adicionando coluna 'transfer_to_account_id'")
            cursor.execute("ALTER TABLE transactions ADD COLUMN transfer_to_account_id INTEGER")
        
        if 'transfer_from_account_id' not in columns:
            logger.info("Adicionando coluna 'transfer_from_account_id'")
            cursor.execute("ALTER TABLE transactions ADD COLUMN transfer_from_account_id INTEGER")
        
        if 'is_transfer' not in columns:
            logger.info("Adicionando coluna 'is_transfer'")
            cursor.execute("ALTER TABLE transactions ADD COLUMN is_transfer BOOLEAN DEFAULT 0")
        
        if 'is_adjustment' not in columns:
            logger.info("Adicionando coluna 'is_adjustment'")
            cursor.execute("ALTER TABLE transactions ADD COLUMN is_adjustment BOOLEAN DEFAULT 0")
        
        if 'adjustment_reason' not in columns:
            logger.info("Adicionando coluna 'adjustment_reason'")
            cursor.execute("ALTER TABLE transactions ADD COLUMN adjustment_reason TEXT")
        
        if 'recurrence_type' not in columns:
            logger.info("Adicionando coluna 'recurrence_type'")
            cursor.execute("ALTER TABLE transactions ADD COLUMN recurrence_type TEXT")
        
        if 'recurrence_interval' not in columns:
            logger.info("Adicionando coluna 'recurrence_interval'")
            cursor.execute("ALTER TABLE transactions ADD COLUMN recurrence_interval INTEGER")
        
        if 'recurrence_count' not in columns:
            logger.info("Adicionando coluna 'recurrence_count'")
            cursor.execute("ALTER TABLE transactions ADD COLUMN recurrence_count INTEGER")
        
        if 'current_occurrence' not in columns:
            logger.info("Adicionando coluna 'current_occurrence'")
            cursor.execute("ALTER TABLE transactions ADD COLUMN current_occurrence INTEGER")
        
        if 'parent_transaction_id' not in columns:
            logger.info("Adicionando coluna 'parent_transaction_id'")
            cursor.execute("ALTER TABLE transactions ADD COLUMN parent_transaction_id INTEGER")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Migração concluída com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na migração: {e}")
        return False

if __name__ == '__main__':
    migrate_database()
