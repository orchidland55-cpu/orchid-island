from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import CustomUser
import cloudinary.uploader

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lister_stagiaires(request):
    stagiaires = CustomUser.objects.filter(role='stagiaire').values(
        'id', 'email', 'first_name', 'last_name', 'is_active',
        'absences_non_justifiees', 'ecole', 'formation', 'departement',
        'date_debut_stage', 'date_fin_stage',
        'cv_url',      # ✅ URL Cloudinary directe
        'cv_name',     # ✅ Nom du fichier original
        'mot_de_passe_clair',
        'statut',
    )
    return Response({'success': True, 'stagiaires': list(stagiaires)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_cv(request):
    email = request.data.get('email')
    fichier = request.FILES.get('cv')

    if not email or not fichier:
        return Response({'success': False, 'error': 'Email et fichier requis'}, status=400)

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return Response({'success': False, 'error': 'Utilisateur non trouvé'}, status=404)

    # ✅ Upload vers Cloudinary en raw (pas image) + accès public
    upload_result = cloudinary.uploader.upload(
        fichier,
        resource_type='raw',
        folder='cv/',
        use_filename=True,
        unique_filename=True,
        access_control=[{"access_type": "anonymous"}],  # ← public
    )

    # ✅ Stocker l'URL Cloudinary dans le modèle
    user.cv_url = upload_result.get('secure_url')
    user.cv_name = fichier.name
    user.cv_public_id = upload_result.get('public_id')
    user.save()

    return Response({
        'success': True,
        'cv_url': user.cv_url,
        'cv_name': user.cv_name,
    })


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

    # ✅ Supprimer de Cloudinary si public_id disponible
    if user.cv_public_id:
        try:
            cloudinary.uploader.destroy(user.cv_public_id, resource_type='raw')
        except Exception as e:
            print(f'[CV DELETE] Erreur Cloudinary: {e}')

    user.cv_url = None
    user.cv_name = None
    user.cv_public_id = None
    user.save()

    return Response({'success': True})
