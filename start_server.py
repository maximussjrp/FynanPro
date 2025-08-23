#!/usr/bin/env python3
# Script simples para iniciar o servidor Flask

print("🚀 Iniciando FynanPro Server...")

try:
    from app_simple_advanced import app, init_db, create_default_data, ensure_admin_user
    
    print("📊 Inicializando base de dados...")
    with app.app_context():
        init_db()
        create_default_data()
        ensure_admin_user()
    
    print("✅ Servidor pronto!")
    print("🌐 Acesse: http://127.0.0.1:5000")
    print("👤 Login: admin@fynanpro.com / admin123")
    
    app.run(debug=False, host='127.0.0.1', port=5000)
    
except Exception as e:
    print(f"❌ Erro ao iniciar servidor: {e}")
    import traceback
    traceback.print_exc()
