from django.urls import path
from .views import ConfiguracaoSiteAPIView, DevocionalRecenteAPIView, LiderancaAPIView, DepartamentosAPIView, AgendaAPIView, DevocionalListView

urlpatterns = [
    path('configuracao/', ConfiguracaoSiteAPIView.as_view(), name='api-configuracao'),
    path('devocionais/recente/', DevocionalRecenteAPIView.as_view(), name='api-devocional-recente'),
    path('lideranca/', LiderancaAPIView.as_view(), name='api-lideranca'),
    path('departamentos/', DepartamentosAPIView.as_view(), name='api-departamentos'),
    path('agenda/', AgendaAPIView.as_view(), name='api-agenda'),
    path('devocionais/', DevocionalListView.as_view(), name='api-devocional-list'),

]