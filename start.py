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
        import sqlite3
        
        # Criar banco básico
        conn = sqlite3.connect('finance_planner_saas.db')
        cursor = conn.cursor()
        
        # Tabela básica de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(150) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                is_admin BOOLEAN DEFAULT 0,
                plan_type TEXT DEFAULT 'trial',
                plan_start_date DATETIME,
                payment_method TEXT DEFAULT 'free',
                last_payment_date DATETIME,
                total_paid REAL DEFAULT 0.0
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados OK")
        
    except Exception as e:
        print(f"⚠️ Erro no banco: {e}")
    
    # Inicializar aplicação
    print("🌐 Iniciando servidor web...")
    try:
        from app import app
        port = int(os.environ.get('PORT', 5000))
        print(f"🌍 Servidor rodando na porta {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"❌ Erro ao iniciar: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
