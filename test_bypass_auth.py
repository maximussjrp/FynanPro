# Sistema de Teste de Transação com Bypass de Autenticação
import requests
import json
import sqlite3
from datetime import datetime

class TransactionBypassTester:
    def __init__(self):
        self.base_url = 'http://127.0.0.1:5000'
        self.session = requests.Session()
        self.db_path = 'finance_planner_saas.db'
        
    def test_transaction_creation_direct_endpoint(self):
        """Testar criação de transação diretamente no endpoint"""
        print("🧪 TESTE DIRETO NO ENDPOINT /transactions/new")
        print("=" * 60)
        
        # Primeiro, vamos fazer login manual via browser e copiar cookies
        # Ou criar uma rota de teste temporária
        
        transaction_data = {
            'description': f'Teste Endpoint Direto {datetime.now().strftime("%H:%M:%S")}',
            'amount': 123.45,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'type': 'despesa',
            'category_id': '8',
            'account_id': '1',
            'notes': 'Teste direto no endpoint com sessão simulada'
        }
        
        print(f"📤 Dados da transação: {transaction_data}")
        
        try:
            # Tentar fazer login primeiro
            login_response = self.session.post(f'{self.base_url}/login', data={
                'email': 'admin@fynanpro.com',
                'password': 'admin123'
            })
            
            print(f"🔐 Status do login: {login_response.status_code}")
            print(f"🔗 URL após login: {login_response.url}")
            print(f"🍪 Cookies: {dict(self.session.cookies)}")
            
            # Tentar criar transação
            response = self.session.post(
                f'{self.base_url}/transactions/new',
                json=transaction_data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"📥 Status da transação: {response.status_code}")
            print(f"📄 Response headers: {dict(response.headers)}")
            print(f"📄 Response content: {response.text[:500]}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('success'):
                        print("✅ Transação criada via endpoint!")
                        return True
                    else:
                        print(f"❌ Erro na resposta: {result.get('message', 'Erro desconhecido')}")
                except:
                    print("⚠️ Resposta não é JSON válido")
            
            return False
            
        except Exception as e:
            print(f"🚨 ERRO: {e}")
            return False
    
    def check_database_changes(self):
        """Verificar mudanças no banco"""
        print("\n🔍 VERIFICANDO BANCO APÓS TESTE")
        print("=" * 50)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar últimas transações
        cursor.execute("SELECT id, description, amount, type, date FROM transactions ORDER BY id DESC LIMIT 10")
        recent = cursor.fetchall()
        
        print("🕒 Últimas 10 transações:")
        for trans in recent:
            print(f"  ID {trans[0]} | {trans[1][:40]} | R$ {trans[2]} | {trans[3]} | {trans[4]}")
        
        conn.close()
    
    def run_bypass_test(self):
        """Executar teste com bypass"""
        print("🎯 TESTE DE BYPASS DE AUTENTICAÇÃO")
        print("=" * 80)
        
        # Verificar estado inicial
        print("📊 ESTADO INICIAL:")
        self.check_database_changes()
        
        # Testar endpoint
        success = self.test_transaction_creation_direct_endpoint()
        
        # Verificar mudanças
        print("\n📊 ESTADO FINAL:")
        self.check_database_changes()
        
        if success:
            print("\n✅ TESTE PASSOU: Endpoint funcionando!")
        else:
            print("\n❌ TESTE FALHOU: Problema no endpoint ou autenticação")
        
        print("=" * 80)

if __name__ == '__main__':
    tester = TransactionBypassTester()
    tester.run_bypass_test()
