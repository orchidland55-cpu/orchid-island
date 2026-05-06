from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Rapport
import cloudinary.uploader

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

    if fichier:
        fichier_nom = fichier.name
        # ✅ Utiliser resource_type='raw' pour PDF/DOCX (pas 'image')
        upload_result = cloudinary.uploader.upload(
            fichier,
            resource_type='raw',          # ← clé du fix
            folder='rapports/',
            use_filename=True,
            unique_filename=True,
            access_mode='public',         # ← AJOUTER CETTE LIGNE
        )
        fichier_url = upload_result.get('secure_url')

    r = Rapport.objects.create(
        auteur=request.user,
        date=request.data.get('date'),
        contenu=request.data.get('contenu', ''),
        fichier_url=fichier_url or '',    # stocker l'URL directement
        fichier_nom=fichier_nom or '',
    )
    return Response({
        'id': r.id,
        'success': True,
        'fichier_url': fichier_url,
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
        return Response({
            'id': r.id,
            'date': r.date,
            'contenu': r.contenu,
            'auteur': r.auteur.email,
            'created_at': r.created_at,
            'fichier_url': r.fichier_url or None,   # ← décommenter + utiliser fichier_url
            'fichier_nom': r.fichier_nom or None,   # ← ajouter aussi le nom
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
