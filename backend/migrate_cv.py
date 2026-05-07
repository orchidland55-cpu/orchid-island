# migrate_cv.py — Script pour nettoyer les anciennes URLs Railway invalides
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orchid_backend.settings')
django.setup()

from users.models import CustomUser

print("🔧 Début de la migration des CVs...")

users = CustomUser.objects.filter(role='stagiaire').exclude(cv_url__isnull=True).exclude(cv_url='')

for user in users:
    # Si l'URL est encore une URL Railway (locale), ignorer
    # Si c'est déjà une URL Cloudinary, ignorer
    if user.cv_url and 'cloudinary.com' not in user.cv_url:
        print(f'[SKIP] {user.email} — URL non-Cloudinary: {user.cv_url}')
        # Vider l'URL invalide
        user.cv_url = None
        user.cv_name = None
        user.cv_public_id = None
        user.save()
        print(f'[CLEAR] {user.email} — URL invalide supprimée')
    elif user.cv_url and 'cloudinary.com' in user.cv_url:
        print(f'[OK] {user.email} — déjà sur Cloudinary')

print("✅ Migration terminée.")
