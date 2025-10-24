"""
Views for the messagebox APIs
"""
import io, csv, pandas as pd
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from rest_framework import (
    viewsets,
    mixins,
    status,
)
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from tqdm import tqdm

from .models import (
    Chat_Room,
    Chat_내용,
    Chat_file,
)
import json

from . import serializers


class Chat_Room_ViewSet(viewsets.ModelViewSet):
    qs = Chat_Room.objects.all()
    serializer_class = serializers.Chat_Room_Serializer

    def get_queryset(self):
        return Chat_Room.objects.filter( 참가자 = self.request.user.id )

    def create(self, request, *args, **kwargs):
        참가자 = json.loads( request.data.get('참가자') )  if request.data.get('참가자') else []
        serializer = self.get_serializer( data=request.data, 참가자=참가자,  partial=True )
        # main thing ends

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers)

    

class Chat_내용_ViewSet(viewsets.ModelViewSet):
    queryset = Chat_내용.objects.order_by('-id')
    serializer_class = serializers.Chat_내용_Serializer

    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =['chatroom_fk__id']

    # def get_queryset(self):
    #     return self.queryset.order_by('id')
    

class Chat_file_ViewSet(viewsets.ModelViewSet):
    qs = Chat_file.objects.all()
    serializer_class = serializers.Chat_file_Serializer

    def get_queryset(self):
        return Chat_file.objects.all()