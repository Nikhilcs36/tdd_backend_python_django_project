from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class UserPagination(PageNumberPagination):
    """Custom pagination class for user listings."""
    page_size = 3  # Default page size
    page_size_query_param = 'size'  # Allows client to override page size
    max_page_size = 100  # Maximum allowed page size
    page_query_param = 'page'  # Page number parameter


class SafePageNumberPagination(PageNumberPagination):
    """
    Custom pagination class that returns empty results instead of 404
    when the requested page is out of range.

    This prevents frontend errors when "load more" is clicked after
    the last page has been reached.
    """

    page_size_query_param = 'size'
    max_page_size = 100
    page_query_param = 'page'

    def paginate_queryset(self, queryset, request, view=None):
        """
        Override to handle out-of-range pages gracefully.
        Returns an empty list instead of raising Http404.
        """
        # Store request for later use in get_paginated_response
        self.request = request

        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)

        try:
            page_number = int(page_number)
        except (TypeError, ValueError):
            page_number = 1

        try:
            self.page = paginator.page(page_number)
            return list(self.page)
        except Exception:
            # Return empty results for out-of-range pages instead of 404.
            # Set up page with paginator so get_paginated_response works.
            if paginator.num_pages > 0:
                # Return the last page if page number is too high
                self.page = paginator.page(paginator.num_pages)
                return list(self.page)
            else:
                # No pages at all - set a dummy page reference
                self.page = paginator.page(1) if paginator.count > 0 else None
                if self.page is None:
                    # Store count for empty response
                    self.count = queryset.count()
                return []

    def get_paginated_response(self, data):
        """
        Override to handle empty page gracefully when no results.
        """
        if hasattr(self, 'page') and self.page is not None:
            return Response(OrderedDict([
                ('count', self.page.paginator.count),
                ('next', self.get_next_link()),
                ('previous', self.get_previous_link()),
                ('results', data)
            ]))
        else:
            # Handle the case where there's no page at all
            return Response(OrderedDict([
                ('count', getattr(self, 'count', 0)),
                ('next', None),
                ('previous', None),
                ('results', data)
            ]))


class LoginActivityPagination(SafePageNumberPagination):
    """Custom pagination class for login activity listings."""
    page_size = 100  # Default page size for login activity
    page_size_query_param = 'size'
    max_page_size = 100
    page_query_param = 'page'
