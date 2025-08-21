#!/usr/bin/env python3
"""Teste básico do Flask"""

print("🧪 Iniciando teste do Flask...")

try:
    from flask import Flask
    print("✅ Flask importado com sucesso")
    
    app = Flask(__name__)
    print("✅ App Flask criado")
    
    @app.route('/test')
    def test():
        return "Hello World!"
    
    print("✅ Rota de teste adicionada")
    print(f"✅ App configurado: {app}")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
