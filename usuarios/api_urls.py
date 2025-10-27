from django.urls import path
from .views import ( 
    UserRegisterView, DashboardStatsAPIView, UserProfileView, AdminUserListView, AdminPendingUserListView, AdminApproveUserView, AdminRejectUserView, AdminUserDetailView, GerarCartaConviteAPIView, GerarCertificadoBatismoAPIView, SuperuserManagementView, SuperuserDemoteView, UserSelectionListView
)

urlpatterns = [

    # Rotas gerais
    path('auth/register/', UserRegisterView.as_view(), name='api-register'),
    path('users/me/', UserProfileView.as_view(), name='api-user-profile'),

    # Rotas de Superusers

    path('superusers/', SuperuserManagementView.as_view(), name='api-superuser-list'),
    path('superusers/users-available/', UserSelectionListView.as_view(), name='api-users-available'),
    path('superusers/<int:user_id>/demote/', SuperuserDemoteView.as_view(), name='api-superuser-demote'),

    # Rotas de Administração (para Secretário)
    path('admin/dashboard-stats/', DashboardStatsAPIView.as_view(), name='api-dashboard-stats'),
    path('admin/users/', AdminUserListView.as_view(), name='api-admin-user-list'),
    path('admin/pending-users/', AdminPendingUserListView.as_view(), name='api-admin-pending-list'),
    path('admin/users/<int:pk>/approve/', AdminApproveUserView.as_view(), name='api-admin-user-approve'),
    path('admin/users/<int:pk>/reject/', AdminRejectUserView.as_view(), name='api-admin-user-reject'),
    path('admin/users/<int:pk>/', AdminUserDetailView.as_view(), name='api-admin-user-detail'),

     # Rotas para geração de documentos
    path('documentos/gerar-certificado-batismo/', GerarCertificadoBatismoAPIView.as_view(), name='api-gerar-certificado-batismo'),
    path('documentos/gerar-carta-convite/', GerarCartaConviteAPIView.as_view(), name='api-gerar-carta-convite'),
]


