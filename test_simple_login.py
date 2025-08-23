# Teste Simples de Login
import requests

session = requests.Session()
base_url = 'http://127.0.0.1:5000'

print("🧪 TESTE SIMPLES DE LOGIN")
print("=" * 40)

# 1. Login
print("1. Fazendo login...")
login_data = {
    'email': 'admin@fynanpro.com',
    'password': 'admin123'
}

response = session.post(f'{base_url}/login', data=login_data)
print(f"   Status: {response.status_code}")
print(f"   URL: {response.url}")
print(f"   Cookies: {dict(session.cookies)}")

# 2. Testar dashboard
print("\n2. Testando dashboard...")
dashboard = session.get(f'{base_url}/dashboard')
print(f"   Status: {dashboard.status_code}")
print(f"   URL: {dashboard.url}")

if dashboard.status_code == 200 and 'login' not in dashboard.url:
    print("   ✅ LOGIN FUNCIONOU!")
else:
    print("   ❌ Login não funcionou")

print(f"   Content preview: {dashboard.text[:200]}...")
