# fix_rapports.py — Script pour rendre publics les fichiers Cloudinary existants
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orchid_backend.settings')
django.setup()

import cloudinary
import cloudinary.uploader
from rapports.models import Rapport

print("🔧 Début de la mise à jour des fichiers Cloudinary...")

rapports = Rapport.objects.filter(fichier_public_id__isnull=False).exclude(fichier_public_id='')

for r in rapports:
    if not r.fichier_public_id:
        continue
    try:
        # ✅ Changer l'access_control du fichier existant
        result = cloudinary.uploader.explicit(
            r.fichier_public_id,
            type='upload',
            resource_type='raw',
            access_control=[{"access_type": "anonymous"}],
        )
        new_url = result.get('secure_url')
        if new_url:
            r.fichier_url = new_url
            r.save()
            print(f"✅ {r.fichier_nom or r.fichier_public_id} → {new_url}")
    except Exception as e:
        print(f"❌ Erreur {r.fichier_nom or r.fichier_public_id}: {e}")

print("✅ Terminé.")
