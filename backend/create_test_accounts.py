#!/usr/bin/env python
import os
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orchid_backend.settings')
django.setup()

from users.models import CustomUser
from django.contrib.auth.hashers import make_password

def create_test_accounts():
    """Créer les comptes de test pour chaque rôle"""
    
    roles_data = [
        {
            'email': 'admin@orchid-island.com', 
            'first_name': 'Admin', 
            'last_name': 'Orchid', 
            'role': 'admin', 
            'password': 'Wacwac199'
        },
        {
            'email': 'manager@orchid-island.com', 
            'first_name': 'Manager', 
            'last_name': 'Projet', 
            'role': 'manager', 
            'password': 'manager123'
        },
        {
            'email': 'rh@orchid-island.com', 
            'first_name': 'RH', 
            'last_name': 'Service', 
            'role': 'rh', 
            'password': 'rh123'
        },
        {
            'email': 'stagiaire@orchid-island.com', 
            'first_name': 'Stagiaire', 
            'last_name': 'Test', 
            'role': 'stagiaire', 
            'password': 'stagiaire123'
        },
    ]

    print("🔧 Création des comptes de test...")
    print("=" * 50)
    
    for data in roles_data:
        user, created = CustomUser.objects.get_or_create(
            email=data['email'],
            defaults={
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'role': data['role'],
                'password': make_password(data['password'])
            }
        )
        
        if created:
            print(f"✅ Compte créé: {data['email']}")
            print(f"   Rôle: {data['role'].upper()}")
            print(f"   Mot de passe: {data['password']}")
        else:
            print(f"ℹ️  Compte existe déjà: {data['email']}")
            print(f"   Rôle: {data['role'].upper()}")
        print("-" * 30)
    
    print("=" * 50)
    print("🎉 Comptes de test créés avec succès!")
    print("\n📋 Identifiants de connexion:")
    print("👑 Admin: admin@orchid-island.com / Wacwac199")
    print("👤 Manager: manager@orchid-island.com / manager123")
    print("🛠️ RH: rh@orchid-island.com / rh123")
    print("🎓 Stagiaire: stagiaire@orchid-island.com / stagiaire123")

if __name__ == '__main__':
    create_test_accounts()
