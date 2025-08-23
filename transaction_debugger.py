# Sistema Avançado de Detecção e Correção de Problemas de Transação
import sqlite3
import json
from flask import Flask
import requests

class TransactionDebugger:
    def __init__(self, db_path='finance_planner_saas.db'):
        self.db_path = db_path
        self.app_url = 'http://127.0.0.1:5000'
        
    def test_transaction_endpoint(self):
        """Testar endpoint de transação diretamente"""
        print("🧪 TESTANDO ENDPOINT DE TRANSAÇÃO")
        print("=" * 50)
        
        # Dados de teste
        test_data = {
            'description': 'Teste Automático',
            'amount': 50.00,
            'date': '2025-08-23',
            'type': 'despesa',
            'category_id': '1',
            'account_id': '1',
            'notes': 'Teste de debug automático'
        }
        
        try:
            # Primeiro, fazer login
            session = requests.Session()
            
            # Obter página de login
            login_page = session.get(f'{self.app_url}/login')
            print(f"📋 Status login page: {login_page.status_code}")
            
            # Fazer login
            login_data = {
                'email': 'admin@fynanpro.com',
                'password': 'admin123'
            }
            
            login_response = session.post(f'{self.app_url}/login', data=login_data)
            print(f"🔐 Status login: {login_response.status_code}")
            
            if login_response.status_code == 200 and 'dashboard' in login_response.url:
                print("✅ Login realizado com sucesso")
                
                # Testar criação de transação
                transaction_response = session.post(
                    f'{self.app_url}/transactions/new',
                    json=test_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                print(f"💰 Status transação: {transaction_response.status_code}")
                print(f"📄 Response: {transaction_response.text[:200]}...")
                
                if transaction_response.status_code == 200:
                    result = transaction_response.json()
                    if result.get('success'):
                        print("✅ Transação criada com sucesso!")
                    else:
                        print(f"❌ Erro na transação: {result.get('message')}")
                else:
                    print(f"❌ Erro HTTP: {transaction_response.status_code}")
                
            else:
                print("❌ Falha no login")
                
        except Exception as e:
            print(f"🚨 ERRO DURANTE TESTE: {e}")
    
    def analyze_database_structure(self):
        """Análise detalhada da estrutura do banco"""
        print("\n🔍 ANÁLISE DETALHADA DA ESTRUTURA")
        print("=" * 50)
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verificar todas as colunas da tabela transactions
        cursor.execute("PRAGMA table_info(transactions)")
        columns = cursor.fetchall()
        
        print("📊 COLUNAS DA TABELA TRANSACTIONS:")
        for col in columns:
            constraint = "PRIMARY KEY" if col[5] else ("NOT NULL" if col[3] else "NULLABLE")
            print(f"  {col[0]:2d} | {col[1]:<20} | {col[2]:<15} | {constraint}")
        
        # Verificar se há transações de exemplo
        cursor.execute("SELECT * FROM transactions LIMIT 5")
        sample_transactions = cursor.fetchall()
        
        print(f"\n📋 AMOSTRA DE TRANSAÇÕES ({len(sample_transactions)} registros):")
        for trans in sample_transactions:
            print(f"  ID {trans['id']} | {trans['type']} | R$ {trans['amount']} | {trans['description'][:30]}")
        
        # Verificar contas disponíveis
        cursor.execute("SELECT id, name, user_id FROM accounts WHERE is_active = 1")
        accounts = cursor.fetchall()
        
        print(f"\n💳 CONTAS DISPONÍVEIS ({len(accounts)} contas):")
        for acc in accounts:
            print(f"  ID {acc['id']} | {acc['name']} | User: {acc['user_id']}")
        
        # Verificar categorias disponíveis
        cursor.execute("SELECT id, name, type FROM categories WHERE is_active = 1 LIMIT 10")
        categories = cursor.fetchall()
        
        print(f"\n📂 CATEGORIAS DISPONÍVEIS ({len(categories)} primeiras):")
        for cat in categories:
            print(f"  ID {cat['id']} | {cat['name']} | {cat['type']}")
        
        conn.close()
    
    def check_constraints_and_triggers(self):
        """Verificar constraints e triggers que podem causar problemas"""
        print("\n⚙️ VERIFICANDO CONSTRAINTS E TRIGGERS")
        print("=" * 50)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar foreign keys
        cursor.execute("PRAGMA foreign_key_check(transactions)")
        fk_violations = cursor.fetchall()
        
        if fk_violations:
            print("❌ VIOLAÇÕES DE FOREIGN KEY:")
            for violation in fk_violations:
                print(f"  {violation}")
        else:
            print("✅ Nenhuma violação de Foreign Key")
        
        # Verificar triggers
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'")
        triggers = cursor.fetchall()
        
        print(f"\n🔧 TRIGGERS ENCONTRADOS ({len(triggers)}):")
        for trigger in triggers:
            print(f"  - {trigger[0]}")
        
        # Verificar índices
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = cursor.fetchall()
        
        print(f"\n📈 ÍNDICES PERSONALIZADOS ({len(indexes)}):")
        for index in indexes:
            print(f"  - {index[0]}")
        
        conn.close()
    
    def generate_repair_sql(self):
        """Gerar SQL de reparo para problemas comuns"""
        print("\n🔧 GERANDO SQL DE REPARO")
        print("=" * 50)
        
        repair_sqls = [
            # Recriar tabela transactions com estrutura correta
            """
            -- Backup da tabela atual
            CREATE TABLE transactions_backup AS SELECT * FROM transactions;
            
            -- Recriar tabela com estrutura otimizada
            DROP TABLE transactions;
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('receita', 'despesa', 'transferencia')),
                category TEXT,
                date DATETIME NOT NULL,
                notes TEXT,
                account_id INTEGER,
                transfer_to_account_id INTEGER,
                transfer_from_account_id INTEGER,
                is_transfer BOOLEAN DEFAULT 0,
                is_adjustment BOOLEAN DEFAULT 0,
                adjustment_reason TEXT,
                recurrence_type TEXT,
                recurrence_interval INTEGER,
                recurrence_count INTEGER,
                current_occurrence INTEGER DEFAULT 1,
                parent_transaction_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (transfer_to_account_id) REFERENCES accounts (id),
                FOREIGN KEY (transfer_from_account_id) REFERENCES accounts (id),
                FOREIGN KEY (parent_transaction_id) REFERENCES transactions (id)
            );
            
            -- Restaurar dados
            INSERT INTO transactions SELECT * FROM transactions_backup;
            
            -- Remover backup
            DROP TABLE transactions_backup;
            """,
            
            # Índices de performance
            """
            -- Índices de performance
            CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date);
            CREATE INDEX IF NOT EXISTS idx_transactions_account_date ON transactions(account_id, date);
            CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
            CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
            """,
            
            # Triggers para auditoria
            """
            -- Trigger para updated_at
            CREATE TRIGGER IF NOT EXISTS update_transactions_timestamp 
            AFTER UPDATE ON transactions
            BEGIN
                UPDATE transactions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
            """
        ]
        
        print("📝 SQL DE REPARO GERADO:")
        for i, sql in enumerate(repair_sqls, 1):
            print(f"\n--- SCRIPT {i} ---")
            print(sql.strip())
        
        return repair_sqls
    
    def run_complete_diagnosis(self):
        """Executar diagnóstico completo"""
        print("🏥 DIAGNÓSTICO COMPLETO DO SISTEMA DE TRANSAÇÕES")
        print("=" * 80)
        
        self.analyze_database_structure()
        self.check_constraints_and_triggers()
        self.generate_repair_sql()
        self.test_transaction_endpoint()
        
        print("\n✅ DIAGNÓSTICO CONCLUÍDO")
        print("=" * 80)

if __name__ == '__main__':
    debugger = TransactionDebugger()
    debugger.run_complete_diagnosis()
