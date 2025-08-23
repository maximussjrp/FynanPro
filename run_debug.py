#!/usr/bin/env python3
"""
DEBUG ESPECÍFICO PARA PRODUÇÃO RENDER.COM
Diagnóstico completo de startup para identificar erro 502
"""
import os
import sys
import logging
import traceback
from datetime import datetime

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)

def test_step(step_name, test_func):
    """Execute um passo de teste e registre resultado"""
    logger.info(f"🔍 TESTE: {step_name}")
    try:
        result = test_func()
        logger.info(f"✅ SUCESSO: {step_name} - {result}")
        return True, result
    except Exception as e:
        logger.error(f"❌ ERRO: {step_name} - {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False, str(e)

def main():
    logger.info("🚀 INICIANDO DIAGNÓSTICO COMPLETO DE PRODUÇÃO")
    logger.info(f"🕒 Timestamp: {datetime.now()}")
    logger.info(f"🐍 Python: {sys.version}")
    logger.info(f"📂 Working Dir: {os.getcwd()}")
    logger.info(f"🌍 Environment Variables:")
    
    # Mostrar variáveis importantes (mascarar secrets)
    for key in ['PORT', 'DATABASE_URL', 'DB_PATH', 'SECRET_KEY']:
        value = os.getenv(key, 'NOT SET')
        if 'SECRET' in key and value != 'NOT SET':
            value = f"{value[:8]}..."
        logger.info(f"   {key} = {value}")
    
    # TESTE 1: Importações básicas
    success, _ = test_step("Importações Python básicas", lambda: "OK")
    if not success:
        return False
    
    # TESTE 2: Sistema de migrações
    def test_migrations_import():
        from migrations import run_all_migrations
        return "Migrations importado"
    
    success, _ = test_step("Import sistema de migrações", test_migrations_import)
    if not success:
        return False
    
    # TESTE 3: Executar migrações
    def test_run_migrations():
        from migrations import run_all_migrations
        result = run_all_migrations()
        return f"Migrações executadas: {result}"
    
    success, _ = test_step("Execução das migrações", test_run_migrations)
    if not success:
        logger.critical("💥 FALHA CRÍTICA: Migrações falharam - sistema não pode continuar")
        return False
    
    # TESTE 4: Import da aplicação Flask
    def test_app_import():
        from app_simple_advanced import app
        return f"Flask app: {app}"
    
    success, app_result = test_step("Import aplicação Flask", test_app_import)
    if not success:
        logger.critical("💥 FALHA CRÍTICA: Não conseguiu importar app Flask")
        return False
    
    # TESTE 5: Configuração SECRET_KEY
    def test_secret_key():
        from app_simple_advanced import app
        import secrets
        sk = os.getenv("SECRET_KEY")
        if not sk:
            sk = secrets.token_hex(32)
            logger.warning("SECRET_KEY ausente. Gerando chave efêmera.")
        app.config["SECRET_KEY"] = sk
        return f"SECRET_KEY configurado: {len(sk)} chars"
    
    success, _ = test_step("Configuração SECRET_KEY", test_secret_key)
    if not success:
        return False
    
    # TESTE 6: Registro rota /healthz
    def test_health_route():
        from app_simple_advanced import app
        
        if "health_check" not in app.view_functions:
            @app.route("/healthz", endpoint="health_check")
            def health_check():
                return {"status": "ok", "timestamp": datetime.now().isoformat()}, 200
            return "Rota /healthz registrada"
        else:
            return "Rota health_check já existe"
    
    success, _ = test_step("Registro rota /healthz", test_health_route)
    if not success:
        return False
    
    # TESTE 7: Preparação do servidor
    def test_server_prep():
        port = int(os.getenv("PORT", "10000"))
        return f"Porta configurada: {port}"
    
    success, port_info = test_step("Preparação servidor", test_server_prep)
    if not success:
        return False
    
    # TESTE 8: Iniciar servidor
    logger.info("🚀 TODOS OS TESTES PASSARAM - INICIANDO SERVIDOR")
    
    try:
        from app_simple_advanced import app
        port = int(os.getenv("PORT", "10000"))
        
        logger.info(f"🌐 Iniciando servidor na porta {port}")
        logger.info("✅ Sistema pronto para receber requisições")
        
        # Usar modo não-debug em produção para evitar reloader
        app.run(
            host="0.0.0.0", 
            port=port, 
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except Exception as e:
        logger.critical(f"💥 ERRO FATAL NO STARTUP DO SERVIDOR: {e}")
        logger.critical(f"Traceback completo: {traceback.format_exc()}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            logger.critical("💥 DIAGNÓSTICO FALHOU - SISTEMA NÃO PODE INICIAR")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"💥 ERRO FATAL NO DIAGNÓSTICO: {e}")
        logger.critical(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
