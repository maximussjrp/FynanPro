import requests
import time

# Testar a nova aba de transações
print("🧪 TESTANDO NOVA ABA DE TRANSAÇÕES")
print("=" * 50)

s = requests.Session()

# 1. Login
print("1️⃣ Fazendo login...")
login = s.post('http://127.0.0.1:5000/login', data={
    'email': 'admin@fynanpro.com', 
    'password': 'admin123'
})
print(f"   Login status: {login.status_code}")
print(f"   Cookies: {bool(s.cookies)}")

# 2. Testar aba de transações
print("\n2️⃣ Testando /transactions...")
trans = s.get('http://127.0.0.1:5000/transactions')
print(f"   Status: {trans.status_code}")

if trans.status_code == 200:
    print("   ✅ ABA DE TRANSAÇÕES FUNCIONANDO!")
    print(f"   Tamanho da resposta: {len(trans.text)} bytes")
    
    # Verificar se contém transações
    if 'Transação' in trans.text or 'transaction' in trans.text.lower():
        print("   📊 Contém dados de transações!")
    
    if 'Extrato' in trans.text:
        print("   📋 Título 'Extrato' encontrado!")
    
else:
    print(f"   ❌ Erro: {trans.status_code}")
    print(f"   Conteúdo: {trans.text[:200]}...")

print("\n📈 RESUMO:")
print(f"Login funcionou: {'✅' if login.status_code == 200 and s.cookies else '❌'}")
print(f"Transações funcionou: {'✅' if trans.status_code == 200 else '❌'}")

if login.status_code == 200 and s.cookies and trans.status_code == 200:
    print("\n🎉 SUCESSO TOTAL! A aba de transações está funcionando!")
else:
    print("\n⚠️ Ainda há problemas para resolver")
