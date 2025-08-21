#!/usr/bin/env python3
"""Script de teste para verificar se o app.py está funcionando"""

try:
    print("🧪 Testando importação do módulo app...")
    import app
    print("✅ Import OK")
    
    print("🧪 Verificando atributos...")
    attrs = [x for x in dir(app) if not x.startswith('_')]
    print(f"📋 Atributos encontrados: {attrs}")
    
    if hasattr(app, 'app'):
        print("✅ Atributo 'app' encontrado")
        print(f"✅ Tipo: {type(app.app).__name__}")
        
        # Testar se é uma Flask app
        if hasattr(app.app, 'url_map'):
            routes = [rule.rule for rule in app.app.url_map.iter_rules()]
            print(f"✅ {len(routes)} rotas encontradas")
            print(f"🎯 Rota /health existe: {'/health' in routes}")
        else:
            print("❌ Não é uma aplicação Flask válida")
    else:
        print("❌ Atributo 'app' não encontrado")
        
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
except Exception as e:
    print(f"❌ Erro geral: {e}")
    import traceback
    traceback.print_exc()
