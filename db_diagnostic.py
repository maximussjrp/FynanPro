# Database Diagnostic and Repair Tool for FynanPro
import sqlite3
import logging
import sys
from datetime import datetime

class DatabaseDiagnostic:
    def __init__(self, db_path='finance_planner_saas.db'):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def diagnose_all(self):
        """Diagnóstico completo do banco de dados"""
        print("🔍 INICIANDO DIAGNÓSTICO AVANÇADO DO BANCO DE DADOS")
        print("=" * 60)
        
        try:
            self.connect()
            
            # 1. Verificar estrutura das tabelas
            self.check_table_structure()
            
            # 2. Verificar integridade referencial
            self.check_referential_integrity()
            
            # 3. Verificar dados inconsistentes
            self.check_data_consistency()
            
            # 4. Verificar performance
            self.check_performance()
            
            # 5. Sugerir otimizações
            self.suggest_optimizations()
            
        except Exception as e:
            print(f"🚨 ERRO DURANTE DIAGNÓSTICO: {e}")
        finally:
            self.close()
    
    def check_table_structure(self):
        """Verificar estrutura das tabelas"""
        print("\n📋 VERIFICANDO ESTRUTURA DAS TABELAS")
        print("-" * 40)
        
        tables = ['users', 'accounts', 'transactions', 'categories']
        
        for table in tables:
            try:
                cursor = self.conn.cursor()
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                print(f"\n✅ Tabela: {table}")
                for col in columns:
                    print(f"   {col[1]} | {col[2]} | {'NOT NULL' if col[3] else 'NULL'} | Default: {col[4] or 'None'}")
                
                # Verificar se a tabela tem dados
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   📊 Total de registros: {count}")
                
            except sqlite3.Error as e:
                print(f"❌ ERRO na tabela {table}: {e}")
    
    def check_referential_integrity(self):
        """Verificar integridade referencial"""
        print("\n🔗 VERIFICANDO INTEGRIDADE REFERENCIAL")
        print("-" * 40)
        
        # Verificar transactions -> users
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM transactions t 
            LEFT JOIN users u ON t.user_id = u.id 
            WHERE u.id IS NULL AND t.user_id IS NOT NULL
        """)
        orphaned_transactions = cursor.fetchone()[0]
        
        if orphaned_transactions > 0:
            print(f"⚠️  {orphaned_transactions} transações órfãs (user_id inválido)")
        else:
            print("✅ Integridade transactions -> users OK")
        
        # Verificar transactions -> accounts
        cursor.execute("""
            SELECT COUNT(*) 
            FROM transactions t 
            LEFT JOIN accounts a ON t.account_id = a.id 
            WHERE a.id IS NULL AND t.account_id IS NOT NULL
        """)
        orphaned_account_transactions = cursor.fetchone()[0]
        
        if orphaned_account_transactions > 0:
            print(f"⚠️  {orphaned_account_transactions} transações com account_id inválido")
        else:
            print("✅ Integridade transactions -> accounts OK")
    
    def check_data_consistency(self):
        """Verificar consistência dos dados"""
        print("\n📊 VERIFICANDO CONSISTÊNCIA DOS DADOS")
        print("-" * 40)
        
        cursor = self.conn.cursor()
        
        # Verificar transações com valores zero ou negativos incorretos
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE amount = 0")
        zero_transactions = cursor.fetchone()[0]
        if zero_transactions > 0:
            print(f"⚠️  {zero_transactions} transações com valor zero")
        
        # Verificar transações com datas futuras muito distantes
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE date > date('now', '+1 year')")
        future_transactions = cursor.fetchone()[0]
        if future_transactions > 0:
            print(f"⚠️  {future_transactions} transações com datas muito futuras")
        
        # Verificar duplicatas potenciais
        cursor.execute("""
            SELECT description, amount, date, COUNT(*) as count
            FROM transactions 
            GROUP BY description, amount, date 
            HAVING COUNT(*) > 1
            LIMIT 5
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"⚠️  Possíveis duplicatas encontradas:")
            for dup in duplicates:
                print(f"     {dup[0]} | R$ {dup[1]} | {dup[2]} (x{dup[3]})")
        else:
            print("✅ Nenhuma duplicata óbvia encontrada")
    
    def check_performance(self):
        """Verificar performance do banco"""
        print("\n⚡ VERIFICANDO PERFORMANCE")
        print("-" * 40)
        
        cursor = self.conn.cursor()
        
        # Verificar se há índices
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = cursor.fetchall()
        
        print(f"📈 Índices personalizados: {len(indexes)}")
        for index in indexes:
            print(f"   - {index[0]}")
        
        # Verificar tamanho do banco
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        
        db_size_mb = (page_count * page_size) / 1024 / 1024
        print(f"💾 Tamanho do banco: {db_size_mb:.2f} MB")
    
    def suggest_optimizations(self):
        """Sugerir otimizações"""
        print("\n🚀 SUGESTÕES DE OTIMIZAÇÃO")
        print("-" * 40)
        
        cursor = self.conn.cursor()
        
        # Verificar se precisa de índices
        cursor.execute("SELECT COUNT(*) FROM transactions")
        transaction_count = cursor.fetchone()[0]
        
        if transaction_count > 1000:
            print("💡 Considere adicionar índices:")
            print("   - CREATE INDEX idx_transactions_date ON transactions(date)")
            print("   - CREATE INDEX idx_transactions_user_date ON transactions(user_id, date)")
            print("   - CREATE INDEX idx_transactions_account ON transactions(account_id)")
        
        # Verificar necessidade de VACUUM
        cursor.execute("PRAGMA freelist_count")
        free_pages = cursor.fetchone()[0]
        
        if free_pages > 100:
            print(f"🧹 Banco tem {free_pages} páginas livres. Execute VACUUM para compactar")
        
        print("\n✅ DIAGNÓSTICO CONCLUÍDO")
        print("=" * 60)
    
    def repair_database(self):
        """Reparar problemas comuns do banco"""
        print("\n🔧 INICIANDO REPARO AUTOMÁTICO")
        print("-" * 40)
        
        try:
            self.connect()
            cursor = self.conn.cursor()
            
            # 1. Remover transações órfãs
            cursor.execute("""
                DELETE FROM transactions 
                WHERE user_id NOT IN (SELECT id FROM users) 
                AND user_id IS NOT NULL
            """)
            deleted_orphaned = cursor.rowcount
            if deleted_orphaned > 0:
                print(f"🗑️  Removidas {deleted_orphaned} transações órfãs")
            
            # 2. Criar índices de performance
            indexes_to_create = [
                ("idx_transactions_date", "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)"),
                ("idx_transactions_user", "CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)"),
                ("idx_transactions_account", "CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)"),
                ("idx_accounts_user", "CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id)")
            ]
            
            for idx_name, idx_sql in indexes_to_create:
                try:
                    cursor.execute(idx_sql)
                    print(f"📈 Índice {idx_name} criado/verificado")
                except sqlite3.Error as e:
                    print(f"⚠️  Erro ao criar índice {idx_name}: {e}")
            
            # 3. Atualizar estatísticas
            cursor.execute("ANALYZE")
            print("📊 Estatísticas atualizadas")
            
            # 4. Compactar banco se necessário
            cursor.execute("PRAGMA freelist_count")
            free_pages = cursor.fetchone()[0]
            
            if free_pages > 50:
                cursor.execute("VACUUM")
                print("🧹 Banco compactado")
            
            self.conn.commit()
            print("✅ REPARO CONCLUÍDO COM SUCESSO")
            
        except Exception as e:
            print(f"🚨 ERRO DURANTE REPARO: {e}")
            if self.conn:
                self.conn.rollback()
        finally:
            self.close()

def main():
    print("🏦 FYNANPRO - FERRAMENTA DE DIAGNÓSTICO DE BANCO DE DADOS")
    print("========================================================")
    
    diagnostic = DatabaseDiagnostic()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'repair':
        diagnostic.repair_database()
    else:
        diagnostic.diagnose_all()
        print("\n💡 Para executar reparo automático, use: python db_diagnostic.py repair")

if __name__ == '__main__':
    main()
