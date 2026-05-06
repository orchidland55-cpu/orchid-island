from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Tache
from projets.models import Projet

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lister_taches(request):
    taches = Tache.objects.all().values('id','titre','description','statut','projet__id','projet__titre')
    return Response(list(taches))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creer_tache(request):
    try:
        projet = Projet.objects.get(pk=request.data.get('projet_id'))
        t = Tache.objects.create(
            titre=request.data.get('titre',''),
            description=request.data.get('description',''),
            statut=request.data.get('statut','a_faire'),
            projet=projet,
        )
        return Response({'id': t.id, 'titre': t.titre})
    except Projet.DoesNotExist:
        return Response({'error': 'Projet not found'}, status=404)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def modifier_tache(request, pk):
    try:
        t = Tache.objects.get(pk=pk)
        for field in ['titre','description','statut']:
            if field in request.data:
                setattr(t, field, request.data[field])
        t.save()
        return Response({'success': True})
    except Tache.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def supprimer_tache(request, pk):
    try:
        Tache.objects.get(pk=pk).delete()
        return Response({'success': True})
    except Tache.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)
