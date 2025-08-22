# Arquivo principal para producao - ETAPA 4 - Sistema de Orcamentos e Metas
# Importa e executa o app_simple_advanced.py que contem toda a implementacao da ETAPA 4

from app_simple_advanced import app

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
