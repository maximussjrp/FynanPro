"""
WSGI entry point for production deployment
"""
import os
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO)

# Executar migrações
try:
    from migrations import run_all_migrations
    logging.info("Executando migrações...")
    ok = run_all_migrations()
    if not ok:
        raise RuntimeError("Erro nas migrações")
except Exception as e:
    logging.error(f"Erro crítico nas migrações: {e}")
    raise

# Importar app
try:
    from app_simple_advanced import app
    logging.info("App importado com sucesso")
except Exception as e:
    logging.error(f"Erro ao importar app: {e}")
    raise

# Configurar SECRET_KEY
import secrets
sk = os.getenv("SECRET_KEY")
if not sk:
    sk = secrets.token_hex(32)
    logging.warning("Gerando SECRET_KEY temporário")
app.config["SECRET_KEY"] = sk

# Health check
if "health_check" not in app.view_functions:
    @app.route("/healthz", endpoint="health_check")
    def health_check():
        return {"status": "ok"}, 200

logging.info("WSGI app pronto para produção")

# Esta é a variável que o Gunicorn procura
application = app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
