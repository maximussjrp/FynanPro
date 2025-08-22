# run.py - Arquivo solicitado pelo Render com logging avançado
# Sistema FynanPro ETAPA 4 - Diagnóstico profissional

import os
import sys
import logging
from datetime import datetime

# Configuração de logging profissional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)

def setup_database_diagnostics():
    """Diagnóstico avançado do banco de dados"""
    try:
        import sqlite3
        
        # Verificar se banco existe
        db_path = 'finance_planner_saas.db'
        if not os.path.exists(db_path):
            logger.warning(f"⚠️ Banco {db_path} não existe - será criado")
            return False
            
        # Verificar estrutura das tabelas
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tabelas críticas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        critical_tables = ['users', 'accounts', 'transactions', 'categories', 'budgets', 'goals', 'goal_contributions']
        
        for table in critical_tables:
            if table in tables:
                logger.info(f"✅ Tabela {table} - OK")
                # Verificar estrutura da tabela users especificamente
                if table == 'users':
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [row[1] for row in cursor.fetchall()]
                    logger.info(f"📋 Colunas users: {columns}")
            else:
                logger.error(f"❌ Tabela {table} - MISSING")
                
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no diagnóstico do banco: {e}")
        return False

def main():
    """Função principal com diagnóstico completo"""
    try:
        logger.info("🚀 INICIANDO FYNANPRO - ETAPA 4 COMPLETA")
        logger.info(f"📍 Python: {sys.version}")
        logger.info(f"📁 Diretório: {os.getcwd()}")
        logger.info(f"🌐 PORT: {os.environ.get('PORT', 'Não configurado')}")
        logger.info(f"🔑 SECRET_KEY: {'✅ OK' if os.environ.get('SECRET_KEY') else '❌ Missing'}")
        
        # Listar arquivos disponíveis
        files = os.listdir('.')
        logger.info(f"📂 Arquivos: {[f for f in files if f.endswith(('.py', '.db', '.txt', '.yaml'))]}")
        
        # Diagnóstico do banco
        logger.info("🔍 DIAGNÓSTICO DO BANCO DE DADOS:")
        db_ok = setup_database_diagnostics()
        
        # Importar aplicação
        logger.info("📦 Importando app_simple_advanced...")
        from app_simple_advanced import app
        logger.info("✅ Aplicação importada com sucesso!")
        
        # Configurar Flask para produção com logs detalhados
        app.config['ENV'] = 'production'
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        app.config['PROPAGATE_EXCEPTIONS'] = True
        
        # Handler de erro personalizado
        @app.errorhandler(Exception)
        def handle_exception(e):
            logger.error(f"🚨 ERRO NA APLICAÇÃO: {str(e)}")
            import traceback
            logger.error(f"📊 Traceback completo: {traceback.format_exc()}")
            return f"Erro interno detectado. Verifique os logs para detalhes. Erro: {str(e)}", 500
            
        # Rota de teste de saúde
        @app.route('/health')
        def health_check():
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'ok' if db_ok else 'error',
                'version': 'ETAPA 4'
            }
        
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"🌐 Iniciando servidor na porta {port}")
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False
        )
        
    except ImportError as e:
        logger.error(f"❌ Erro de importação: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        import traceback
        logger.error(f"📊 Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == '__main__':
    main()
