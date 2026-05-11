#!/usr/bin/env python
"""
Script pour créer les comptes Manager et RH par défaut
Exécutez avec: python manage.py shell < create_manager_rh_accounts.py
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orchid_backend.settings')
django.setup()

from users.models import CustomUser

def create_accounts():
    """Créer les comptes Manager et RH par défaut"""
    
    # Compte RH
    rh_email = 'rh@orchid-island.com'
    rh_password = 'Rh123456!'
    
    # Vérifier si le compte RH existe déjà
    if CustomUser.objects.filter(email=rh_email).exists():
        print(f"✅ Le compte RH existe déjà: {rh_email}")
    else:
        rh_user = CustomUser.objects.create_user(
            username=rh_email,
            email=rh_email,
            password=rh_password,
            first_name='Ressources',
            last_name='Humaines',
            role='rh',
            is_active=True,
            phone='+212600000000',
            ecole='Orchid Island',
            formation='Management RH',
            departement='Ressources Humaines'
        )
        print(f"✅ Compte RH créé: {rh_email}")
        print(f"   Mot de passe: {rh_password}")
    
    # Compte Manager
    manager_email = 'manager@orchid-island.com'
    manager_password = 'Manager123456!'
    
    # Vérifier si le compte Manager existe déjà
    if CustomUser.objects.filter(email=manager_email).exists():
        print(f"✅ Le compte Manager existe déjà: {manager_email}")
    else:
        manager_user = CustomUser.objects.create_user(
            username=manager_email,
            email=manager_email,
            password=manager_password,
            first_name='Project',
            last_name='Manager',
            role='manager',
            is_active=True,
            phone='+212610000000',
            ecole='Orchid Island',
            formation='Project Management',
            departement='Projets'
        )
        print(f"✅ Compte Manager créé: {manager_email}")
        print(f"   Mot de passe: {manager_password}")
    
    print("\n📋 Résumé des comptes créés:")
    print("=" * 50)
    print(f"RH:       {rh_email}      | Mot de passe: {rh_password}")
    print(f"Manager:  {manager_email} | Mot de passe: {manager_password}")
    print("=" * 50)
    print("\n🔐 Les comptes sont maintenant utilisables!")
    
    # Afficher tous les utilisateurs existants
    print("\n👥 Liste complète des utilisateurs:")
    users = CustomUser.objects.all()
    for user in users:
        status = "✅ Actif" if user.is_active else "❌ Bloqué"
        print(f"  • {user.email} ({user.role}) - {status}")

if __name__ == '__main__':
    create_accounts()
