# Teste Final de Sessão - Verificar se problema foi resolvido
import requests
import time
import json

class SessionTester:
    def __init__(self):
        self.base_url = 'http://127.0.0.1:5000'
        self.session = requests.Session()
    
    def test_login_and_session(self):
        """Testar login completo e manutenção de sessão"""
        print("🎯 TESTE FINAL DE SESSÃO")
        print("=" * 60)
        
        # 1. Verificar debug inicial
        print("1️⃣ VERIFICANDO ESTADO INICIAL")
        debug_response = self.session.get(f'{self.base_url}/debug-session')
        print(f"   Status debug: {debug_response.status_code}")
        if 'user_id' in debug_response.text:
            print("   ⚠️ Sessão já existe")
        else:
            print("   ✅ Sem sessão (esperado)")
        
        # 2. Tentar fazer login
        print("\n2️⃣ FAZENDO LOGIN")
        login_data = {
            'email': 'admin@fynanpro.com',
            'password': 'admin123',
            'remember_me': 'on'
        }
        
        login_response = self.session.post(f'{self.base_url}/login', data=login_data)
        print(f"   Status login: {login_response.status_code}")
        print(f"   URL final: {login_response.url}")
        print(f"   Cookies: {dict(self.session.cookies)}")
        
        # 3. Verificar debug pós-login
        print("\n3️⃣ VERIFICANDO SESSÃO PÓS-LOGIN")
        debug_response = self.session.get(f'{self.base_url}/debug-session')
        print(f"   Status debug: {debug_response.status_code}")
        
        if 'user_id' in debug_response.text and 'admin@fynanpro.com' in debug_response.text:
            print("   ✅ SESSÃO CRIADA COM SUCESSO!")
            session_ok = True
        else:
            print("   ❌ Problema na criação da sessão")
            session_ok = False
        
        # 4. Testar acesso ao dashboard (rota protegida)
        print("\n4️⃣ TESTANDO ROTA PROTEGIDA (dashboard)")
        dashboard_response = self.session.get(f'{self.base_url}/dashboard')
        print(f"   Status dashboard: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200 and 'login' not in dashboard_response.url:
            print("   ✅ ACESSO AO DASHBOARD OK!")
            dashboard_ok = True
        else:
            print("   ❌ Redirecionado para login (problema na sessão)")
            dashboard_ok = False
        
        # 5. Testar criação de transação (rota principal do problema)
        print("\n5️⃣ TESTANDO CRIAÇÃO DE TRANSAÇÃO")
        transaction_data = {
            'description': f'Teste Sessão Final {time.strftime("%H:%M:%S")}',
            'amount': '199.99',
            'date': time.strftime('%Y-%m-%d'),
            'type': 'receita',
            'category': 'Teste > Final',
            'account_id': '1'
        }
        
        # Tentar via POST JSON (como no app real)
        transaction_response = self.session.post(
            f'{self.base_url}/transactions/new',
            json=transaction_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Status transação: {transaction_response.status_code}")
        print(f"   URL final: {transaction_response.url}")
        
        try:
            if transaction_response.headers.get('content-type', '').startswith('application/json'):
                result = transaction_response.json()
                if result.get('success'):
                    print("   ✅ TRANSAÇÃO CRIADA COM SUCESSO!")
                    transaction_ok = True
                else:
                    print(f"   ❌ Erro na transação: {result.get('message', 'Desconhecido')}")
                    transaction_ok = False
            else:
                # Se não é JSON, pode ser redirect para login
                if 'login' in transaction_response.text.lower():
                    print("   ❌ Redirecionado para login (problema na sessão)")
                    transaction_ok = False
                else:
                    print("   ⚠️ Resposta inesperada")
                    transaction_ok = False
        except:
            print("   ❌ Erro ao processar resposta")
            transaction_ok = False
        
        # 6. Resultado final
        print("\n🏁 RESULTADO FINAL")
        print("=" * 40)
        print(f"Login: {'✅ OK' if session_ok else '❌ FALHOU'}")
        print(f"Dashboard: {'✅ OK' if dashboard_ok else '❌ FALHOU'}")
        print(f"Transação: {'✅ OK' if transaction_ok else '❌ FALHOU'}")
        
        if session_ok and dashboard_ok and transaction_ok:
            print("\n🎉 PROBLEMA DE SESSÃO RESOLVIDO!")
            print("   O usuário agora pode fazer login e criar transações!")
            return True
        else:
            print("\n⚠️ Ainda há problemas de sessão")
            print("   Mais diagnósticos necessários")
            return False
    
    def run_test(self):
        return self.test_login_and_session()

if __name__ == '__main__':
    tester = SessionTester()
    success = tester.run_test()
    
    if success:
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("   1. O usuário pode acessar: http://127.0.0.1:5000/login")
        print("   2. Fazer login com: admin@fynanpro.com / admin123")
        print("   3. Criar transações normalmente!")
    else:
        print("\n🔧 AINDA PRECISA DE AJUSTES:")
        print("   Verificar logs do servidor para mais detalhes")
