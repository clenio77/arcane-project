#!/bin/bash

# Script de Deploy Automatizado - Arcane AI SaaS
# Uso: ./deploy.sh [staging|production]

set -e  # Exit on any error

ENVIRONMENT=${1:-staging}
PROJECT_NAME="arcane-ai"
DOCKER_IMAGE="$PROJECT_NAME:latest"

echo "🚀 Iniciando deploy para $ENVIRONMENT..."

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Inicie o Docker e tente novamente."
    exit 1
fi

# Verificar se arquivo .env existe
if [ ! -f ".env.${ENVIRONMENT}" ]; then
    echo "❌ Arquivo .env.${ENVIRONMENT} não encontrado!"
    echo "Crie o arquivo com as variáveis de ambiente necessárias."
    exit 1
fi

# Copiar arquivo de ambiente
cp ".env.${ENVIRONMENT}" .env

echo "📦 Construindo imagem Docker..."
docker build -t $DOCKER_IMAGE .

echo "🧪 Executando testes..."
docker run --rm \
    --env-file .env \
    -v $(pwd):/app \
    $DOCKER_IMAGE \
    python manage.py test --settings=core.settings_production

echo "✅ Testes passaram!"

if [ "$ENVIRONMENT" = "production" ]; then
    echo "🔍 Verificações de segurança para produção..."
    
    # Verificar se DEBUG está False
    if grep -q "DEBUG=True" .env; then
        echo "❌ DEBUG=True detectado em produção! Altere para DEBUG=False"
        exit 1
    fi
    
    # Verificar se SECRET_KEY está definida
    if ! grep -q "SECRET_KEY=" .env; then
        echo "❌ SECRET_KEY não definida!"
        exit 1
    fi
    
    echo "✅ Verificações de segurança passaram!"
fi

echo "🗄️ Executando migrações..."
docker run --rm \
    --env-file .env \
    -v $(pwd)/data:/app/data \
    $DOCKER_IMAGE \
    python manage.py migrate --settings=core.settings_production

echo "📊 Coletando arquivos estáticos..."
docker run --rm \
    --env-file .env \
    -v $(pwd)/staticfiles:/app/staticfiles \
    $DOCKER_IMAGE \
    python manage.py collectstatic --noinput --settings=core.settings_production

if [ "$ENVIRONMENT" = "production" ]; then
    echo "🏷️ Criando tag de versão..."
    VERSION=$(date +%Y%m%d-%H%M%S)
    docker tag $DOCKER_IMAGE "$PROJECT_NAME:$VERSION"
    
    echo "📤 Fazendo push para registry..."
    # Configurar seu registry aqui (Docker Hub, AWS ECR, etc.)
    # docker push "$PROJECT_NAME:$VERSION"
    # docker push $DOCKER_IMAGE
fi

echo "🚀 Iniciando aplicação..."

# Parar containers existentes
docker-compose -f docker-compose.${ENVIRONMENT}.yml down || true

# Iniciar novos containers
docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d

echo "⏳ Aguardando aplicação ficar pronta..."
sleep 10

# Health check
HEALTH_URL="http://localhost:8000/health/"
if [ "$ENVIRONMENT" = "production" ]; then
    HEALTH_URL="https://arcane-ai.com/health/"
fi

for i in {1..30}; do
    if curl -f $HEALTH_URL > /dev/null 2>&1; then
        echo "✅ Aplicação está rodando!"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "❌ Aplicação não respondeu após 30 tentativas"
        echo "📋 Logs dos containers:"
        docker-compose -f docker-compose.${ENVIRONMENT}.yml logs --tail=50
        exit 1
    fi
    
    echo "⏳ Tentativa $i/30..."
    sleep 2
done

echo "🎉 Deploy concluído com sucesso!"
echo "🌐 Aplicação disponível em: $HEALTH_URL"

if [ "$ENVIRONMENT" = "production" ]; then
    echo "📧 Enviando notificação de deploy..."
    # Implementar notificação (Slack, email, etc.)
    
    echo "📊 Métricas pós-deploy:"
    echo "- Versão: $VERSION"
    echo "- Timestamp: $(date)"
    echo "- Environment: $ENVIRONMENT"
fi

echo "✨ Deploy finalizado!"
