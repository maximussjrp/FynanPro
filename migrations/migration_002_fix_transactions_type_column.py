"""
Migração 002: Padronizar coluna type para transaction_type
Objetivo: Corrigir erro "table transactions has no column named type"
Estratégia: Garantir que transaction_type existe e migrar dados se necessário
"""

import sqlite3
import logging
from . import column_exists, table_exists

logger = logging.getLogger(__name__)

def migration_002(conn: sqlite3.Connection):
    """
    Padroniza coluna de tipo de transação para transaction_type
    Migra dados da coluna type se existir
    """
    logger.info("💱 [002] Padronizando coluna de tipo de transação...")
    
    # Verificar se tabela transactions existe
    if not table_exists(conn, "transactions"):
        logger.warning("⚠️ Tabela transactions não encontrada - será criada pelo sistema")
        return
    
    # Verificar estrutura atual
    columns_info = conn.execute("PRAGMA table_info(transactions)").fetchall()
    existing_columns = [col[1] for col in columns_info]
    
    logger.info(f"🔍 Colunas existentes na tabela transactions: {existing_columns}")
    
    has_type = column_exists(conn, "transactions", "type")
    has_transaction_type = column_exists(conn, "transactions", "transaction_type")
    
    logger.info(f"📋 Status: type={has_type}, transaction_type={has_transaction_type}")
    
    # Cenário 1: Só tem type, precisa criar transaction_type e migrar
    if has_type and not has_transaction_type:
        logger.info("🔧 Criando coluna transaction_type e migrando dados de type...")
        
        conn.execute("""
            ALTER TABLE transactions 
            ADD COLUMN transaction_type TEXT
        """)
        
        # Migrar dados de type para transaction_type
        conn.execute("""
            UPDATE transactions 
            SET transaction_type = type 
            WHERE transaction_type IS NULL
        """)
        
        # Verificar migração
        migrated_count = conn.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE transaction_type IS NOT NULL
        """).fetchone()[0]
        
        logger.info(f"✅ {migrated_count} registros migrados de type para transaction_type")
    
    # Cenário 2: Não tem transaction_type, precisa criar
    elif not has_transaction_type:
        logger.info("🔧 Criando coluna transaction_type...")
        
        conn.execute("""
            ALTER TABLE transactions 
            ADD COLUMN transaction_type TEXT
        """)
        
        # Definir valores padrão baseado em amount (positivo = receita, negativo = despesa)
        conn.execute("""
            UPDATE transactions 
            SET transaction_type = CASE 
                WHEN amount >= 0 THEN 'receita'
                ELSE 'despesa'
            END
            WHERE transaction_type IS NULL
        """)
        
        logger.info("✅ Coluna transaction_type criada com valores padrão")
    
    # Cenário 3: Já tem transaction_type
    else:
        logger.info("✅ Coluna transaction_type já existe")
    
    # Normalizar valores para consistência
    logger.info("🔄 Normalizando valores de transaction_type...")
    
    normalization_updates = [
        # Receitas
        ("UPDATE transactions SET transaction_type = 'receita' WHERE transaction_type IN ('income', 'entrada', 'credit')", "receitas"),
        # Despesas  
        ("UPDATE transactions SET transaction_type = 'despesa' WHERE transaction_type IN ('expense', 'saida', 'debit')", "despesas"),
        # Transferências
        ("UPDATE transactions SET transaction_type = 'transferencia' WHERE transaction_type IN ('transfer')", "transferências")
    ]
    
    total_normalized = 0
    for update_query, type_name in normalization_updates:
        result = conn.execute(update_query)
        count = result.rowcount
        if count > 0:
            logger.info(f"📝 {count} registros normalizados para {type_name}")
            total_normalized += count
    
    if total_normalized > 0:
        logger.info(f"✅ {total_normalized} registros normalizados no total")
    else:
        logger.info("✅ Todos os registros já estavam normalizados")
    
    # Criar índice para performance se não existir
    try:
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_type 
            ON transactions(transaction_type)
        """)
        logger.info("📈 Índice criado para transaction_type")
    except Exception as e:
        logger.warning(f"⚠️ Não foi possível criar índice: {e}")
    
    # Estatísticas finais
    stats = conn.execute("""
        SELECT 
            transaction_type, 
            COUNT(*) as count,
            SUM(amount) as total_amount
        FROM transactions 
        GROUP BY transaction_type
        ORDER BY count DESC
    """).fetchall()
    
    logger.info("📊 Estatísticas finais por tipo:")
    for stat in stats:
        type_name, count, total = stat
        logger.info(f"   {type_name}: {count} transações, R$ {total:.2f}")
    
    logger.info("✅ [002] Padronização de transaction_type concluída!")

def ensure_transaction_type_column(conn: sqlite3.Connection):
    """
    Função utilitária para garantir que transaction_type existe
    Para uso em outras partes do código
    """
    if not column_exists(conn, "transactions", "transaction_type"):
        conn.execute("ALTER TABLE transactions ADD COLUMN transaction_type TEXT")
        # Definir valores padrão se necessário
        conn.execute("""
            UPDATE transactions 
            SET transaction_type = CASE 
                WHEN amount >= 0 THEN 'receita'
                ELSE 'despesa'
            END
            WHERE transaction_type IS NULL
        """)

def get_transaction_type_column_name(conn: sqlite3.Connection) -> str:
    """
    Retorna o nome da coluna de tipo de transação disponível
    Para uso dinâmico no código
    """
    if column_exists(conn, "transactions", "transaction_type"):
        return "transaction_type"
    elif column_exists(conn, "transactions", "type"):
        return "type"
    else:
        return "transaction_type"  # Default - será criado se necessário
