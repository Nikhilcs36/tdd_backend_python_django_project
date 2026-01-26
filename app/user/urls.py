from django.urls import path
from user import views
from user.views_dashboard import (
    UserStatsView,
    LoginActivityView,
    AdminDashboardView,
    LoginTrendsView,
    LoginComparisonView,
    LoginDistributionView,
    AdminChartsView,
    UserSpecificStatsView,
    UserSpecificLoginActivityView,
    AdminUsersStatsView
)
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
    path('logout/', views.LogoutView.as_view(), name='logout'),
    # Dashboard endpoints
    path('dashboard/stats/', UserStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/login-activity/',
         LoginActivityView.as_view(), name='login-activity'),
    path(
        'admin/dashboard/',
        AdminDashboardView.as_view(),
        name='admin-dashboard'
    ),
    # Chart endpoints
    path(
        'dashboard/charts/trends/',
        LoginTrendsView.as_view(),
        name='login-trends'
    ),
    path(
        'dashboard/charts/comparison/',
        LoginComparisonView.as_view(),
        name='login-comparison'
    ),
    path(
        'dashboard/charts/distribution/',
        LoginDistributionView.as_view(),
        name='login-distribution'
    ),
    path('admin/charts/', AdminChartsView.as_view(), name='admin-charts'),
    # Role-based dashboard endpoints
    path(
        '<int:user_id>/dashboard/stats/',
        UserSpecificStatsView.as_view(),
        name='user-specific-stats'
    ),
    path(
        '<int:user_id>/dashboard/login-activity/',
        UserSpecificLoginActivityView.as_view(),
        name='user-specific-login-activity'
    ),
    path(
        'admin/dashboard/users/stats/',
        AdminUsersStatsView.as_view(),
        name='admin-users-stats'
    ),
]
