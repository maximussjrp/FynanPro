#!/bin/bash
# Script de verificação pré-deploy para Render.com
echo "🔍 Verificando versão do app.py..."

if grep -q "ZERO_SQLALCHEMY_DEFINITIVA_21AGO2025" app.py; then
    echo "✅ Versão ZERO SQLAlchemy CORRETA detectada!"
    echo "🚀 Iniciando FynanPro..."
else
    echo "❌ ERRO: Versão incorreta do app.py!"
    exit 1
fi

# Verificar se não há SQLAlchemy no código
if grep -q "from sqlalchemy" app.py; then
    echo "❌ ERRO: SQLAlchemy encontrado no código!"
    exit 1
else
    echo "✅ Código ZERO SQLAlchemy confirmado!"
fi

echo "🎯 Deploy CORRETO - Prosseguindo..."
