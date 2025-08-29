from rest_framework.pagination import PageNumberPagination


class UserPagination(PageNumberPagination):
    """Custom pagination class for user listings."""
    page_size = 3  # Default page size
    page_size_query_param = 'size'  # Allows client to override page size
    max_page_size = 100  # Maximum allowed page size
    page_query_param = 'page'  # Page number parameter
