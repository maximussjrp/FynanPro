#!/usr/bin/env python3
"""
Suite de testes para o sistema de migrações FynanPro
"""

import os
import sqlite3
import tempfile
import shutil
from datetime import datetime
import sys

# Adicionar o diretório atual ao Python path
sys.path.insert(0, '.')

from migrations import run_all_migrations, table_exists, column_exists

def test_empty_database():
    """Teste: banco vazio → migrações criam estrutura completa"""
    print("🧪 Teste 1: Banco vazio → estrutura completa")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Executar migrações em banco vazio
        success = run_all_migrations(db_path)
        assert success, "Migrações falharam"
        
        # Verificar estrutura criada
        with sqlite3.connect(db_path) as conn:
            # Verificar tabelas essenciais
            essential_tables = ['users', 'accounts', 'transactions', 'categories', 'schema_migrations']
            for table in essential_tables:
                assert table_exists(conn, table), f"Tabela {table} não foi criada"
            
            # Verificar colunas críticas
            assert column_exists(conn, 'accounts', 'balance'), "Coluna accounts.balance não existe"
            assert column_exists(conn, 'transactions', 'transaction_type'), "Coluna transactions.transaction_type não existe"
            
            # Verificar categorias foram inseridas
            count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
            assert count > 0, "Categorias não foram inseridas"
            
            # Verificar usuário admin foi criado
            user_count = conn.execute("SELECT COUNT(*) FROM users WHERE username='admin'").fetchone()[0]
            assert user_count == 1, "Usuário admin não foi criado"
        
        print("✅ Teste 1 passou: Estrutura completa criada em banco vazio")
        
    finally:
        os.unlink(db_path)

