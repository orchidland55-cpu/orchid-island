#!/usr/bin/env python
import os
import sys

# Ajouter le chemin du projet
sys.path.append('/Users/mac/Documents/orchid-island/backend')

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orchid_backend.settings')

import django
django.setup()

from users.models import CustomUser
from django.contrib.auth.hashers import make_password

def create_test_users():
    """Créer les 4 comptes de test"""
    
    # Supprimer les utilisateurs existants pour éviter les doublons
    CustomUser.objects.all().delete()
    
    # Données des 4 comptes
    users_data = [
        {
            'email': 'admin@orchid-island.com',
            'username': 'admin',
            'first_name': 'Admin',
            'last_name': 'Orchid',
            'role': 'admin',
            'password': 'Wacwac199'
        },
        {
            'email': 'manager@orchid-island.com',
            'username': 'manager',
            'first_name': 'Manager',
            'last_name': 'Projet',
            'role': 'manager',
            'password': 'manager123'
        },
        {
            'email': 'rh@orchid-island.com',
            'username': 'rh',
            'first_name': 'RH',
            'last_name': 'Service',
            'role': 'rh',
            'password': 'rh123'
        },
        {
            'email': 'stagiaire@orchid-island.com',
            'username': 'stagiaire',
            'first_name': 'Stagiaire',
            'last_name': 'Test',
            'role': 'stagiaire',
            'password': 'stagiaire123'
        }
    ]
    
    print("🔧 Création des 4 comptes de test...")
    print("=" * 60)
    
    for user_data in users_data:
        try:
            user = CustomUser.objects.create(
                email=user_data['email'],
                username=user_data['username'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role'],
                password=make_password(user_data['password'])
            )
            print(f"✅ Compte créé avec succès:")
            print(f"   Email: {user_data['email']}")
            print(f"   Username: {user_data['username']}")
            print(f"   Nom: {user_data['first_name']} {user_data['last_name']}")
            print(f"   Rôle: {user_data['role'].upper()}")
            print(f"   Mot de passe: {user_data['password']}")
            print("-" * 40)
        except Exception as e:
            print(f"❌ Erreur lors de la création du compte {user_data['email']}: {e}")
    
    print("=" * 60)
    print("🎉 Opération terminée!")
    print("\n📋 IDENTIFIANTS POUR TESTS:")
    print("👑 ADMIN: admin@orchid-island.com / Wacwac199")
    print("👤 MANAGER: manager@orchid-island.com / manager123")
    print("🛠️ RH: rh@orchid-island.com / rh123")
    print("🎓 STAGIAIRE: stagiaire@orchid-island.com / stagiaire123")

if __name__ == '__main__':
    create_test_users()
