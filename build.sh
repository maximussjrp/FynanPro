#!/bin/bash
# Build script para Render.com

echo "🔧 Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build concluído!"
