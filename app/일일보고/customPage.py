from django.conf import settings
from rest_framework import pagination
from rest_framework.response import Response


class CustomPagination(pagination.PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 1000
    page_size = 10

    # https://stackoverflow.com/questions/44370252/django-rest-framework-how-to-turn-off-on-pagination-in-modelviewset
    def get_page_size(self, request):
        if self.page_size_query_param:
            page_size = min(int(request.query_params.get(self.page_size_query_param, self.page_size)),
                        self.max_page_size)
            if page_size > 0:
                print ( self.page_size)
                return page_size
            elif page_size == 0:
                print ( self.page_size)
                return None
            else:
                pass
        print ( self.page_size)
        return self.page_size
    
    def get_paginated_response(self, data):
        return Response({
            'links': {
               'next': self.get_next_link(),
               'previous': self.get_previous_link()
            },
            'countTotal': self.page.paginator.count,
            'countOnPage': self.get_page_size(self.request),
            'current_Page':self.page.number,
            'total_Page': self.page.paginator.num_pages,
            'results': data
    })