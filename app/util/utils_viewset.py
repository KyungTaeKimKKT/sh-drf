from rest_framework.parsers import MultiPartParser,FormParser
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters

class Util_Model_Viewset:
    # queryset =  MODEL.objects.order_by('-id')

    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]