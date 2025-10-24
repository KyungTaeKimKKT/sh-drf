from django.conf import settings
from rest_framework import pagination
from rest_framework.response import Response


class CustomPagination(pagination.PageNumberPagination):

    def get_paginated_response(self, data):
        return Response({
            'links': {
               'next': self.get_next_link(),
               'previous': self.get_previous_link()
            },
            'countTotal': self.page.paginator.count,
            'countOnPage': self.page_size,
            'current_Page':self.page.number,
            'total_Page': self.page.paginator.num_pages,
            'results': data
    })