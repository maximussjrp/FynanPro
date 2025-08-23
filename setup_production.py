#!/usr/bin/env python3
"""
Script de configuração para produção
Executa todas as migrações e verifica o estado do sistema
"""

import os
import sys
import logging
from datetime import datetime

# Setup de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('production_setup.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Função principal de setup"""
    try:
        logger.info("🚀 INICIANDO SETUP DE PRODUÇÃO")
        logger.info(f"⏰ Timestamp: {datetime.now().isoformat()}")
        logger.info(f"🐍 Python: {sys.version}")
        logger.info(f"📂 Diretório: {os.getcwd()}")
        
        # 1. SECRET_KEY
        logger.info("\n1️⃣ CONFIGURANDO SECRET_KEY")
        setup_secret_key()
        
        # 2. Migrações
        logger.info("\n2️⃣ EXECUTANDO MIGRAÇÕES")
        success = run_migrations()
        
        # 3. Verificação final
        logger.info("\n3️⃣ VERIFICAÇÃO FINAL")
        verify_setup()
        
        if success:
            logger.info("✅ SETUP CONCLUÍDO COM SUCESSO!")
            return True
        else:
            logger.error("❌ SETUP FALHOU!")
            return False
            
    except Exception as e:
        logger.error(f"🚨 ERRO NO SETUP: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def setup_secret_key():
    """Configurar SECRET_KEY"""
    try:
        # Verificar se já existe
        secret_key = os.environ.get('SECRET_KEY')
        if secret_key:
            logger.info(f"✅ SECRET_KEY já existe (tamanho: {len(secret_key)})")
            return True
            
        # Gerar nova chave
        import secrets
        new_key = secrets.token_urlsafe(32)
        os.environ['SECRET_KEY'] = new_key
        
        # Salvar em arquivo .env se não existir
        env_file = '.env'
        if not os.path.exists(env_file):
            with open(env_file, 'w') as f:
                f.write(f"SECRET_KEY={new_key}\n")
            logger.info("✅ SECRET_KEY gerada e salva em .env")
        else:
            logger.info("✅ SECRET_KEY gerada (arquivo .env já existe)")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao configurar SECRET_KEY: {e}")
        return False

def run_migrations():
    """Executar todas as migrações"""
    try:
        # Importar sistema de migração
        from migrations import run_all_migrations
        
        logger.info("🔄 Iniciando migrações...")
        success = run_all_migrations()
        
        if success:
            logger.info("✅ Migrações executadas com sucesso!")
        else:
            logger.error("❌ Erro nas migrações!")
            
        return success
        
    except ImportError as e:
        logger.error(f"❌ Erro ao importar sistema de migração: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Erro nas migrações: {e}")
        return False

def verify_setup():
    """Verificar se o setup está correto"""
    try:
        import sqlite3
        
        # Verificar banco de dados
        db_path = 'finance_planner.db'
        if os.path.exists(db_path):
            logger.info(f"✅ Banco de dados existe: {db_path}")
            
            # Verificar estrutura
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar tabelas principais
            tables = ['accounts', 'transactions', 'categories', 'schema_migrations']
            for table in tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if cursor.fetchone():
                    logger.info(f"✅ Tabela '{table}' existe")
                else:
                    logger.warning(f"⚠️  Tabela '{table}' não encontrada")
            
            # Verificar coluna balance em accounts
            cursor.execute("PRAGMA table_info(accounts)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'balance' in columns:
                logger.info("✅ Coluna 'balance' existe na tabela accounts")
            else:
                logger.warning("⚠️  Coluna 'balance' não encontrada na tabela accounts")
            
            # Verificar coluna transaction_type em transactions
            cursor.execute("PRAGMA table_info(transactions)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'transaction_type' in columns:
                logger.info("✅ Coluna 'transaction_type' existe na tabela transactions")
            else:
                logger.warning("⚠️  Coluna 'transaction_type' não encontrada na tabela transactions")
            
            # Verificar migrações executadas
            cursor.execute("SELECT migration FROM schema_migrations ORDER BY migration")
            executed_migrations = [row[0] for row in cursor.fetchall()]
            logger.info(f"✅ Migrações executadas: {executed_migrations}")
            
            conn.close()
            
        else:
            logger.warning(f"⚠️  Banco de dados não encontrado: {db_path}")
        
        # Verificar SECRET_KEY
        secret_key = os.environ.get('SECRET_KEY')
        if secret_key:
            logger.info(f"✅ SECRET_KEY configurada (tamanho: {len(secret_key)})")
        else:
            logger.warning("⚠️  SECRET_KEY não encontrada")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
