from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from .models import ConfiguracaoSite, Departamento, SecaoLideranca, DiaSemana, EventoEspecial, Devocional, Pessoa
from django.conf import settings
from .serializers import ConfiguracaoSiteSerializer, DevocionalSerializer, SecaoLiderancaSerializer, DepartamentoSerializer, DiaSemanaSerializer, EventoEspecialSerializer

# --- VIEWS DA API ---

class ConfiguracaoSiteAPIView(APIView):
    """
    API View para buscar a configuração (singleton) do site.
    """
    def get(self, request, format=None):
        configuracao = ConfiguracaoSite.objects.first()
        if configuracao:
            # Passando o 'request' no contexto do serializer
            serializer = ConfiguracaoSiteSerializer(configuracao, context={'request': request})
            return Response(serializer.data)
        return Response({})

class DevocionalRecenteAPIView(APIView):
    """
    API View para buscar a devocional mais recente.
    """
    def get(self, request, format=None):
        devocional = Devocional.objects.order_by('-data_publicacao').first()
        if devocional:
            # Passando o 'request' no contexto do serializer
            serializer = DevocionalSerializer(devocional, context={'request': request})
            return Response(serializer.data)
        return Response({})
    
class LiderancaAPIView(generics.ListAPIView):
    """
    API View para listar todas as seções de liderança com as pessoas aninhadas.
    """
    queryset = SecaoLideranca.objects.prefetch_related('pessoas').all()
    serializer_class = SecaoLiderancaSerializer    

class DepartamentosAPIView(APIView):
    """
    API View que retorna os departamentos agrupados por categoria.
    """
    def get(self, request, format=None):
        # A ordenação já é feita pelo Meta do modelo
        departamentos = Departamento.objects.all()
        
        departamentos_agrupados = {}
        
        for depto in departamentos:
            categoria_chave = depto.categoria
            
            # Se a categoria ainda não existe no nosso dicionário, a criamos
            if categoria_chave not in departamentos_agrupados:
                departamentos_agrupados[categoria_chave] = {
                    "nome_display": depto.get_categoria_display(),
                    "lista": []
                }
            
            # Serializamos e adicionamos o departamento à lista da sua categoria
            serializer = DepartamentoSerializer(depto, context={'request': request})
            departamentos_agrupados[categoria_chave]['lista'].append(serializer.data)
            
        return Response(departamentos_agrupados)

 
class AgendaAPIView(APIView):
    """
    API View que retorna os dados completos da agenda, incluindo
    dias da semana com eventos aninhados e eventos especiais.
    """
    def get(self, request, format=None):
        # Usamos prefetch_related para otimizar a busca dos eventos
        dias_semana = DiaSemana.objects.prefetch_related('eventos').all()
        eventos_especiais = EventoEspecial.objects.all()

        # Serializamos os dois conjuntos de dados
        dias_serializer = DiaSemanaSerializer(dias_semana, many=True, context={'request': request})
        especiais_serializer = EventoEspecialSerializer(eventos_especiais, many=True, context={'request': request})

        # Montamos a resposta final
        data = {
            'dias_semana': dias_serializer.data,
            'eventos_especiais': especiais_serializer.data
        }
        
        return Response(data)



class DevocionalListView(generics.ListAPIView):
    """
    View de API para listar todas as devocionais, ordenadas pela mais recente.
    Este endpoint é público.
    """
    queryset = Devocional.objects.all().order_by('-data_publicacao')
    serializer_class = DevocionalSerializer
    permission_classes = [AllowAny]