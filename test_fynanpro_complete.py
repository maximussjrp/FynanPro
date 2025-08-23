#!/usr/bin/env python3
"""
Testes Automáticos - Sistema FynanPro
Arquitetura: Testes de migração, transações e health checks
Compatibilidade: SQLite + Python 3.13 + Flask
"""

import os
import sys
import sqlite3
import logging
import tempfile
import shutil
from datetime import datetime

# Configurar logging para testes
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TEST - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class FynanProTests:
    """
    Suite de testes para o sistema FynanPro
    """
    
    def __init__(self):
        self.test_db_path = None
        self.temp_dir = None
        self.passed = 0
        self.failed = 0
        
    def setup(self):
        """Setup do ambiente de testes"""
        logger.info("🧪 Configurando ambiente de testes...")
        
        # Criar diretório temporário
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_finance_planner.db")
        
        logger.info(f"📁 Diretório de teste: {self.temp_dir}")
        logger.info(f"🗃️ Banco de teste: {self.test_db_path}")
        
    def teardown(self):
        """Limpeza após os testes"""
        logger.info("🧹 Limpando ambiente de testes...")
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logger.info("✅ Ambiente limpo")
    
    def assert_true(self, condition, message):
        """Assertion customizada"""
        if condition:
            logger.info(f"✅ {message}")
            self.passed += 1
        else:
            logger.error(f"❌ {message}")
            self.failed += 1
            
    def assert_equal(self, expected, actual, message):
        """Assertion de igualdade"""
        if expected == actual:
            logger.info(f"✅ {message}")
            self.passed += 1
        else:
            logger.error(f"❌ {message} - Esperado: {expected}, Atual: {actual}")
            self.failed += 1
    
    def test_migration_system(self):
        """Testa o sistema de migrações"""
        logger.info("🔧 Testando sistema de migrações...")
        
        try:
            # Importar sistema de migrações
            from migrations import run_all_migrations
            
            # Executar migrações no banco de teste
            run_all_migrations(self.test_db_path)
            
            # Verificar se tabelas foram criadas
            conn = sqlite3.connect(self.test_db_path)
            
            # Verificar tabela de controle de migrações
            migrations_table = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_migrations'
            """).fetchone()
            
            self.assert_true(migrations_table is not None, "Tabela schema_migrations criada")
            
            # Verificar se migrações foram registradas
            migrations_count = conn.execute(
                "SELECT COUNT(*) FROM schema_migrations"
            ).fetchone()[0]
            
            self.assert_true(migrations_count >= 3, f"Pelo menos 3 migrações executadas ({migrations_count})")
            
            # Verificar se tabelas essenciais existem
            essential_tables = ['users', 'accounts', 'transactions', 'categories']
            for table in essential_tables:
                table_exists = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table,)).fetchone()
                
                self.assert_true(table_exists is not None, f"Tabela {table} existe")
            
            # Verificar coluna balance na tabela accounts
            try:
                conn.execute("SELECT balance FROM accounts LIMIT 1")
                self.assert_true(True, "Coluna balance existe na tabela accounts")
            except sqlite3.OperationalError:
                self.assert_true(False, "Coluna balance NÃO existe na tabela accounts")
            
            # Verificar coluna transaction_type na tabela transactions
            try:
                conn.execute("SELECT transaction_type FROM transactions LIMIT 1")
                self.assert_true(True, "Coluna transaction_type existe na tabela transactions")
            except sqlite3.OperationalError:
                self.assert_true(False, "Coluna transaction_type NÃO existe na tabela transactions")
            
            # Verificar se categorias foram criadas
            categories_count = conn.execute(
                "SELECT COUNT(*) FROM categories WHERE user_id IS NULL"
            ).fetchone()[0]
            
            self.assert_true(categories_count > 0, f"Categorias padrão criadas ({categories_count})")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erro no teste de migrações: {e}")
            self.failed += 1
    
    def test_migration_idempotency(self):
        """Testa se migrações são idempotentes"""
        logger.info("🔄 Testando idempotência das migrações...")
        
        try:
            from migrations import run_all_migrations
            
            # Executar migrações pela primeira vez
            run_all_migrations(self.test_db_path)
            
            conn = sqlite3.connect(self.test_db_path)
            first_run_count = conn.execute(
                "SELECT COUNT(*) FROM schema_migrations"
            ).fetchone()[0]
            conn.close()
            
            # Executar migrações novamente
            run_all_migrations(self.test_db_path)
            
            conn = sqlite3.connect(self.test_db_path)
            second_run_count = conn.execute(
                "SELECT COUNT(*) FROM schema_migrations"
            ).fetchone()[0]
            conn.close()
            
            self.assert_equal(
                first_run_count, 
                second_run_count, 
                "Migrações são idempotentes (mesmo número de execuções)"
            )
            
        except Exception as e:
            logger.error(f"❌ Erro no teste de idempotência: {e}")
            self.failed += 1
    
    def test_transaction_creation(self):
        """Testa criação de transações"""
        logger.info("💰 Testando criação de transações...")
        
        try:
            from migrations import run_all_migrations
            
            # Preparar banco
            run_all_migrations(self.test_db_path)
            
            conn = sqlite3.connect(self.test_db_path)
            
            # Criar usuário de teste
            user_id = conn.execute("""
                INSERT INTO users (name, email, password_hash, created_at)
                VALUES ('Test User', 'test@example.com', 'hash123', datetime('now'))
            """).lastrowid
            
            # Criar conta de teste
            account_id = conn.execute("""
                INSERT INTO accounts (user_id, name, type, bank, initial_balance, current_balance, is_active, created_at)
                VALUES (?, 'Conta Teste', 'Conta Corrente', 'Banco Teste', 1000.0, 1000.0, 1, datetime('now'))
            """, (user_id,)).lastrowid
            
            # Criar transação de receita
            income_id = conn.execute("""
                INSERT INTO transactions (user_id, description, amount, date, transaction_type, account_id, notes, created_at)
                VALUES (?, 'Salário Teste', 2500.0, '2025-01-01', 'receita', ?, 'Teste', datetime('now'))
            """, (user_id, account_id)).lastrowid
            
            # Criar transação de despesa
            expense_id = conn.execute("""
                INSERT INTO transactions (user_id, description, amount, date, transaction_type, account_id, notes, created_at)
                VALUES (?, 'Supermercado Teste', -150.0, '2025-01-02', 'despesa', ?, 'Teste', datetime('now'))
            """, (user_id, account_id)).lastrowid
            
            self.assert_true(income_id > 0, "Transação de receita criada")
            self.assert_true(expense_id > 0, "Transação de despesa criada")
            
            # Verificar dados das transações
            transactions = conn.execute("""
                SELECT id, description, amount, transaction_type
                FROM transactions
                WHERE user_id = ?
                ORDER BY id
            """, (user_id,)).fetchall()
            
            self.assert_equal(len(transactions), 2, "2 transações criadas")
            
            if len(transactions) >= 2:
                income_tx, expense_tx = transactions[0], transactions[1]
                
                self.assert_equal(income_tx[2], 2500.0, "Valor da receita correto")
                self.assert_equal(income_tx[3], 'receita', "Tipo da receita correto")
                
                self.assert_equal(expense_tx[2], -150.0, "Valor da despesa correto")
                self.assert_equal(expense_tx[3], 'despesa', "Tipo da despesa correto")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erro no teste de transações: {e}")
            self.failed += 1
    
    def test_account_balance_calculation(self):
        """Testa cálculo de saldo de contas"""
        logger.info("💳 Testando cálculo de saldo de contas...")
        
        try:
            from migrations import run_all_migrations
            from migrations.migration_001_add_accounts_balance import get_account_balance_dynamic
            
            # Preparar banco
            run_all_migrations(self.test_db_path)
            
            conn = sqlite3.connect(self.test_db_path)
            
            # Criar usuário e conta
            user_id = conn.execute("""
                INSERT INTO users (name, email, password_hash, created_at)
                VALUES ('Balance Test', 'balance@test.com', 'hash123', datetime('now'))
            """).lastrowid
            
            account_id = conn.execute("""
                INSERT INTO accounts (user_id, name, type, initial_balance, current_balance, balance, is_active, created_at)
                VALUES (?, 'Conta Saldo', 'Poupança', 0.0, 0.0, 0.0, 1, datetime('now'))
            """, (user_id,)).lastrowid
            
            # Criar transações
            transactions = [
                (1000.0, 'receita', 'Depósito inicial'),
                (-200.0, 'despesa', 'Saque'),
                (500.0, 'receita', 'Depósito adicional'),
                (-100.0, 'despesa', 'Taxa'),
            ]
            
            for amount, tx_type, description in transactions:
                conn.execute("""
                    INSERT INTO transactions (user_id, description, amount, date, transaction_type, account_id, created_at)
                    VALUES (?, ?, ?, '2025-01-01', ?, ?, datetime('now'))
                """, (user_id, description, amount, tx_type, account_id))
            
            # Calcular saldo esperado: 1000 - 200 + 500 - 100 = 1200
            expected_balance = 1200.0
            
            # Testar função de cálculo dinâmico
            calculated_balance = get_account_balance_dynamic(conn, account_id)
            
            self.assert_equal(
                calculated_balance, 
                expected_balance, 
                f"Saldo calculado dinamicamente correto: R$ {calculated_balance:.2f}"
            )
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erro no teste de saldo: {e}")
            self.failed += 1
    
    def test_categories_seed(self):
        """Testa seed de categorias"""
        logger.info("🏷️ Testando seed de categorias...")
        
        try:
            from migrations import run_all_migrations
            from migrations.migration_003_create_categories_and_seed import get_categories_for_user
            
            # Preparar banco
            run_all_migrations(self.test_db_path)
            
            conn = sqlite3.connect(self.test_db_path)
            
            # Buscar categorias globais
            categories = get_categories_for_user(conn)
            
            self.assert_true(len(categories) > 0, f"Categorias carregadas ({len(categories)})")
            
            # Verificar se existem categorias de receita e despesa
            receita_categories = [cat for cat in categories if cat[2] == 'receita']
            despesa_categories = [cat for cat in categories if cat[2] == 'despesa']
            
            self.assert_true(len(receita_categories) > 0, f"Categorias de receita ({len(receita_categories)})")
            self.assert_true(len(despesa_categories) > 0, f"Categorias de despesa ({len(despesa_categories)})")
            
            # Verificar se categorias essenciais existem
            essential_categories = ['Salário', 'Alimentação', 'Moradia', 'Transporte']
            
            category_names = [cat[1] for cat in categories]
            for essential in essential_categories:
                self.assert_true(essential in category_names, f"Categoria '{essential}' existe")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erro no teste de categorias: {e}")
            self.failed += 1
    
    def run_all_tests(self):
        """Executa todos os testes"""
        logger.info("🧪 ===== INICIANDO TESTES FYNANPRO =====")
        
        self.setup()
        
        try:
            # Executar testes
            self.test_migration_system()
            self.test_migration_idempotency()
            self.test_transaction_creation()
            self.test_account_balance_calculation()
            self.test_categories_seed()
            
        finally:
            self.teardown()
        
        # Resultado final
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        logger.info("🧪 ===== RESULTADO DOS TESTES =====")
        logger.info(f"✅ Passou: {self.passed}")
        logger.info(f"❌ Falhou: {self.failed}")
        logger.info(f"📊 Total: {total}")
        logger.info(f"🎯 Taxa de sucesso: {success_rate:.1f}%")
        
        if self.failed == 0:
            logger.info("🎉 TODOS OS TESTES PASSARAM!")
            return True
        else:
            logger.error("💥 ALGUNS TESTES FALHARAM!")
            return False

def main():
    """Função principal"""
    tester = FynanProTests()
    success = tester.run_all_tests()
    
    # Exit code baseado no resultado
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
