"""
Script para inicializar o banco de dados do FynanPro
Execute este arquivo para criar o banco de dados e suas tabelas iniciais
"""
import sqlite3
import os
from datetime import datetime

def init_database():
    """Inicializa o banco de dados com as tabelas necessárias"""
    
    # Criar banco de dados
    db_path = 'finance_planner_saas.db'
    print(f"🗄️ Criando banco de dados: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(150) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                is_admin BOOLEAN DEFAULT 0,
                plan_type TEXT DEFAULT 'trial',
                plan_start_date DATETIME,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                payment_method TEXT DEFAULT 'free',
                last_payment_date DATETIME,
                total_paid REAL DEFAULT 0.0
            )
        ''')
        print("✅ Tabela 'users' criada")
        
        # Tabela de contas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                account_type VARCHAR(50) NOT NULL,
                initial_balance REAL DEFAULT 0.0,
                current_balance REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("✅ Tabela 'accounts' criada")
        
        # Tabela de categorias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                category_type VARCHAR(20) NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("✅ Tabela 'categories' criada")
        
        # Tabela de transações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                category_id INTEGER,
                amount REAL NOT NULL,
                description TEXT,
                transaction_date DATE NOT NULL,
                transaction_type VARCHAR(20) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        print("✅ Tabela 'transactions' criada")
        
        # Commit das alterações
        conn.commit()
        print("\n🎉 Banco de dados inicializado com sucesso!")
        print(f"📁 Local: {os.path.abspath(db_path)}")
        
    except Exception as e:
        print(f"❌ Erro ao criar banco de dados: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Inicializando banco de dados do FynanPro...")
    init_database()