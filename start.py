#!/usr/bin/env python3
"""
Script de inicialização para o FynanPro em produção
"""
import os
import sys

def main():
    """Inicializa o banco e inicia a aplicação"""
    print("🚀 Iniciando FynanPro...")
    
    # Criar banco se não existir
    try:
        print("🗄️ Verificando banco de dados...")
        import init_db
        init_db.init_database()
    except Exception as e:
        print(f"⚠️ Aviso: {e}")
    
    # Inicializar aplicação
    print("🌐 Iniciando servidor web...")
    from app import app
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()
