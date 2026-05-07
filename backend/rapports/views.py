from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Rapport
import cloudinary.uploader
import cloudinary
from cloudinary.utils import cloudinary_url
import time
import requests
from django.http import HttpResponse, StreamingHttpResponse
from rest_framework_simplejwt.tokens import AccessToken

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
        # ✅ Stocker localement au lieu de Cloudinary
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import os
        import uuid

        # Générer un nom de fichier unique
        ext = os.path.splitext(fichier.name)[1]
        unique_filename = f"rapport_{uuid.uuid4().hex}{ext}"
        path = default_storage.save(f'rapports/{unique_filename}', fichier)
        fichier_url = f"/media/{path}"
        fichier_public_id = path  # Stocker le chemin local comme public_id

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
        # ✅ Retourner l'URL directement sans signature
        return Response({
            'id': r.id,
            'date': r.date,
            'contenu': r.contenu,
            'auteur': r.auteur.email,
            'created_at': r.created_at,
            'fichier_url': r.fichier_url or None,
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


# ✅ NOUVEAU — Proxy qui sert le fichier local au client
@api_view(['GET'])
def proxy_fichier(request, pk):
    # ✅ Accepter token depuis query param (pour iframe)
    token_str = request.GET.get('token')
    if token_str:
        try:
            from users.models import CustomUser
            token = AccessToken(token_str)
            user = CustomUser.objects.get(id=token['user_id'])
        except Exception:
            return HttpResponse('Token invalide', status=401)
    elif not request.user.is_authenticated:
        return HttpResponse('Non authentifié', status=401)

    try:
        r = Rapport.objects.get(pk=pk)
    except Rapport.DoesNotExist:
        return HttpResponse('Not found', status=404)

    if not r.fichier_public_id:
        return HttpResponse('Pas de fichier', status=404)

    # ✅ Servir le fichier local
    from django.core.files.storage import default_storage
    import os

    try:
        # Le fichier_public_id contient maintenant le chemin local
        file_path = r.fichier_public_id
        if not default_storage.exists(file_path):
            return HttpResponse('Fichier non trouvé', status=404)

        file = default_storage.open(file_path, 'rb')
        response = HttpResponse(file.read(), content_type='application/octet-stream')

        # ✅ Gérer le paramètre download pour forcer le téléchargement
        download = request.GET.get('download')
        nom = r.fichier_nom or 'fichier'
        if download:
            response['Content-Disposition'] = f'attachment; filename="{nom}"'
        else:
            response['Content-Disposition'] = f'inline; filename="{nom}"'

        response['Access-Control-Allow-Origin'] = '*'
        response['X-Frame-Options'] = 'ALLOWALL'

        # Déterminer le Content-Type basé sur l'extension
        if nom.lower().endswith('.pdf'):
            response['Content-Type'] = 'application/pdf'
        elif nom.lower().endswith('.docx'):
            response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

        file.close()
        return response
    except Exception as e:
        return HttpResponse(f'Erreur lecture fichier: {e}', status=500)
