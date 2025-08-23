"""
Sistema de Migrações Idempotentes - FynanPro
Arquitetura: Migrations automáticas no startup
Compatibilidade: SQLite + Python 3.13 + Flask
"""

import os
import sqlite3
import logging
from typing import List, Callable

logger = logging.getLogger(__name__)

class MigrationRunner:
    """
    Executa migrações de forma idempotente e segura
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.migrations = []
        
    def register_migration(self, name: str, migration_func: Callable):
        """Registra uma migração para execução"""
        self.migrations.append((name, migration_func))
        
    def run_all(self):
        """Executa todas as migrações registradas"""
        logger.info("🔧 Iniciando sistema de migrações...")
        
        # Criar tabela de controle de migrações se não existir
        self._create_migrations_table()
        
        executed_count = 0
        for name, migration_func in self.migrations:
            try:
                if not self._is_migration_executed(name):
                    logger.info(f"⚡ Executando migração: {name}")
                    
                    # Executar migração em transação
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("BEGIN TRANSACTION;")
                        try:
                            migration_func(conn)
                            self._mark_migration_executed(conn, name)
                            conn.execute("COMMIT;")
                            executed_count += 1
                            logger.info(f"✅ Migração concluída: {name}")
                        except Exception as e:
                            conn.execute("ROLLBACK;")
                            raise e
                else:
                    logger.debug(f"⏭️  Migração já executada: {name}")
                    
            except Exception as e:
                logger.error(f"❌ Erro na migração {name}: {str(e)}")
                raise
                
        if executed_count > 0:
            logger.info(f"🎉 {executed_count} migrações executadas com sucesso!")
        else:
            logger.info("✅ Todas as migrações já estavam aplicadas")
            
    def _create_migrations_table(self):
        """Cria tabela de controle de migrações"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    executed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
    def _is_migration_executed(self, name: str) -> bool:
        """Verifica se uma migração já foi executada"""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE name = ?", 
                (name,)
            ).fetchone()
            return result is not None
            
    def _mark_migration_executed(self, conn: sqlite3.Connection, name: str):
        """Marca uma migração como executada"""
        conn.execute(
            "INSERT INTO schema_migrations (name) VALUES (?)", 
            (name,)
        )

# Utilitários para migrações
def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Verifica se uma coluna existe em uma tabela"""
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    """Verifica se uma tabela existe"""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
        (table,)
    )
    return cursor.fetchone() is not None

def index_exists(conn: sqlite3.Connection, index_name: str) -> bool:
    """Verifica se um índice existe"""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?", 
        (index_name,)
    )
    return cursor.fetchone() is not None

# Importar todas as migrações
from .migration_001_add_accounts_balance import migration_001
from .migration_002_fix_transactions_type_column import migration_002
# from .migration_003_create_categories_and_seed import migration_003  # Temporariamente desabilitado

def run_all_migrations(db_path: str = "finance_planner.db"):
    """
    Executa todas as migrações disponíveis
    
    Args:
        db_path: Caminho para o banco de dados SQLite
    """
    runner = MigrationRunner(db_path)
    
    # Registrar migrações na ordem correta
    runner.register_migration("001_add_accounts_balance", migration_001)
    runner.register_migration("002_fix_transactions_type_column", migration_002)
    # runner.register_migration("003_create_categories_and_seed", migration_003)  # Desabilitado temporariamente
    
    # Executar todas
    runner.run_all()
    
    logger.info("🚀 Sistema de migrações concluído!")
