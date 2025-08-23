# Sistema Avançado de Teste de Transação Automático
import requests
import json
import sqlite3
from datetime import datetime
import time

class TransactionTester:
    def __init__(self):
        self.base_url = 'http://127.0.0.1:5000'
        self.session = requests.Session()
        self.db_path = 'finance_planner_saas.db'
        
    def check_database_before_test(self):
        """Verificar estado do banco antes do teste"""
        print("🔍 ESTADO DO BANCO ANTES DO TESTE")
        print("=" * 50)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar transações existentes
        cursor.execute("SELECT COUNT(*) FROM transactions")
        transaction_count = cursor.fetchone()[0]
        print(f"📊 Transações no banco: {transaction_count}")
        
        # Verificar últimas transações
        cursor.execute("SELECT id, description, amount, type, date FROM transactions ORDER BY id DESC LIMIT 5")
        recent = cursor.fetchall()
        print("🕒 Últimas transações:")
        for trans in recent:
            print(f"  ID {trans[0]} | {trans[1]} | R$ {trans[2]} | {trans[3]} | {trans[4]}")
        
        # Verificar contas
        cursor.execute("SELECT id, name, current_balance FROM accounts WHERE is_active = 1")
        accounts = cursor.fetchall()
        print(f"\n💳 Contas ativas ({len(accounts)}):")
        for acc in accounts:
            print(f"  ID {acc[0]} | {acc[1]} | R$ {acc[2]}")
        
        # Verificar categorias
        cursor.execute("SELECT id, name, type FROM categories WHERE is_active = 1 LIMIT 5")
        categories = cursor.fetchall()
        print(f"\n📂 Categorias ativas ({len(categories)} primeiras):")
        for cat in categories:
            print(f"  ID {cat[0]} | {cat[1]} | {cat[2]}")
        
        conn.close()
        return transaction_count, len(accounts), len(categories)
    
    def perform_login(self):
        """Realizar login no sistema"""
        print("\n🔐 REALIZANDO LOGIN")
        print("=" * 50)
        
        try:
            # Obter página de login
            login_page = self.session.get(f'{self.base_url}/login')
            print(f"📋 Status da página de login: {login_page.status_code}")
            
            if login_page.status_code != 200:
                print(f"❌ Erro ao carregar página de login: {login_page.status_code}")
                return False
            
            # Fazer login
            login_data = {
                'email': 'admin@fynanpro.com',
                'password': 'admin123'
            }
            
            login_response = self.session.post(f'{self.base_url}/login', data=login_data)
            print(f"🔑 Status do login: {login_response.status_code}")
            print(f"🔗 URL final: {login_response.url}")
            
            # Verificar se redirecionou para dashboard
            if 'dashboard' in login_response.url:
                print("✅ Login realizado com sucesso!")
                return True
            else:
                print(f"❌ Login falhou. Conteúdo da resposta: {login_response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"🚨 ERRO DURANTE LOGIN: {e}")
            return False
    
    def test_account_creation(self):
        """Testar criação de conta"""
        print("\n💳 TESTANDO CRIAÇÃO DE CONTA")
        print("=" * 50)
        
        account_data = {
            'name': f'Conta Teste {datetime.now().strftime("%H%M%S")}',
            'type': 'conta_corrente',
            'bank': 'Banco Teste',
            'initial_balance': 1000.00,
            'color': '#FF5733'
        }
        
        try:
            response = self.session.post(
                f'{self.base_url}/accounts/create',
                json=account_data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"📤 Dados enviados: {account_data}")
            print(f"📥 Status da resposta: {response.status_code}")
            print(f"📄 Conteúdo: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    account_id = result.get('account_id')
                    print(f"✅ Conta criada com sucesso! ID: {account_id}")
                    return account_id
                else:
                    print(f"❌ Erro na resposta: {result.get('message')}")
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"🚨 ERRO DURANTE CRIAÇÃO DE CONTA: {e}")
        
        return None
    
    def test_transaction_creation(self, account_id):
        """Testar criação de transação"""
        print(f"\n💰 TESTANDO CRIAÇÃO DE TRANSAÇÃO (Conta ID: {account_id})")
        print("=" * 50)
        
        transaction_data = {
            'description': f'Transação Teste {datetime.now().strftime("%H:%M:%S")}',
            'amount': 50.00,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'type': 'despesa',
            'category_id': '8',  # Categoria de teste
            'account_id': str(account_id),
            'notes': 'Teste automático de transação'
        }
        
        try:
            response = self.session.post(
                f'{self.base_url}/transactions/new',
                json=transaction_data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"📤 Dados enviados: {transaction_data}")
            print(f"📥 Status da resposta: {response.status_code}")
            print(f"📄 Conteúdo: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ Transação criada com sucesso!")
                    return True
                else:
                    print(f"❌ Erro na resposta: {result.get('message')}")
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"🚨 ERRO DURANTE CRIAÇÃO DE TRANSAÇÃO: {e}")
        
        return False
    
    def check_database_after_test(self):
        """Verificar estado do banco após o teste"""
        print("\n🔍 ESTADO DO BANCO APÓS O TESTE")
        print("=" * 50)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar transações existentes
        cursor.execute("SELECT COUNT(*) FROM transactions")
        transaction_count = cursor.fetchone()[0]
        print(f"📊 Transações no banco: {transaction_count}")
        
        # Verificar últimas transações
        cursor.execute("SELECT id, description, amount, type, date FROM transactions ORDER BY id DESC LIMIT 5")
        recent = cursor.fetchall()
        print("🕒 Últimas transações:")
        for trans in recent:
            print(f"  ID {trans[0]} | {trans[1]} | R$ {trans[2]} | {trans[3]} | {trans[4]}")
        
        # Verificar contas
        cursor.execute("SELECT id, name, current_balance FROM accounts WHERE is_active = 1 ORDER BY id DESC LIMIT 5")
        accounts = cursor.fetchall()
        print(f"\n💳 Últimas contas:")
        for acc in accounts:
            print(f"  ID {acc[0]} | {acc[1]} | R$ {acc[2]}")
        
        conn.close()
        return transaction_count
    
    def check_server_logs(self):
        """Verificar logs do servidor"""
        print("\n📋 VERIFICANDO LOGS DO SERVIDOR")
        print("=" * 50)
        
        try:
            # Fazer uma requisição simples para gerar logs
            response = self.session.get(f'{self.base_url}/dashboard')
            print(f"📊 Status dashboard: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Erro ao acessar dashboard: {e}")
    
    def run_complete_test(self):
        """Executar teste completo"""
        print("🧪 TESTE COMPLETO DE TRANSAÇÃO E PERSISTÊNCIA")
        print("=" * 80)
        
        # 1. Verificar estado inicial
        initial_transactions, initial_accounts, initial_categories = self.check_database_before_test()
        
        # 2. Fazer login
        if not self.perform_login():
            print("❌ TESTE FALHOU: Não foi possível fazer login")
            return
        
        # 3. Testar criação de conta
        account_id = self.test_account_creation()
        if not account_id:
            print("⚠️ Falha ao criar conta, tentando com conta existente...")
            account_id = 1  # Usar conta existente
        
        # 4. Testar criação de transação
        transaction_success = self.test_transaction_creation(account_id)
        
        # 5. Aguardar um momento para persistence
        print("\n⏳ Aguardando persistência...")
        time.sleep(2)
        
        # 6. Verificar estado final
        final_transactions = self.check_database_after_test()
        
        # 7. Verificar logs do servidor
        self.check_server_logs()
        
        # 8. Análise final
        print("\n📊 ANÁLISE FINAL")
        print("=" * 50)
        print(f"Transações iniciais: {initial_transactions}")
        print(f"Transações finais: {final_transactions}")
        print(f"Diferença: {final_transactions - initial_transactions}")
        
        if final_transactions > initial_transactions:
            print("✅ TESTE PASSOU: Dados foram persistidos corretamente!")
        else:
            print("❌ TESTE FALHOU: Dados não foram persistidos!")
            print("🔧 PROBLEMAS POSSÍVEIS:")
            print("   - Rollback de transação")
            print("   - Erro de commit no banco")
            print("   - Problema de sessão")
            print("   - Validação falhando")
        
        print("=" * 80)

if __name__ == '__main__':
    tester = TransactionTester()
    tester.run_complete_test()
