#!/usr/bin/env python
"""
Script de configuração inicial do projeto Arcane
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_project():
    """Configura o projeto inicial"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()
    
    from django.contrib.auth.models import User
    from rolepermissions.roles import assign_role
    
    print("🚀 Configurando projeto Arcane...")
    
    # Executar migrações
    print("📦 Executando migrações...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Criar superusuário se não existir
    if not User.objects.filter(is_superuser=True).exists():
        print("👤 Criando superusuário...")
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@arcane.com',
            password='admin123'
        )
        print(f"✅ Superusuário criado: {admin_user.username}")
    else:
        print("✅ Superusuário já existe")
    
    # Criar usuário gerente de exemplo
    if not User.objects.filter(username='gerente').exists():
        print("👨‍💼 Criando usuário gerente...")
        gerente_user = User.objects.create_user(
            username='gerente',
            email='gerente@arcane.com',
            password='gerente123'
        )
        assign_role(gerente_user, 'gerente')
        print(f"✅ Usuário gerente criado: {gerente_user.username}")
    else:
        print("✅ Usuário gerente já existe")
    
    print("\n🎉 Configuração concluída!")
    print("\n📋 Credenciais:")
    print("   Admin: admin / admin123")
    print("   Gerente: gerente / gerente123")
    print("\n🌐 Para iniciar o servidor:")
    print("   python manage.py runserver")

if __name__ == '__main__':
    setup_project()
