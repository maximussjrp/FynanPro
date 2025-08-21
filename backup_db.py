"""
Script para backup e restauração do banco de dados
"""
import sqlite3
import os
import shutil
from datetime import datetime

DATABASE_PATH = 'finance_planner_saas.db'
BACKUP_DIR = 'database_backups'

def create_backup():
    """Cria um backup do banco de dados"""
    if not os.path.exists(DATABASE_PATH):
        print("❌ Banco de dados não encontrado!")
        return False
        
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f'backup_{timestamp}.db')
    
    try:
        shutil.copy2(DATABASE_PATH, backup_path)
        print(f"✅ Backup criado: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        return False

def export_users_sql():
    """Exporta dados dos usuários como SQL INSERT statements"""
    if not os.path.exists(DATABASE_PATH):
        print("❌ Banco de dados não encontrado!")
        return
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print("-- SQL para recriar usuários:")
        print("-- Execute este código no banco de produção")
        print()
        
        for user in users:
            values = []
            for value in user:
                if value is None:
                    values.append('NULL')
                elif isinstance(value, str):
                    values.append(f"'{value.replace("'", "''")}'")
                else:
                    values.append(str(value))
            
            sql = f"INSERT INTO users ({', '.join(columns)}) VALUES ({', '.join(values)});"
            print(sql)
        
        conn.close()
        print(f"\n✅ {len(users)} usuários exportados")
        
    except Exception as e:
        print(f"❌ Erro ao exportar: {e}")

if __name__ == "__main__":
    print("🗄️ Gerenciador de Banco de Dados FynanPro")
    print("1. Criando backup...")
    backup_file = create_backup()
    
    print("\n2. Exportando usuários como SQL...")
    export_users_sql()
    
    if backup_file:
        print(f"\n📁 Backup salvo em: {backup_file}")
        print("💡 Dica: Salve este arquivo em um local seguro!")
