#!/usr/bin/env python
"""
Script de inicialização para Heroku
Cria dados iniciais necessários para o funcionamento do sistema
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_heroku_simple')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

def create_superuser():
    """Criar superusuário se não existir"""
    print("👤 Criando superusuário...")
    
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@arcane-ai.com',
            password='admin123',
            first_name='Admin',
            last_name='Arcane AI'
        )
        print("✅ Superusuário 'admin' criado com senha 'admin123'")
    else:
        print("✅ Superusuário 'admin' já existe")

def create_directories():
    """Criar diretórios necessários"""
    print("📁 Criando diretórios necessários...")
    
    directories = [
        'data',
        'data/faiss_index',
        'logs',
        'media',
        'staticfiles',
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Diretório criado: {directory}")

def main():
    """Função principal"""
    print("🚀 Iniciando setup do Heroku para Arcane AI...")
    
    try:
        create_directories()
        create_superuser()
        
        print("\n🎉 Setup básico concluído com sucesso!")
        print("📋 Resumo:")
        print(f"   - Usuários: {User.objects.count()}")
        print("\n🌐 Acesse a aplicação e faça login com:")
        print("   Username: admin")
        print("   Password: admin123")
        print("\n⚠️ IMPORTANTE: Altere a senha do admin após o primeiro login!")
        
    except Exception as e:
        print(f"❌ Erro durante setup: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