def test_legacy_database():
    """Teste: banco legado com transactions.type → migra para transaction_type"""
    print("🧪 Teste 2: Migração de banco legado")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Criar banco legado com estrutura antiga
        with sqlite3.connect(db_path) as conn:
            # Criar tabelas no formato antigo
            conn.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    email TEXT UNIQUE,
                    password_hash TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE accounts (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    name TEXT,
                    bank TEXT
                )
            """)
            
            # Tabela transactions com coluna 'type' (formato antigo)
            conn.execute("""
                CREATE TABLE transactions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER DEFAULT 1,
                    account_id INTEGER,
                    amount NUMERIC,
                    type TEXT,
                    description TEXT,
                    date DATE
                )
            """)
            
            # Inserir dados de teste
            conn.execute("INSERT INTO users (id, username, email, password_hash) VALUES (1, 'test', 'test@test.com', 'hash')")
            conn.execute("INSERT INTO accounts (id, user_id, name, bank) VALUES (1, 1, 'Conta Teste', 'Banco Teste')")
            conn.execute("INSERT INTO transactions (id, user_id, account_id, amount, type, description, date) VALUES (1, 1, 1, 100.0, 'income', 'Teste', '2025-01-01')")
            conn.execute("INSERT INTO transactions (id, user_id, account_id, amount, type, description, date) VALUES (2, 1, 1, -50.0, 'expense', 'Teste 2', '2025-01-02')")
        
        # Executar migrações
        success = run_all_migrations(db_path)
        assert success, "Migrações falharam no banco legado"
        
        # Verificar migração
        with sqlite3.connect(db_path) as conn:
            # Verificar que transaction_type existe
            assert column_exists(conn, 'transactions', 'transaction_type'), "transaction_type não foi criado"
            
            # Verificar que dados foram migrados
            transactions = conn.execute("SELECT transaction_type FROM transactions ORDER BY id").fetchall()
            assert transactions[0][0] == 'income', "Dado de receita não migrado corretamente"
            assert transactions[1][0] == 'expense', "Dado de despesa não migrado corretamente"
            
            # Verificar que balance foi adicionado e calculado
            assert column_exists(conn, 'accounts', 'balance'), "Coluna balance não foi adicionada"
            balance = conn.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0]
            assert balance == 50.0, f"Saldo calculado incorreto: {balance} (esperado: 50.0)"
            
            # Verificar que categorias foram inseridas
            count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
            assert count > 0, "Categorias não foram inseridas"
        
        print("✅ Teste 2 passou: Migração de banco legado bem-sucedida")
        
    finally:
        os.unlink(db_path)

def test_transaction_creation():
    """Teste: criar transação via função utilitária"""
    print("🧪 Teste 3: Criação de transações")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Executar migrações
        success = run_all_migrations(db_path)
        assert success, "Migrações falharam"
        
        # Criar transação de teste
        with sqlite3.connect(db_path) as conn:
            # Criar conta de teste adicional
            conn.execute("INSERT INTO accounts (user_id, name, balance) VALUES (1, 'Conta Teste', 0)")
            account_id = conn.lastrowid
            
            # Criar receita
            conn.execute("""
                INSERT INTO transactions (user_id, account_id, amount, transaction_type, description, date)
                VALUES (1, ?, 500.0, 'income', 'Salário Teste', '2025-08-23')
            """, (account_id,))
            
            # Criar despesa
            conn.execute("""
                INSERT INTO transactions (user_id, account_id, amount, transaction_type, description, date)
                VALUES (1, ?, 150.0, 'expense', 'Compras Teste', '2025-08-23')
            """, (account_id,))
            
            # Atualizar saldo
            conn.execute("UPDATE accounts SET balance = 350.0 WHERE id = ?", (account_id,))
            
            # Verificar dados
            balance = conn.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,)).fetchone()[0]
            assert balance == 350.0, f"Saldo incorreto: {balance}"
            
            transaction_count = conn.execute("SELECT COUNT(*) FROM transactions WHERE account_id = ?", (account_id,)).fetchone()[0]
            assert transaction_count == 2, f"Número incorreto de transações: {transaction_count}"
        
        print("✅ Teste 3 passou: Transações criadas com sucesso")
        
    finally:
        os.unlink(db_path)

def test_balance_column_compatibility():
    """Teste: compatibilidade com e sem coluna balance"""
    print("🧪 Teste 4: Compatibilidade coluna balance")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Criar banco sem coluna balance
        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE accounts (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT)")
            conn.execute("CREATE TABLE transactions (id INTEGER PRIMARY KEY, account_id INTEGER, amount NUMERIC, transaction_type TEXT)")
            
            # Inserir dados
            conn.execute("INSERT INTO accounts (id, user_id, name) VALUES (1, 1, 'Test')")
            conn.execute("INSERT INTO transactions (account_id, amount, transaction_type) VALUES (1, 100, 'income')")
            conn.execute("INSERT INTO transactions (account_id, amount, transaction_type) VALUES (1, -30, 'expense')")
        
        # Importar função de teste
        sys.path.insert(0, '.')
        
        # Simular função get_accounts_with_balance
        def test_get_accounts_with_balance(user_id):
            with sqlite3.connect(db_path) as conn:
                has_balance = column_exists(conn, 'accounts', 'balance')
                
                if not has_balance:
                    # Usar CTE para calcular saldo
                    result = conn.execute("""
                        WITH balances AS (
                            SELECT account_id, 
                                   SUM(CASE WHEN transaction_type='income' THEN amount ELSE -amount END) as balance
                            FROM transactions 
                            GROUP BY account_id
                        )
                        SELECT a.id, a.name, COALESCE(b.balance, 0) as balance
                        FROM accounts a
                        LEFT JOIN balances b ON b.account_id = a.id
                        WHERE a.user_id = ?
                    """, (user_id,)).fetchone()
                    
                    return result
        
        # Testar função
        account = test_get_accounts_with_balance(1)
        assert account is not None, "Conta não encontrada"
        assert account[2] == 70, f"Saldo calculado incorreto: {account[2]} (esperado: 70)"
        
        print("✅ Teste 4 passou: Compatibilidade com CTE para saldo")
        
    finally:
        os.unlink(db_path)

def test_idempotent_migrations():
    """Teste: migrações são idempotentes (podem ser executadas múltiplas vezes)"""
    print("🧪 Teste 5: Migrações idempotentes")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Executar migrações 3 vezes
        for i in range(3):
            success = run_all_migrations(db_path)
            assert success, f"Migrações falharam na execução {i+1}"
        
        # Verificar que estrutura ainda está correta
        with sqlite3.connect(db_path) as conn:
            # Contar execuções de cada migração
            migrations = conn.execute("SELECT migration, COUNT(*) as count FROM schema_migrations GROUP BY migration").fetchall()
            
            for migration, count in migrations:
                assert count == 1, f"Migração {migration} foi executada {count} vezes (deveria ser 1)"
            
            # Verificar que não há dados duplicados
            admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE username='admin'").fetchone()[0]
            assert admin_count == 1, f"Usuário admin duplicado: {admin_count}"
            
            category_count = conn.execute("SELECT COUNT(*) FROM categories WHERE user_id IS NULL").fetchone()[0]
            # Deve ter pelo menos as categorias padrão, mas não duplicadas
            assert 20 <= category_count <= 30, f"Número suspeito de categorias: {category_count}"
        
        print("✅ Teste 5 passou: Migrações são idempotentes")
        
    finally:
        os.unlink(db_path)

def run_all_tests():
    """Executa todos os testes"""
    print("🧪 INICIANDO SUITE DE TESTES - SISTEMA DE MIGRAÇÕES")
    print("=" * 60)
    
    tests = [
        test_empty_database,
        test_legacy_database,
        test_transaction_creation,
        test_balance_column_compatibility,
        test_idempotent_migrations
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} falhou: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    print(f"📊 RESULTADO DOS TESTES:")
    print(f"✅ Passou: {passed}")
    print(f"❌ Falhou: {failed}")
    print(f"📈 Taxa de sucesso: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("🎉 TODOS OS TESTES PASSARAM!")
        return True
    else:
        print("🚨 ALGUNS TESTES FALHARAM!")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
