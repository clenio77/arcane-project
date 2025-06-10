#!/bin/bash

# Script de Deploy Automatizado para Heroku - Arcane AI
# Uso: ./deploy_heroku.sh

set -e  # Exit on any error

APP_NAME="arcane-ai-saas"
REGION="us"

echo "🚀 Iniciando deploy do Arcane AI no Heroku..."

# Verificar se Heroku CLI está instalado
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI não encontrado!"
    echo "Instale em: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Login no Heroku (se necessário)
echo "🔐 Verificando login no Heroku..."
if ! heroku auth:whoami &> /dev/null; then
    echo "Faça login no Heroku:"
    heroku login
fi

# Criar aplicação no Heroku
echo "📱 Criando aplicação no Heroku..."
if heroku apps:info $APP_NAME &> /dev/null; then
    echo "✅ App $APP_NAME já existe"
else
    heroku create $APP_NAME --region $REGION
    echo "✅ App $APP_NAME criado"
fi

# Adicionar addons necessários
echo "🔧 Configurando addons..."

# PostgreSQL
if heroku addons:info postgresql --app $APP_NAME &> /dev/null; then
    echo "✅ PostgreSQL já configurado"
else
    heroku addons:create heroku-postgresql:essential-0 --app $APP_NAME
    echo "✅ PostgreSQL adicionado"
fi

# Redis
if heroku addons:info redis --app $APP_NAME &> /dev/null; then
    echo "✅ Redis já configurado"
else
    heroku addons:create heroku-redis:mini --app $APP_NAME
    echo "✅ Redis adicionado"
fi

# SendGrid (opcional)
if heroku addons:info sendgrid --app $APP_NAME &> /dev/null; then
    echo "✅ SendGrid já configurado"
else
    heroku addons:create sendgrid:starter --app $APP_NAME || echo "⚠️ SendGrid não adicionado (opcional)"
fi

# Configurar variáveis de ambiente
echo "⚙️ Configurando variáveis de ambiente..."

heroku config:set \
    DJANGO_SETTINGS_MODULE=core.settings_heroku \
    DEBUG=False \
    DOMAIN_NAME=$APP_NAME.herokuapp.com \
    DEFAULT_FROM_EMAIL=noreply@$APP_NAME.herokuapp.com \
    FAISS_DIMENSION=1536 \
    --app $APP_NAME

# Solicitar chave OpenAI
echo ""
echo "🔑 CONFIGURAÇÃO NECESSÁRIA:"
echo "Você precisa configurar sua chave da OpenAI:"
echo ""
echo "1. Acesse: https://platform.openai.com/api-keys"
echo "2. Crie uma nova chave API"
echo "3. Execute: heroku config:set OPENAI_API_KEY=sua_chave_aqui --app $APP_NAME"
echo ""
read -p "Pressione Enter quando tiver configurado a chave OpenAI..."

# Verificar se OpenAI key foi configurada
if heroku config:get OPENAI_API_KEY --app $APP_NAME | grep -q "sk-"; then
    echo "✅ Chave OpenAI configurada"
else
    echo "❌ Chave OpenAI não configurada!"
    echo "Execute: heroku config:set OPENAI_API_KEY=sua_chave_aqui --app $APP_NAME"
    exit 1
fi

# Configurar Stripe (opcional)
echo ""
echo "💳 CONFIGURAÇÃO STRIPE (Opcional):"
echo "Para habilitar pagamentos, configure as chaves do Stripe:"
echo ""
echo "1. Acesse: https://dashboard.stripe.com/apikeys"
echo "2. Copie as chaves (test ou live)"
echo "3. Execute os comandos:"
echo "   heroku config:set STRIPE_PUBLIC_KEY=pk_... --app $APP_NAME"
echo "   heroku config:set STRIPE_SECRET_KEY=sk_... --app $APP_NAME"
echo ""
read -p "Configurar Stripe agora? (y/n): " configure_stripe

if [[ $configure_stripe =~ ^[Yy]$ ]]; then
    echo "Digite sua chave pública do Stripe (pk_...):"
    read stripe_public_key
    echo "Digite sua chave secreta do Stripe (sk_...):"
    read stripe_secret_key
    
    heroku config:set \
        STRIPE_PUBLIC_KEY=$stripe_public_key \
        STRIPE_SECRET_KEY=$stripe_secret_key \
        --app $APP_NAME
    
    echo "✅ Stripe configurado"
fi

# Configurar git remote
echo "🔗 Configurando git remote..."
if git remote | grep -q heroku; then
    git remote remove heroku
fi
heroku git:remote -a $APP_NAME

# Deploy da aplicação
echo "🚀 Fazendo deploy..."
git push heroku main

# Executar migrações
echo "🗄️ Executando migrações..."
heroku run python manage.py migrate --app $APP_NAME

# Executar setup inicial
echo "⚙️ Executando setup inicial..."
heroku run python scripts/heroku_setup.py --app $APP_NAME

# Coletar arquivos estáticos
echo "📦 Coletando arquivos estáticos..."
heroku run python manage.py collectstatic --noinput --app $APP_NAME

# Configurar worker (Celery)
echo "👷 Configurando workers..."
heroku ps:scale worker=1 --app $APP_NAME

# Abrir aplicação
echo "🌐 Abrindo aplicação..."
heroku open --app $APP_NAME

echo ""
echo "🎉 Deploy concluído com sucesso!"
echo ""
echo "📋 INFORMAÇÕES DA APLICAÇÃO:"
echo "   🌐 URL: https://$APP_NAME.herokuapp.com"
echo "   📊 Dashboard: https://dashboard.heroku.com/apps/$APP_NAME"
echo "   📝 Logs: heroku logs --tail --app $APP_NAME"
echo ""
echo "🔐 CREDENCIAIS DE ADMIN:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "⚙️ COMANDOS ÚTEIS:"
echo "   heroku logs --tail --app $APP_NAME"
echo "   heroku run python manage.py shell --app $APP_NAME"
echo "   heroku run python manage.py createsuperuser --app $APP_NAME"
echo "   heroku config --app $APP_NAME"
echo ""
echo "🎯 PRÓXIMOS PASSOS:"
echo "   1. Acesse a aplicação e teste o login"
echo "   2. Configure domínio customizado (opcional)"
echo "   3. Configure SSL customizado (opcional)"
echo "   4. Configure monitoramento (Sentry)"
echo "   5. Configure backup automático"
echo ""
echo "✨ Sua plataforma de IA está no ar!"
