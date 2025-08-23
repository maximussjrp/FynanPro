# Teste Direto de Persistência - Bypass do Frontend
import sqlite3
from datetime import datetime
import sys
import os

class DirectDatabaseTester:
    def __init__(self, db_path='finance_planner_saas.db'):
        self.db_path = db_path
        
    def test_direct_transaction_insert(self):
        """Testar inserção direta de transação no banco"""
        print("🔧 TESTE DIRETO DE INSERÇÃO NO BANCO")
        print("=" * 50)
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verificar transações antes
            cursor.execute("SELECT COUNT(*) FROM transactions")
            before_count = cursor.fetchone()[0]
            print(f"📊 Transações antes: {before_count}")
            
            # Inserir transação de teste
            test_data = {
                'user_id': 1,
                'description': f'Teste Direto {datetime.now().strftime("%H:%M:%S")}',
                'amount': 99.99,
                'type': 'despesa',
                'category': '8',  # ID da categoria
                'date': datetime.now().strftime('%Y-%m-%d'),
                'account_id': 1,
                'notes': 'Teste de inserção direta no banco'
            }
            
            # Inserir com SQL direto
            cursor.execute('''
                INSERT INTO transactions (user_id, description, amount, type, category, date, account_id, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (test_data['user_id'], test_data['description'], test_data['amount'], 
                  test_data['type'], test_data['category'], test_data['date'], 
                  test_data['account_id'], test_data['notes']))
            
            transaction_id = cursor.lastrowid
            print(f"✅ Transação inserida com ID: {transaction_id}")
            
            # Verificar se foi inserida
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
            inserted_transaction = cursor.fetchone()
            
            if inserted_transaction:
                print("📋 Dados da transação inserida:")
                print(f"   ID: {inserted_transaction['id']}")
                print(f"   Descrição: {inserted_transaction['description']}")
                print(f"   Valor: R$ {inserted_transaction['amount']}")
                print(f"   Tipo: {inserted_transaction['type']}")
                print(f"   Data: {inserted_transaction['date']}")
            
            # COMMIT para salvar
            conn.commit()
            print("💾 COMMIT executado")
            
            # Verificar após commit
            cursor.execute("SELECT COUNT(*) FROM transactions")
            after_count = cursor.fetchone()[0]
            print(f"📊 Transações depois: {after_count}")
            
            if after_count > before_count:
                print("✅ TESTE PASSOU: Transação persistida com sucesso!")
                return True
            else:
                print("❌ TESTE FALHOU: Transação não foi persistida!")
                return False
                
        except Exception as e:
            print(f"🚨 ERRO: {e}")
            if conn:
                conn.rollback()
                print("🔄 ROLLBACK executado")
            return False
        finally:
            if conn:
                conn.close()
    
    def test_flask_endpoint_simulation(self):
        """Simular o que acontece no endpoint Flask"""
        print("\n🌐 SIMULAÇÃO DO ENDPOINT FLASK")
        print("=" * 50)
        
        try:
            # Importar função do Flask app
            sys.path.append(os.getcwd())
            
            # Simular dados de entrada do endpoint
            current_user = {'id': 1}
            data = {
                'description': f'Teste Flask Sim {datetime.now().strftime("%H:%M:%S")}',
                'amount': 77.77,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'type': 'despesa',
                'category_id': '8',
                'account_id': '1',
                'notes': 'Simulação do endpoint Flask'
            }
            
            print(f"📤 Dados simulados: {data}")
            
            # Usar a mesma lógica do Flask
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Contar antes
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM transactions")
            before_count = cursor.fetchone()[0]
            print(f"📊 Transações antes: {before_count}")
            
            # Validações (como no Flask)
            description = data['description']
            amount = float(data['amount'])
            date_str = data['date']
            transaction_type = data['type']
            account_id = int(data['account_id'])
            chart_account_id = data.get('category_id', '')
            notes = data.get('notes', '')
            
            print(f"🔍 Processando - Type: {transaction_type}, Account: {account_id}, Category: {chart_account_id}")
            
            # Verificar se a conta existe
            account_check = conn.execute('SELECT id FROM accounts WHERE id = ? AND user_id = ?', 
                                       (account_id, current_user['id'])).fetchone()
            
            if not account_check:
                print("❌ Conta não encontrada!")
                return False
                
            print("✅ Conta validada")
            
            # Detectar estrutura da tabela
            cursor.execute("PRAGMA table_info(transactions)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"🔍 Colunas disponíveis: {columns[:5]}...")
            
            # Inserir transação (lógica do Flask)
            if 'user_id' in columns:
                print("🔧 Inserindo com user_id...")
                transaction_id = conn.execute('''
                    INSERT INTO transactions (user_id, description, amount, date, type, category, account_id, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (current_user['id'], description, amount, date_str, transaction_type, 
                      chart_account_id or None, account_id, notes)).lastrowid
            else:
                print("🔧 Inserindo sem user_id...")
                transaction_id = conn.execute('''
                    INSERT INTO transactions (description, amount, date, type, category, account_id, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (description, amount, date_str, transaction_type, 
                      chart_account_id or None, account_id, notes)).lastrowid
            
            print(f"✅ Transação inserida com ID: {transaction_id}")
            
            # COMMIT (crítico!)
            conn.commit()
            print("💾 COMMIT executado na simulação Flask")
            
            # Verificar persistência
            cursor.execute("SELECT COUNT(*) FROM transactions")
            after_count = cursor.fetchone()[0]
            print(f"📊 Transações depois: {after_count}")
            
            if after_count > before_count:
                print("✅ SIMULAÇÃO PASSOU: Dados persistidos!")
                return True
            else:
                print("❌ SIMULAÇÃO FALHOU: Dados não persistidos!")
                return False
                
        except Exception as e:
            print(f"🚨 ERRO NA SIMULAÇÃO: {e}")
            import traceback
            print(f"📊 Traceback: {traceback.format_exc()}")
            if 'conn' in locals():
                conn.rollback()
                print("🔄 ROLLBACK na simulação")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def analyze_flask_app_issues(self):
        """Analisar possíveis problemas no app Flask"""
        print("\n🔍 ANÁLISE DE PROBLEMAS NO FLASK APP")
        print("=" * 50)
        
        try:
            # Verificar se o banco está sendo usado corretamente
            conn = sqlite3.connect(self.db_path)
            
            # Verificar transações mais recentes
            cursor = conn.cursor()
            cursor.execute("SELECT id, description, amount, type, date FROM transactions ORDER BY id DESC LIMIT 10")
            recent = cursor.fetchall()
            
            print("📊 ÚLTIMAS 10 TRANSAÇÕES NO BANCO:")
            for trans in recent:
                print(f"  ID {trans[0]} | {trans[1][:30]} | R$ {trans[2]} | {trans[3]} | {trans[4]}")
            
            # Verificar se há transações sem commit
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("INSERT INTO transactions (user_id, description, amount, type, date, account_id) VALUES (999, 'TESTE ROLLBACK', 1.0, 'teste', '2025-08-23', 1)")
            print("🔄 Transação de teste inserida (sem commit)")
            
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE user_id = 999")
            test_count = cursor.fetchone()[0]
            print(f"📊 Transações de teste visíveis: {test_count}")
            
            cursor.execute("ROLLBACK")
            print("🔄 ROLLBACK executado")
            
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE user_id = 999")
            test_count_after = cursor.fetchone()[0]
            print(f"📊 Transações de teste após rollback: {test_count_after}")
            
            if test_count > 0 and test_count_after == 0:
                print("✅ Transações funcionam corretamente com commit/rollback")
            else:
                print("⚠️ Possível problema com commit/rollback")
            
        except Exception as e:
            print(f"🚨 ERRO NA ANÁLISE: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def run_all_tests(self):
        """Executar todos os testes"""
        print("🧪 BATERIA COMPLETA DE TESTES DE PERSISTÊNCIA")
        print("=" * 80)
        
        test1_result = self.test_direct_transaction_insert()
        test2_result = self.test_flask_endpoint_simulation()
        
        self.analyze_flask_app_issues()
        
        print(f"\n📊 RESULTADOS FINAIS:")
        print(f"✅ Teste direto no banco: {'PASSOU' if test1_result else 'FALHOU'}")
        print(f"✅ Simulação Flask: {'PASSOU' if test2_result else 'FALHOU'}")
        
        if test1_result and test2_result:
            print("🎉 TODOS OS TESTES PASSARAM - Problema pode estar no frontend/sessão")
        elif test1_result and not test2_result:
            print("⚠️ Problema na lógica do Flask endpoint")
        else:
            print("🚨 Problemas fundamentais de persistência")
        
        print("=" * 80)

if __name__ == '__main__':
    tester = DirectDatabaseTester()
    tester.run_all_tests()
