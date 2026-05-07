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
        # ✅ Uploader sur Cloudinary
        resource_type = "raw"  # pour PDF, DOCX, etc.
        
        result = cloudinary.uploader.upload(
            fichier,
            folder="rapports",
            resource_type=resource_type,
            use_filename=True,
            unique_filename=True,
            access_mode="public",  # ✅ Rendre le fichier public
        )
        fichier_url = result.get("secure_url")
        fichier_public_id = result.get("public_id")

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
        
        # ✅ Générer une URL signée valable 1 heure si nécessaire
        fichier_url = None
        if r.fichier_public_id:
            fichier_url, _ = cloudinary_url(
                r.fichier_public_id,
                resource_type="raw",
                sign_url=True,
                expires_at=int(time.time()) + 3600  # 1 heure
            )
        else:
            fichier_url = r.fichier_url or None
            
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

    if not r.fichier_url:
        return HttpResponse('Pas de fichier', status=404)

    # Streamer le fichier depuis Cloudinary
    try:
        cloudinary_response = requests.get(r.fichier_url, timeout=15)
        if cloudinary_response.status_code != 200:
            return HttpResponse('Fichier inaccessible', status=502)

        nom = r.fichier_nom or 'fichier'
        download = request.GET.get('download')

        # Déterminer Content-Type
        if nom.lower().endswith('.pdf'):
            content_type = 'application/pdf'
        elif nom.lower().endswith('.docx'):
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            content_type = 'application/octet-stream'

        response = HttpResponse(cloudinary_response.content, content_type=content_type)
        
        if download:
            response['Content-Disposition'] = f'attachment; filename="{nom}"'
        else:
            response['Content-Disposition'] = f'inline; filename="{nom}"'
        
        response['Access-Control-Allow-Origin'] = '*'
        response['X-Frame-Options'] = 'ALLOWALL'
        return response

    except Exception as e:
        return HttpResponse(f'Erreur lecture fichier: {e}', status=500)
