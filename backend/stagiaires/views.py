from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import CustomUser
import cloudinary.uploader
import cloudinary
import requests
import uuid
from django.http import HttpResponse
from rest_framework_simplejwt.tokens import AccessToken


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lister_stagiaires(request):
    stagiaires = CustomUser.objects.filter(role='stagiaire').values(
        'id', 'email', 'first_name', 'last_name', 'is_active',
        'absences_non_justifiees', 'ecole', 'formation', 'departement',
        'date_debut_stage', 'date_fin_stage',
        'cv_url',
        'cv_name',
        'cv_public_id',
        'mot_de_passe_clair',
        'statut',
    )
    result = list(stagiaires)
    for s in result:
        if s.get('cv_url'):
            print(f'[LIST] {s["email"]} → cv_url={s["cv_url"]}')
    return Response({'success': True, 'stagiaires': result})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_cv(request):
    email = request.data.get('email')
    fichier = request.FILES.get('cv')

    print(f'[CV UPLOAD] email={email}, fichier={fichier}')

    if not email or not fichier:
        return Response({'success': False, 'error': 'Email et fichier requis'}, status=400)

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return Response({'success': False, 'error': 'Utilisateur non trouvé'}, status=404)

    print(f'[CV UPLOAD] User id={user.id}, cv_url actuel={user.cv_url}')

    # Supprimer l'ancien CV Cloudinary si existant
    if user.cv_public_id:
        try:
            cloudinary.uploader.destroy(user.cv_public_id, resource_type='raw')
            print(f'[CV UPLOAD] Ancien CV supprimé: {user.cv_public_id}')
        except Exception as e:
            print(f'[CV UPLOAD] Erreur suppression: {e}')

    # Upload vers Cloudinary
    try:
        unique_id = uuid.uuid4().hex[:8]
        upload_result = cloudinary.uploader.upload(
            fichier,
            resource_type='raw',
            folder='orchid_cv',
            public_id=f'cv_{user.id}_{unique_id}',
            overwrite=True,
        )

        cv_url = upload_result.get('secure_url')
        cv_public_id = upload_result.get('public_id')

        print(f'[CV UPLOAD] Cloudinary OK: url={cv_url}')

        if not cv_url:
            return Response({'success': False, 'error': 'URL Cloudinary vide'}, status=500)

        # ✅ Utiliser .update() au lieu de .save() pour éviter le cache ORM
        rows = CustomUser.objects.filter(id=user.id).update(
            cv_url=cv_url,
            cv_name=fichier.name,
            cv_public_id=cv_public_id,
        )
        print(f'[CV UPLOAD] DB update: {rows} row(s) mis à jour')

        # Vérification
        check = CustomUser.objects.get(id=user.id)
        print(f'[CV UPLOAD] Vérif DB: cv_url={check.cv_url}')

        return Response({
            'success': True,
            'cv_url': cv_url,
            'cv_name': fichier.name,
        })

    except Exception as e:
        print(f'[CV UPLOAD] Erreur: {e}')
        import traceback
        traceback.print_exc()
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_cv(request):
    email = request.GET.get('email')
    if not email:
        return Response({'success': False, 'error': 'Email requis'}, status=400)

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return Response({'success': False, 'error': 'Utilisateur non trouvé'}, status=404)

    if user.cv_public_id:
        try:
            cloudinary.uploader.destroy(user.cv_public_id, resource_type='raw')
        except Exception as e:
            print(f'[CV DELETE] Erreur Cloudinary: {e}')

    CustomUser.objects.filter(id=user.id).update(
        cv_url=None,
        cv_name=None,
        cv_public_id=None,
    )

    return Response({'success': True})


@api_view(['GET'])
def proxy_cv(request, user_id):
    """Proxy pour servir les CVs Cloudinary avec auth JWT."""
    token_str = request.GET.get('token')
    if token_str:
        try:
            AccessToken(token_str)
        except Exception:
            return HttpResponse('Token invalide', status=401)
    elif not request.user.is_authenticated:
        return HttpResponse('Non authentifié', status=401)

    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return HttpResponse('Utilisateur non trouvé', status=404)

    if not user.cv_url:
        return HttpResponse('Pas de CV', status=404)

    print(f'[PROXY CV] Serving cv_url={user.cv_url}')

    try:
        cv_response = requests.get(user.cv_url, timeout=15)
        cv_response.raise_for_status()

        nom = user.cv_name or 'cv.pdf'
        if nom.lower().endswith('.pdf'):
            content_type = 'application/pdf'
        elif nom.lower().endswith('.docx'):
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            content_type = 'application/octet-stream'

        response = HttpResponse(cv_response.content, content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{nom}"'
        response['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        print(f'[PROXY CV] Erreur: {e}')
        return HttpResponse(f'Erreur: {e}', status=500)
