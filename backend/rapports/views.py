from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Rapport

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lister_rapports(request):
    rapports = Rapport.objects.all().values('id','date','contenu','auteur__email','created_at')
    return Response(list(rapports))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creer_rapport(request):
    r = Rapport.objects.create(
        auteur=request.user,
        date=request.data.get('date'),
        contenu=request.data.get('contenu',''),
    )
    return Response({'id': r.id, 'success': True})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def supprimer_rapport(request, pk):
    try:
        Rapport.objects.get(pk=pk).delete()
        return Response({'success': True})
    except Rapport.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)
