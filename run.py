# run.py - Arquivo solicitado pelo Render
# Importa e executa o sistema FynanPro ETAPA 4

from app_simple_advanced import app

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
