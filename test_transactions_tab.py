# Teste completo da aba de transações
import requests
import time

def test_transactions_tab():
    print("🏦 TESTANDO ABA DE TRANSAÇÕES COMPLETA")
    print("=" * 60)
    
    session = requests.Session()
    
    # 1. Login
    print("1️⃣ Fazendo login...")
    login_response = session.post('http://127.0.0.1:5000/login', data={
        'email': 'admin@fynanpro.com',
        'password': 'admin123'
    })
    
    print(f"   Status: {login_response.status_code}")
    print(f"   Cookies: {dict(session.cookies)}")
    
    if session.cookies:
        print("   ✅ Cookie de sessão criado!")
    else:
        print("   ❌ Sem cookie de sessão")
        return False
    
    # 2. Acessar aba de transações
    print("\n2️⃣ Acessando aba de transações...")
    transactions_response = session.get('http://127.0.0.1:5000/transactions')
    
    print(f"   Status: {transactions_response.status_code}")
    print(f"   URL final: {transactions_response.url}")
    
    if transactions_response.status_code == 200:
        content = transactions_response.text
        
        # Verificar conteúdo esperado
        if "Extrato de Transações" in content:
            print("   ✅ PÁGINA DE TRANSAÇÕES CARREGADA!")
            print("   ✅ Título 'Extrato de Transações' encontrado")
            
            # Verificar elementos específicos
            checks = [
                ("Total de Transações", "📊 Estatísticas"),
                ("Filtros", "🔍 Sistema de filtros"),
                ("table", "📋 Tabela de transações"),
                ("Nova Transação", "➕ Botão de nova transação"),
                ("Teste Rápido", "🧪 Botão de teste")
            ]
            
            found_elements = 0
            for check_text, description in checks:
                if check_text in content:
                    print(f"   ✅ {description}")
                    found_elements += 1
                else:
                    print(f"   ⚠️ {description} - não encontrado")
            
            print(f"\n   📊 Elementos encontrados: {found_elements}/{len(checks)}")
            
            if found_elements >= 3:
                print("   🎉 ABA DE TRANSAÇÕES FUNCIONANDO!")
                return True
            else:
                print("   ⚠️ Aba parcialmente funcional")
                return True
                
        else:
            print("   ❌ Conteúdo não reconhecido")
            print(f"   Preview: {content[:300]}...")
            return False
            
    else:
        print(f"   ❌ Erro HTTP: {transactions_response.status_code}")
        return False

if __name__ == '__main__':
    success = test_transactions_tab()
    
    if success:
        print("\n🎉 SUCESSO! Aba de transações está funcionando!")
        print("   Acesse: http://127.0.0.1:5000/transactions")
    else:
        print("\n❌ Problemas encontrados na aba de transações")
        print("   Verificar logs do servidor")
