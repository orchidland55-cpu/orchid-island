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
        upload_result = cloudinary.uploader.upload(
            fichier,
            resource_type='raw',
            folder='rapports/',
            use_filename=True,
            unique_filename=True,
            # ✅ Forcer accès public — clé du fix
            type='upload',
            access_control=[{"access_type": "anonymous"}],
        )
        fichier_public_id = upload_result.get('public_id')
        # ✅ Construire URL publique directement (pas de signature)
        fichier_url = upload_result.get('secure_url')

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


# ✅ NOUVEAU — Proxy qui télécharge le fichier Cloudinary et le sert au client
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

    if not r.fichier_url:
        return HttpResponse('Pas de fichier', status=404)

    # ✅ Utiliser l'URL directe publique (pas de signature)
    # L'upload force l'accès public avec access_control anonymous
    fetch_url = r.fichier_url

    # Télécharger le fichier depuis Cloudinary côté serveur
    try:
        resp = requests.get(fetch_url, timeout=30, stream=True)
        resp.raise_for_status()
    except Exception as e:
        return HttpResponse(f'Erreur Cloudinary: {e}', status=502)

    # Déterminer le Content-Type
    nom = r.fichier_nom or 'fichier'
    if nom.lower().endswith('.pdf'):
        content_type = 'application/pdf'
    elif nom.lower().endswith('.docx'):
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    else:
        content_type = resp.headers.get('Content-Type', 'application/octet-stream')

    # Streamer le fichier au client avec les bons headers CORS
    response = StreamingHttpResponse(
        resp.iter_content(chunk_size=8192),
        content_type=content_type,
        status=200,
    )
    response['Content-Disposition'] = f'inline; filename="{nom}"'
    response['Access-Control-Allow-Origin'] = '*'
    response['X-Frame-Options'] = 'ALLOWALL'
    return response
