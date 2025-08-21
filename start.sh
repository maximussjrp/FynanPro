#!/bin/bash
# Start script para Render.com

echo "🚀 Iniciando FynanPro..."

# Tentar com gunicorn primeiro
if command -v gunicorn &> /dev/null; then
    echo "✅ Usando Gunicorn..."
    exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app:app --preload
else
    echo "⚠️  Gunicorn não encontrado, usando Flask development server..."
    exec python app.py
fi
