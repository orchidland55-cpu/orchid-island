from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Rapport
import cloudinary.uploader
import cloudinary
from cloudinary.utils import cloudinary_url
import time

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lister_rapports(request):
    rapports = Rapport.objects.all().values(
        'id', 'date', 'contenu', 'auteur__email',
        'created_at', 'fichier_url', 'fichier_nom', 'statut'  # ✅ ajouter ces champs
    )
    return Response(list(rapports))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creer_rapport(request):
    fichier = request.FILES.get('fichier')
    fichier_url = None
    fichier_nom = None
    fichier_public_id = None

    if fichier:
        fichier_nom = fichier.name
        upload_result = cloudinary.uploader.upload(
            fichier,
            resource_type='raw',
            folder='rapports/',
            use_filename=True,
            unique_filename=True,
            # ✅ NE PAS mettre access_mode='public' pour les PDFs sensibles
            # On va générer une URL signée à la volée
        )
        fichier_public_id = upload_result.get('public_id')
        
        # ✅ Générer une URL signée valable 1 heure
        fichier_url, _ = cloudinary_url(
            fichier_public_id,
            resource_type='raw',
            sign_url=True,
            expires_at=int(time.time()) + 3600,  # 1 heure
        )

    r = Rapport.objects.create(
        auteur=request.user,
        date=request.data.get('date'),
        contenu=request.data.get('contenu', ''),
        fichier_url=fichier_url or '',
        fichier_nom=fichier_nom or '',
        fichier_public_id=fichier_public_id or '',
    )
    return Response({
        'id': r.id,
        'success': True,
        'fichier_url': fichier_url,   # URL signée temporaire
        'fichier_nom': fichier_nom,
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def supprimer_rapport(request, pk):
    try:
        Rapport.objects.get(pk=pk).delete()
        return Response({'success': True})
    except Rapport.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

# ✅ NOUVEAU — Récupérer le contenu complet d'un rapport (fichier inclus)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detail_rapport(request, pk):
    try:
        r = Rapport.objects.get(pk=pk)
        
        # ✅ Régénérer une URL signée fraîche à chaque accès
        fichier_url = None
        if r.fichier_public_id:
            fichier_url, _ = cloudinary_url(
                r.fichier_public_id,
                resource_type='raw',
                sign_url=True,
                expires_at=int(time.time()) + 3600,  # valide 1h
            )
        elif r.fichier_url:
            fichier_url = r.fichier_url  # fallback URL stockée

        return Response({
            'id': r.id,
            'date': r.date,
            'contenu': r.contenu,
            'auteur': r.auteur.email,
            'created_at': r.created_at,
            'fichier_url': fichier_url,
            'fichier_nom': r.fichier_nom or None,
        })
    except Rapport.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

# ✅ NOUVEAU — Valider un rapport (admin, rh, manager uniquement)
ROLES_AUTORISES = ['admin', 'rh', 'manager']

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def valider_rapport(request, pk):
    user_role = getattr(request.user, 'role', None)
    if user_role not in ROLES_AUTORISES:
        return Response({'error': 'Permission refusée. Seuls admin, RH et manager peuvent valider.'}, status=403)
    try:
        r = Rapport.objects.get(pk=pk)
        r.statut = 'valide'   # Assurez-vous que ce champ existe dans votre modèle
        r.save()
        return Response({'success': True, 'statut': r.statut})
    except Rapport.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)
