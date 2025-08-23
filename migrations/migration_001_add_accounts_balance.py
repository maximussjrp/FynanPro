"""
Migração 001: Adicionar coluna balance na tabela accounts
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

def migration_001(conn: sqlite3.Connection):
    """
    Migração 001: Adicionar coluna balance na tabela accounts e calcular saldos iniciais
    """
    logger.info("🚀 [001] Iniciando migração - Adicionando coluna balance...")
    
    try:
        # 1. Verificar se a coluna balance já existe
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(accounts)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'balance' in columns:
            logger.info("✅ [001] Coluna 'balance' já existe na tabela accounts")
            return
            
        # 2. Adicionar coluna balance
        logger.info("🔧 [001] Adicionando coluna 'balance' na tabela accounts...")
        conn.execute("ALTER TABLE accounts ADD COLUMN balance DECIMAL(10,2) DEFAULT 0.00")
        
        # 3. Verificar se existe tabela de transações
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
        if not cursor.fetchone():
            logger.info("⚠️ [001] Tabela transactions não existe ainda, definindo saldos como 0.00")
            conn.commit()
            return
        
        # 4. Calcular saldo inicial para cada conta baseado nas transações
        logger.info("💰 [001] Calculando saldos iniciais baseados nas transações...")
        
        # Buscar todas as contas
        accounts = conn.execute("SELECT id FROM accounts").fetchall()
        
        for account_row in accounts:
            account_id = account_row[0]
            
            # Calcular saldo baseado nas transações com fallback para diferentes esquemas
            calculated_balance = calculate_account_balance(conn, account_id)
            
            # Atualizar saldo da conta
            conn.execute(
                "UPDATE accounts SET balance = ? WHERE id = ?", 
                (calculated_balance, account_id)
            )
            
            logger.debug(f"💰 [001] Conta ID {account_id}: saldo calculado = R$ {calculated_balance:.2f}")
        
        conn.commit()
        logger.info("✅ [001] Coluna balance adicionada e saldos calculados com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ [001] Erro na migração: {e}")
        conn.rollback()
        raise

def calculate_account_balance(conn: sqlite3.Connection, account_id: int) -> float:
    """
    Calcula o saldo de uma conta considerando diferentes esquemas de colunas
    """
    try:
        # Tentar usar transaction_type primeiro
        balance_query = """
        SELECT 
            COALESCE(SUM(
                CASE 
                    WHEN transaction_type IN ('income', 'receita', 'entrada') THEN amount
                    WHEN transaction_type IN ('expense', 'despesa', 'saida') THEN -amount
                    WHEN transaction_type = 'transfer_in' THEN amount
                    WHEN transaction_type = 'transfer_out' THEN -amount
                    ELSE 0
                END
            ), 0) as calculated_balance
        FROM transactions 
        WHERE account_id = ?
        """
        
        result = conn.execute(balance_query, (account_id,)).fetchone()
        return result[0] if result else 0.0
        
    except sqlite3.OperationalError as e:
        if "no such column: transaction_type" in str(e):
            logger.debug(f"⚠️ [001] Coluna transaction_type não existe, usando 'type' para conta {account_id}")
            
            # Fallback para coluna 'type'
            balance_query = """
            SELECT 
                COALESCE(SUM(
                    CASE 
                        WHEN type IN ('income', 'receita', 'entrada') THEN amount
                        WHEN type IN ('expense', 'despesa', 'saida') THEN -amount
                        WHEN type = 'transfer_in' THEN amount
                        WHEN type = 'transfer_out' THEN -amount
                        ELSE 0
                    END
                ), 0) as calculated_balance
            FROM transactions 
            WHERE account_id = ?
            """
            
            result = conn.execute(balance_query, (account_id,)).fetchone()
            return result[0] if result else 0.0
        else:
            raise e

def get_account_balance_dynamic(conn: sqlite3.Connection, account_id: int) -> float:
    """
    Função utilitária para calcular saldo dinamicamente quando balance não existe
    """
    return calculate_account_balance(conn, account_id)
