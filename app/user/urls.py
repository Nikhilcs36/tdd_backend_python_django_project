from django.urls import path
from user import views
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from user.views import CustomTokenObtainPairView

app_name = 'user'

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', views.ManageUserView.as_view(), name='me'),
    path('users/', views.UserListView.as_view(), name='users'),
    path('users/<int:pk>/',
         views.UserDetailView.as_view(),
         name='user-detail'),
]
