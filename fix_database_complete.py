#!/usr/bin/env python3
"""
CORREÇÃO CRÍTICA DO BANCO DE DADOS - ETAPA 4
Resolução de todos os erros identificados nos logs
"""

import sqlite3
import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_database():
    """Corrige todos os problemas do banco de dados"""
    
    db_path = 'fynanpro.db'
    backup_path = f'fynanpro_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    # Fazer backup se banco existir
    if os.path.exists(db_path):
        logger.info(f"📦 Fazendo backup: {backup_path}")
        import shutil
        shutil.copy2(db_path, backup_path)
    
    logger.info("🔧 INICIANDO CORREÇÃO COMPLETA DO BANCO DE DADOS")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. CRIAR/VERIFICAR TABELA USERS
        logger.info("👤 Criando/verificando tabela users...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(120) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                plan_type VARCHAR(20) DEFAULT 'free',
                plan_start_date TIMESTAMP,
                plan_end_date TIMESTAMP,
                trial_used BOOLEAN DEFAULT 0,
                stripe_customer_id VARCHAR(100),
                stripe_subscription_id VARCHAR(100),
                payment_method VARCHAR(50),
                last_payment_date TIMESTAMP,
                total_paid DECIMAL(10,2) DEFAULT 0.00
            )
        ''')
        
        # 2. CRIAR/VERIFICAR TABELA ACCOUNTS
        logger.info("🏦 Criando/verificando tabela accounts...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                account_type VARCHAR(50) NOT NULL,
                balance DECIMAL(15,2) DEFAULT 0.00,
                initial_balance DECIMAL(15,2) DEFAULT 0.00,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # 3. CRIAR/VERIFICAR TABELA CATEGORIES
        logger.info("📂 Criando/verificando tabela categories...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                category_type VARCHAR(20) DEFAULT 'expense',
                color VARCHAR(7) DEFAULT '#007bff',
                icon VARCHAR(50) DEFAULT 'fas fa-tag',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # 4. CRIAR/VERIFICAR TABELA TRANSACTIONS (COM TODAS AS COLUNAS)
        logger.info("💳 Criando/verificando tabela transactions...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                category_id INTEGER,
                description TEXT NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                transaction_type VARCHAR(20) NOT NULL,
                category VARCHAR(100),
                transaction_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_recurring BOOLEAN DEFAULT 0,
                recurring_type VARCHAR(20),
                recurring_day INTEGER,
                tags TEXT,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            )
        ''')
        
        # 5. CRIAR TABELA BUDGETS (ETAPA 4)
        logger.info("💼 Criando tabela budgets...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                amount DECIMAL(15,2) NOT NULL,
                spent_amount DECIMAL(15,2) DEFAULT 0.00,
                period_type VARCHAR(20) DEFAULT 'monthly',
                start_date DATE NOT NULL,
                end_date DATE,
                is_active BOOLEAN DEFAULT 1,
                alert_percentage INTEGER DEFAULT 80,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            )
        ''')
        
        # 6. CRIAR TABELA GOALS (ETAPA 4)
        logger.info("🎯 Criando tabela goals...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                target_amount DECIMAL(15,2) NOT NULL,
                current_amount DECIMAL(15,2) DEFAULT 0.00,
                target_date DATE,
                is_achieved BOOLEAN DEFAULT 0,
                priority INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # 7. CRIAR TABELA GOAL_CONTRIBUTIONS (ETAPA 4)
        logger.info("💰 Criando tabela goal_contributions...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                description TEXT,
                contribution_date DATE DEFAULT (date('now')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # 8. ADICIONAR COLUNAS FALTANTES SE NÃO EXISTIREM
        logger.info("🔧 Verificando e adicionando colunas faltantes...")
        
        # Verificar se coluna category existe em transactions
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'category' not in columns:
            logger.info("➕ Adicionando coluna 'category' em transactions...")
            cursor.execute('ALTER TABLE transactions ADD COLUMN category VARCHAR(100)')
        
        if 'transaction_type' not in columns:
            logger.info("➕ Adicionando coluna 'transaction_type' em transactions...")
            cursor.execute('ALTER TABLE transactions ADD COLUMN transaction_type VARCHAR(20) NOT NULL DEFAULT "expense"')
        
        # Verificar coluna category_type em categories
        cursor.execute("PRAGMA table_info(categories)")
        cat_columns = [column[1] for column in cursor.fetchall()]
        
        if 'category_type' not in cat_columns:
            logger.info("➕ Adicionando coluna 'category_type' em categories...")
            cursor.execute('ALTER TABLE categories ADD COLUMN category_type VARCHAR(20) DEFAULT "expense"')
        
        # 9. INSERIR CATEGORIAS PADRÃO
        logger.info("📁 Inserindo categorias padrão...")
        default_categories = [
            ('Alimentação', 'expense', '#ff6b6b', 'fas fa-utensils'),
            ('Transporte', 'expense', '#4ecdc4', 'fas fa-car'),
            ('Moradia', 'expense', '#45b7d1', 'fas fa-home'),
            ('Saúde', 'expense', '#96ceb4', 'fas fa-heartbeat'),
            ('Lazer', 'expense', '#ffeaa7', 'fas fa-gamepad'),
            ('Educação', 'expense', '#dda0dd', 'fas fa-graduation-cap'),
            ('Vestuário', 'expense', '#ff7675', 'fas fa-tshirt'),
            ('Outros Gastos', 'expense', '#636e72', 'fas fa-ellipsis-h'),
            ('Salário', 'income', '#00b894', 'fas fa-money-bill-wave'),
            ('Freelance', 'income', '#00cec9', 'fas fa-laptop'),
            ('Investimentos', 'income', '#6c5ce7', 'fas fa-chart-line'),
            ('Outros Rendimentos', 'income', '#a29bfe', 'fas fa-plus')
        ]
        
        for name, cat_type, color, icon in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (user_id, name, category_type, color, icon)
                VALUES (NULL, ?, ?, ?, ?)
            ''', (name, cat_type, color, icon))
        
        # 10. CRIAR ÍNDICES PARA PERFORMANCE
        logger.info("📊 Criando índices para performance...")
        indices = [
            'CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, transaction_date)',
            'CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)',
            'CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id)',
            'CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_budgets_user ON budgets(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_goals_user ON goals(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_goal_contributions_goal ON goal_contributions(goal_id)'
        ]
        
        for index_sql in indices:
            cursor.execute(index_sql)
        
        # 11. VERIFICAR INTEGRIDADE
        logger.info("🔍 Verificando integridade do banco...")
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        
        if integrity == 'ok':
            logger.info("✅ Integridade do banco: OK")
        else:
            logger.warning(f"⚠️ Problemas de integridade: {integrity}")
        
        # 12. COMMIT E ESTATÍSTICAS FINAIS
        conn.commit()
        
        # Estatísticas das tabelas
        tables = ['users', 'accounts', 'categories', 'transactions', 'budgets', 'goals', 'goal_contributions']
        logger.info("📊 ESTATÍSTICAS FINAIS:")
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"  📋 {table}: {count} registros")
            except sqlite3.Error as e:
                logger.error(f"  ❌ Erro ao contar {table}: {e}")
        
        logger.info("✅ CORREÇÃO DO BANCO DE DADOS CONCLUÍDA COM SUCESSO!")
        return True
        
    except Exception as e:
        logger.error(f"🚨 ERRO DURANTE CORREÇÃO: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = fix_database()
    if success:
        print("\n🎉 BANCO DE DADOS CORRIGIDO E PRONTO PARA USO!")
        print("✅ Todas as tabelas ETAPA 4 criadas")
        print("✅ Colunas faltantes adicionadas")
        print("✅ Categorias padrão inseridas") 
        print("✅ Índices de performance criados")
        print("\n🚀 O sistema agora deve funcionar sem erros!")
    else:
        print("\n❌ FALHA NA CORREÇÃO DO BANCO DE DADOS")
        print("Verifique os logs para mais detalhes.")
