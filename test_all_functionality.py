#!/usr/bin/env python3
"""
Script de teste completo para verificar todas as funcionalidades do sistema FynanPro
Executa testes automatizados em todas as rotas e funcionalidades principais
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os

# Configurações do teste
BASE_URL = "http://127.0.0.1:5000"
TEST_USER = {
    "email": "teste@fynanpro.com",
    "password": "123456",
    "name": "Usuário Teste"
}

class FynanProTester:
    def __init__(self):
        self.session = requests.Session()
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
    
    def test_route(self, route, method="GET", data=None, expected_status=200, description=""):
        """Testa uma rota específica"""
        try:
            self.results["total_tests"] += 1
            url = f"{BASE_URL}{route}"
            
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, data=data)
            elif method == "DELETE":
                response = self.session.delete(url)
            
            if response.status_code == expected_status:
                self.log(f"✅ {method} {route} - {description}", "PASS")
                self.results["passed"] += 1
                return True, response
            else:
                self.log(f"❌ {method} {route} - Status: {response.status_code} (esperado: {expected_status}) - {description}", "FAIL")
                self.results["failed"] += 1
                self.results["errors"].append(f"{method} {route}: Status {response.status_code}")
                return False, response
        
        except Exception as e:
            self.log(f"❌ {method} {route} - Erro: {str(e)} - {description}", "ERROR")
            self.results["failed"] += 1
            self.results["errors"].append(f"{method} {route}: {str(e)}")
            return False, None
    
    def test_authentication(self):
        """Testa sistema de autenticação"""
        self.log("=== TESTANDO AUTENTICAÇÃO ===")
        
        # Teste da página de login
        self.test_route("/login", description="Página de login")
        
        # Teste da página de registro
        self.test_route("/register", description="Página de registro")
        
        # Teste de registro de usuário
        register_data = {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"],
            "confirm_password": TEST_USER["password"],
            "name": TEST_USER["name"]
        }
        success, response = self.test_route("/register", "POST", register_data, 
                                          expected_status=302, description="Registro de usuário")
        
        # Teste de login
        login_data = {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
        success, response = self.test_route("/login", "POST", login_data, 
                                          expected_status=302, description="Login de usuário")
        
        return success
    
    def test_main_pages(self):
        """Testa páginas principais do sistema"""
        self.log("=== TESTANDO PÁGINAS PRINCIPAIS ===")
        
        pages = [
            ("/", "Página inicial/Dashboard"),
            ("/financial_health", "Saúde Financeira"),
            ("/transactions", "Lista de Transações"),
            ("/add_transaction", "Adicionar Transação"),
            ("/categories", "Categorias"),
            ("/add_category", "Adicionar Categoria"),
            ("/indicators", "Indicadores"),
            ("/profile", "Perfil do usuário"),
            ("/search", "Busca"),
            ("/pricing", "Preços"),
            ("/support", "Suporte")
        ]
        
        for route, description in pages:
            self.test_route(route, description=description)
    
    def test_admin_pages(self):
        """Testa páginas administrativas"""
        self.log("=== TESTANDO PÁGINAS ADMINISTRATIVAS ===")
        
        admin_pages = [
            ("/admin", "Dashboard Admin"),
            ("/admin/users", "Gerenciar Usuários"),
            ("/admin/analytics", "Analytics"),
            ("/admin/support-agents", "Agentes de Suporte"),
            ("/admin/quick-replies", "Respostas Rápidas"),
            ("/admin/chat", "Chat Admin")
        ]
        
        for route, description in admin_pages:
            # Admin pages may require special permissions, so we expect 302 redirect or 403
            self.test_route(route, expected_status=[200, 302, 403], description=description)
    
    def test_support_system(self):
        """Testa sistema de suporte"""
        self.log("=== TESTANDO SISTEMA DE SUPORTE ===")
        
        support_pages = [
            ("/suporte", "Portal de Suporte"),
            ("/suporte/login", "Login Suporte"),
            ("/suporte/dashboard", "Dashboard Suporte")
        ]
        
        for route, description in support_pages:
            self.test_route(route, description=description)
    
    def test_api_endpoints(self):
        """Testa endpoints da API"""
        self.log("=== TESTANDO ENDPOINTS DA API ===")
        
        # Teste de chat API
        chat_data = {
            "message": "Teste de mensagem"
        }
        self.test_route("/api/chat/send", "POST", chat_data, 
                       expected_status=[200, 302, 401], description="Enviar mensagem chat")
        
        self.test_route("/api/chat/messages", description="Listar mensagens chat")
    
    def test_user_profile_functions(self):
        """Testa funcionalidades do perfil do usuário"""
        self.log("=== TESTANDO FUNCIONALIDADES DE PERFIL ===")
        
        profile_pages = [
            ("/profile/edit", "Editar Perfil"),
            ("/profile/change_password", "Alterar Senha")
        ]
        
        for route, description in profile_pages:
            self.test_route(route, description=description)
    
    def test_payment_system(self):
        """Testa sistema de pagamentos"""
        self.log("=== TESTANDO SISTEMA DE PAGAMENTOS ===")
        
        payment_routes = [
            ("/select_plan/monthly", "Selecionar Plano Mensal"),
            ("/payment/monthly", "Página de Pagamento Mensal"),
            ("/payment/success/monthly", "Página de Sucesso"),
            ("/payment/cancel", "Cancelar Pagamento")
        ]
        
        for route, description in payment_routes:
            self.test_route(route, expected_status=[200, 302], description=description)
    
    def test_crud_operations(self):
        """Testa operações CRUD básicas"""
        self.log("=== TESTANDO OPERAÇÕES CRUD ===")
        
        # Teste de adicionar categoria
        category_data = {
            "name": "Categoria Teste",
            "description": "Categoria para testes",
            "color": "#FF0000"
        }
        self.test_route("/add_category", "POST", category_data, 
                       expected_status=[200, 302], description="Criar categoria")
        
        # Teste de adicionar transação
        transaction_data = {
            "description": "Transação Teste",
            "amount": "100.00",
            "type": "income",
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        self.test_route("/add_transaction", "POST", transaction_data, 
                       expected_status=[200, 302], description="Criar transação")
    
    def test_server_connectivity(self):
        """Testa conectividade com o servidor"""
        self.log("=== TESTANDO CONECTIVIDADE DO SERVIDOR ===")
        
        try:
            response = requests.get(BASE_URL, timeout=5)
            if response.status_code in [200, 302]:
                self.log("✅ Servidor está respondendo", "PASS")
                return True
            else:
                self.log(f"❌ Servidor retornou status {response.status_code}", "FAIL")
                return False
        except requests.exceptions.ConnectionError:
            self.log("❌ Não foi possível conectar ao servidor", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Erro de conectividade: {str(e)}", "ERROR")
            return False
    
    def generate_report(self):
        """Gera relatório final dos testes"""
        self.log("\n" + "="*60)
        self.log("RELATÓRIO FINAL DE TESTES")
        self.log("="*60)
        
        success_rate = (self.results["passed"] / self.results["total_tests"] * 100) if self.results["total_tests"] > 0 else 0
        
        print(f"📊 Total de testes executados: {self.results['total_tests']}")
        print(f"✅ Testes aprovados: {self.results['passed']}")
        print(f"❌ Testes falharam: {self.results['failed']}")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        
        if self.results["errors"]:
            print(f"\n🚨 Erros encontrados ({len(self.results['errors'])}):")
            for i, error in enumerate(self.results["errors"], 1):
                print(f"   {i}. {error}")
        
        print("\n" + "="*60)
        
        # Status final
        if success_rate >= 80:
            self.log("🎉 SISTEMA FUNCIONANDO ADEQUADAMENTE", "SUCCESS")
        elif success_rate >= 60:
            self.log("⚠️ SISTEMA COM ALGUNS PROBLEMAS", "WARNING") 
        else:
            self.log("🚨 SISTEMA COM MUITOS PROBLEMAS", "CRITICAL")
    
    def run_all_tests(self):
        """Executa todos os testes"""
        self.log("🚀 INICIANDO TESTES COMPLETOS DO FYNANPRO")
        self.log("="*60)
        
        start_time = time.time()
        
        # Verificar conectividade primeiro
        if not self.test_server_connectivity():
            self.log("❌ Servidor não está acessível. Abortando testes.", "ERROR")
            return
        
        # Executar todos os testes
        try:
            self.test_authentication()
            self.test_main_pages()
            self.test_admin_pages()
            self.test_support_system()
            self.test_api_endpoints()
            self.test_user_profile_functions()
            self.test_payment_system()
            self.test_crud_operations()
            
        except KeyboardInterrupt:
            self.log("❌ Testes interrompidos pelo usuário", "WARNING")
        except Exception as e:
            self.log(f"❌ Erro durante execução dos testes: {str(e)}", "ERROR")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.log(f"⏱️ Tempo total de execução: {execution_time:.2f} segundos")
        
        # Gerar relatório final
        self.generate_report()

if __name__ == "__main__":
    print("🔧 FynanPro - Sistema de Testes Automatizados")
    print("=" * 50)
    
    tester = FynanProTester()
    tester.run_all_tests()
    
    # Aguardar entrada do usuário antes de sair
    input("\n📋 Pressione ENTER para finalizar...")
