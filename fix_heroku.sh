#!/bin/bash

# Script para corrigir problemas de deploy no Heroku
# Uso: ./fix_heroku.sh seu-app-name

APP_NAME=${1:-clenio-ai-saas}

echo "🔧 Corrigindo deploy do Heroku para $APP_NAME..."

# 1. Atualizar configuração
echo "⚙️ Atualizando configurações..."
heroku config:set \
    DJANGO_SETTINGS_MODULE=core.settings_heroku_simple \
    DISABLE_COLLECTSTATIC=1 \
    --app $APP_NAME

# 2. Fazer deploy
echo "🚀 Fazendo deploy..."
git push heroku main

# 3. Executar migrações
echo "🗄️ Executando migrações..."
heroku run python manage.py migrate --settings=core.settings_heroku_simple --app $APP_NAME

# 4. Executar setup
echo "⚙️ Executando setup inicial..."
heroku run python scripts/heroku_setup.py --app $APP_NAME

# 5. Coletar arquivos estáticos
echo "📦 Coletando arquivos estáticos..."
heroku run python manage.py collectstatic --noinput --settings=core.settings_heroku_simple --app $APP_NAME

# 6. Reabilitar collectstatic
echo "✅ Reabilitando collectstatic..."
heroku config:unset DISABLE_COLLECTSTATIC --app $APP_NAME

# 7. Verificar status
echo "📊 Verificando status..."
heroku ps --app $APP_NAME

# 8. Abrir aplicação
echo "🌐 Abrindo aplicação..."
heroku open --app $APP_NAME

echo ""
echo "🎉 Correção concluída!"
echo "📋 Se ainda houver problemas, verifique os logs:"
echo "   heroku logs --tail --app $APP_NAME"
