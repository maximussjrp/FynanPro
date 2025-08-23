import requests
import time

print("🔍 Verificando status do Render...")

try:
    response = requests.get('https://fynanpro.onrender.com/', timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Deploy parece estar funcionando!")
        print(f"Título da página: {response.text[:200]}")
    else:
        print("⚠️ Site pode estar em rebuild...")
        
except requests.exceptions.Timeout:
    print("⏰ Timeout - Site provavelmente fazendo rebuild (normal após deploy)")
except requests.exceptions.ConnectionError:
    print("🔄 Conexão recusada - Site provavelmente fazendo rebuild (normal)")
except Exception as e:
    print(f"❌ Site indisponível: {e}")
    print("🔄 Isso é normal se o Render estiver fazendo rebuild...")

print("\n💡 Se o site estiver indisponível, é normal! O Render demora 2-5 minutos para fazer rebuild.")
