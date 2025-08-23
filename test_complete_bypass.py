# Teste Completo de Transação com Servidor Integrado
import threading
import time
import requests
import sqlite3
from datetime import datetime
import sys
import os

# Adicionar o diretório atual ao path para importar o Flask app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class IntegratedTransactionTester:
    def __init__(self):
        self.base_url = 'http://127.0.0.1:5000'
        self.db_path = 'finance_planner_saas.db'
        self.server_thread = None
        self.app = None
    
    def start_flask_server(self):
        """Iniciar servidor Flask em thread separada"""
        try:
            from app_simple_advanced import app
            self.app = app
            
            print("🚀 Iniciando servidor Flask...")
            
            def run_server():
                with app.app_context():
                    from app_simple_advanced import init_db, create_default_data, ensure_admin_user
                    init_db()
                    create_default_data()
                    ensure_admin_user()
                
                app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            # Aguardar servidor iniciar
            print("⏳ Aguardando servidor iniciar...")
            time.sleep(3)
            
            # Testar se servidor está respondendo
            for i in range(10):
                try:
                    response = requests.get(f'{self.base_url}/', timeout=2)
                    if response.status_code in [200, 302]:
                        print("✅ Servidor Flask iniciado com sucesso!")
                        return True
                except:
                    print(f"⏳ Tentativa {i+1}/10...")
                    time.sleep(1)
            
            print("❌ Falha ao iniciar servidor Flask")
            return False
            
        except Exception as e:
            print(f"🚨 Erro ao iniciar servidor: {e}")
            return False
    
    def test_bypass_route(self):
        """Testar rota de bypass"""
        print("🧪 TESTANDO ROTA DE BYPASS")
        print("=" * 50)
        
        try:
            # Teste GET - Formulário
            print("📋 Testando formulário GET...")
            response = requests.get(f'{self.base_url}/test-transaction-bypass', timeout=5)
            print(f"📊 Status GET: {response.status_code}")
            
            if response.status_code == 200 and 'Teste de Transação' in response.text:
                print("✅ Formulário carregado com sucesso!")
            else:
                print("❌ Problema ao carregar formulário")
                return False
            
            # Teste POST - Criar transação
            print("\n💰 Testando criação de transação...")
            
            transaction_data = {
                'description': f'Teste Bypass {datetime.now().strftime("%H:%M:%S")}',
                'amount': '150.75',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'type': 'receita',
                'category_id': '8',
                'account_id': '1'
            }
            
            print(f"📤 Dados enviados: {transaction_data}")
            
            response = requests.post(
                f'{self.base_url}/test-transaction-bypass', 
                data=transaction_data,
                timeout=10
            )
            
            print(f"📊 Status POST: {response.status_code}")
            print(f"📄 Conteúdo (primeiros 300 chars): {response.text[:300]}")
            
            if response.status_code == 200 and 'SUCESSO' in response.text:
                print("✅ Transação criada via bypass!")
                return True
            else:
                print("❌ Falha na criação via bypass")
                return False
                
        except Exception as e:
            print(f"🚨 Erro no teste bypass: {e}")
            return False
    
    def check_database(self):
        """Verificar estado do banco"""
        print("\n🔍 VERIFICANDO BANCO DE DADOS")
        print("=" * 40)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Contar transações
            cursor.execute("SELECT COUNT(*) FROM transactions")
            total = cursor.fetchone()[0]
            print(f"📊 Total de transações: {total}")
            
            # Últimas 5
            cursor.execute("SELECT id, description, amount, type, date FROM transactions ORDER BY id DESC LIMIT 5")
            recent = cursor.fetchall()
            
            print("🕒 Últimas 5 transações:")
            for trans in recent:
                print(f"  ID {trans[0]} | {trans[1][:30]} | R$ {trans[2]} | {trans[3]} | {trans[4]}")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"🚨 Erro ao verificar banco: {e}")
            return False
    
    def run_complete_test(self):
        """Executar teste completo"""
        print("🎯 TESTE COMPLETO DE TRANSAÇÃO")
        print("=" * 80)
        
        # Estado inicial
        print("📊 ESTADO INICIAL:")
        self.check_database()
        
        # Iniciar servidor
        if not self.start_flask_server():
            print("❌ Falha ao iniciar servidor")
            return
        
        try:
            # Testar rota de bypass
            success = self.test_bypass_route()
            
            # Estado final
            print("\n📊 ESTADO FINAL:")
            self.check_database()
            
            if success:
                print("\n✅ TESTE COMPLETO PASSOU!")
                print("🎉 Transação criada com sucesso via bypass!")
            else:
                print("\n❌ TESTE COMPLETO FALHOU!")
                print("🔍 Verificar logs para mais detalhes")
            
        finally:
            print("\n🛑 Encerrando teste...")
            # O servidor vai encerrar automaticamente quando o script terminar

if __name__ == '__main__':
    tester = IntegratedTransactionTester()
    tester.run_complete_test()
