#!/usr/bin/env python3
"""Debug version of app.py to find the issue"""

print("🧪 Iniciando debug do app.py...")

try:
    print("1️⃣ Importando Flask...")
    from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
    print("✅ Flask importado")
    
    print("2️⃣ Importando Flask-Login...")
    from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
    print("✅ Flask-Login importado")
    
    print("3️⃣ Importando Werkzeug...")
    from werkzeug.security import generate_password_hash, check_password_hash
    print("✅ Werkzeug importado")
    
    print("4️⃣ Importando bibliotecas padrão...")
    import sqlite3
    import os
    from datetime import datetime, timedelta
    import logging
    from contextlib import contextmanager
    import json
    from decimal import Decimal
    print("✅ Bibliotecas padrão importadas")
    
    print("5️⃣ Criando app Flask...")
    app = Flask(__name__)
    print("✅ App Flask criado")
    
    print("6️⃣ Configurando app...")
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fynanpro-secret-key-2024')
    app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'finance_planner_saas.db')
    print("✅ App configurado")
    
    print("7️⃣ Configurando logging...")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    print("✅ Logging configurado")
    
    print("8️⃣ Configurando Login Manager...")
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    print("✅ Login Manager configurado")
    
    print("9️⃣ Adicionando rota de teste...")
    @app.route('/debug')
    def debug():
        return "Debug OK!"
    print("✅ Rota de teste adicionada")
    
    print("🎉 SUCESSO! App debug criado com sucesso")
    print(f"🎯 App final: {app}")
    
except Exception as e:
    print(f"❌ ERRO no debug: {e}")
    import traceback
    traceback.print_exc()
