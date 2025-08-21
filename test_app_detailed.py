#!/usr/bin/env python3
"""Teste detalhado do app.py"""

import sys
import traceback

try:
    print("🧪 Tentando importar app...")
    import app
    print("✅ app importado com sucesso")
    
    print(f"📋 Atributos do módulo app: {dir(app)}")
    
    if hasattr(app, 'app'):
        print(f"✅ app.app existe: {app.app}")
        print(f"📍 Tipo: {type(app.app)}")
        if hasattr(app.app, 'url_map'):
            routes = list(app.app.url_map.iter_rules())
            print(f"🎯 {len(routes)} rotas encontradas:")
            for rule in routes:
                print(f"   - {rule.rule} [{', '.join(rule.methods)}]")
    else:
        print("❌ app.app não existe")
        
    # Verificar se há outras variáveis globais
    module_vars = [name for name in dir(app) if not name.startswith('_')]
    print(f"📦 Variáveis públicas do módulo: {module_vars}")
        
except Exception as e:
    print(f"❌ ERRO: {e}")
    print("📜 Traceback completo:")
    traceback.print_exc()
    
    # Verificar se é problema de importação específica
    print("\n🔍 Testando imports individuais...")
    try:
        from flask import Flask
        print("✅ Flask OK")
    except Exception as flask_err:
        print(f"❌ Flask: {flask_err}")
        
    try:
        from flask_login import LoginManager
        print("✅ Flask-Login OK")
    except Exception as login_err:
        print(f"❌ Flask-Login: {login_err}")
        
    try:
        import sqlite3
        print("✅ SQLite3 OK")
    except Exception as sqlite_err:
        print(f"❌ SQLite3: {sqlite_err}")
