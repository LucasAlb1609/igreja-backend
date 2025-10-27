from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import User, ModeloDocumento
from .permissions import IsSecretario
from .serializers import (
    UserRegistrationSerializer, MyTokenObtainPairSerializer, UserProfileSerializer, UserProfileUpdateSerializer, AdminUserListSerializer, AdminUserCreateSerializer, 
    AdminUserUpdateSerializer, UserBasicSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.template.loader import render_to_string
from django.http import HttpResponse
try:
    from weasyprint import HTML
except ImportError:
    HTML = None # Permite que o servidor inicie mesmo sem WeasyPrint instalado localmente
from datetime import datetime
import base64
import os
from django.conf import settings


class MyTokenObtainPairView(TokenObtainPairView):
    """
    View de login que usa nosso serializer de token personalizado.
    """
    serializer_class = MyTokenObtainPairSerializer

class UserRegisterView(generics.CreateAPIView):
    """ View de API para registrar um novo usuário (cadastro). """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

class DashboardStatsAPIView(APIView):
    """ View de API que retorna estatísticas do sistema para o dashboard do secretário. """
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        if not request.user.is_secretario:
            return Response(
                {"detail": "Acesso negado. Apenas secretários podem ver as estatísticas."},
                status=status.HTTP_403_FORBIDDEN
            )
        stats = {
            'total_usuarios': User.objects.count(),
            'usuarios_pendentes': User.objects.filter(aprovado=False).count(),
            'total_membros': User.objects.filter(papel='membro', aprovado=True).count(),
            'total_congregados': User.objects.filter(papel='congregado', aprovado=True).count(),
        }
        return Response(stats)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    View de API para LER ou ATUALIZAR os dados do usuário logado.
    GET: Retorna o perfil (usa UserProfileSerializer).
    PUT/PATCH: Atualiza o perfil (usa UserProfileUpdateSerializer).
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Usa um serializer diferente para leitura (GET) e escrita (PUT/PATCH)
        if self.request.method == 'GET':
            return UserProfileSerializer
        return UserProfileUpdateSerializer

    def get_object(self):
        return self.request.user
    
class AdminUserListView(generics.ListCreateAPIView):
    """
    View de API para secretários LISTAREM (GET com filtros) e CRIAREM (POST) usuários.
    """
    queryset = User.objects.all().order_by('nome_completo')
    permission_classes = [IsAuthenticated, IsSecretario]
    
    # Configuração dos filtros
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['papel', 'aprovado', 'ativo'] # Campos para filtro exato (ex: /api/admin/users/?papel=membro)
    search_fields = ['nome_completo', 'email', 'cpf'] # Campos para busca textual (ex: /api/admin/users/?search=João)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminUserCreateSerializer
        return AdminUserListSerializer

class AdminPendingUserListView(generics.ListAPIView):
    queryset = User.objects.filter(aprovado=False).order_by('data_cadastro')
    serializer_class = AdminUserListSerializer
    permission_classes = [IsAuthenticated, IsSecretario]

class AdminApproveUserView(APIView):
    permission_classes = [IsAuthenticated, IsSecretario]
    def post(self, request, pk, format=None):
        try:
            user_to_approve = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "Usuário não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        new_role = request.data.get('papel')
        if new_role not in ['membro', 'congregado', 'secretario']:
            return Response({"detail": "Papel inválido fornecido."}, status=status.HTTP_400_BAD_REQUEST)
        user_to_approve.aprovado = True
        user_to_approve.aprovado_por = request.user
        user_to_approve.data_aprovacao = timezone.now()
        user_to_approve.papel = new_role
        user_to_approve.save()
        return Response({"detail": f"Usuário {user_to_approve.nome_completo} aprovado como {user_to_approve.get_papel_display()}."}, status=status.HTTP_200_OK)

class AdminRejectUserView(APIView):
    permission_classes = [IsAuthenticated, IsSecretario]
    def delete(self, request, pk, format=None):
        try:
            user_to_reject = User.objects.get(pk=pk, aprovado=False)
        except User.DoesNotExist:
            return Response({"detail": "Usuário pendente não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        user_to_reject.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View de API para um secretário:
    - LER (GET) os detalhes completos de um usuário.
    - ATUALIZAR (PUT/PATCH) os dados de um usuário.
    - EXCLUIR (DELETE) um usuário.
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsSecretario]

    def get_serializer_class(self):
        # Usa um serializer para leitura e outro para escrita
        if self.request.method in ['PUT', 'PATCH']:
            return AdminUserUpdateSerializer
        return UserProfileSerializer

class AdminPendingUserListView(generics.ListAPIView):
    """
    View de API para secretários listarem apenas usuários pendentes de aprovação.
    """
    # Filtra o queryset para pegar apenas usuários não aprovados
    queryset = User.objects.filter(aprovado=False).order_by('data_cadastro')
    serializer_class = AdminUserListSerializer # Reutilizamos o serializer da lista
    permission_classes = [IsAuthenticated, IsSecretario]

class AdminApproveUserView(APIView):
    """
    View de API para um secretário aprovar um usuário e definir seu papel.
    """
    permission_classes = [IsAuthenticated, IsSecretario]

    def post(self, request, pk, format=None):
        try:
            user_to_approve = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "Usuário не encontrado."}, status=status.HTTP_404_NOT_FOUND)

        new_role = request.data.get('papel')
        if new_role not in ['membro', 'congregado', 'secretario']:
            return Response({"detail": "Papel inválido fornecido."}, status=status.HTTP_400_BAD_REQUEST)

        user_to_approve.aprovado = True
        user_to_approve.aprovado_por = request.user
        user_to_approve.data_aprovacao = timezone.now()
        user_to_approve.papel = new_role
        user_to_approve.save()
        
        return Response({"detail": f"Usuário {user_to_approve.nome_completo} aprovado como {user_to_approve.get_papel_display()}."}, status=status.HTTP_200_OK)

class AdminRejectUserView(APIView):
    """
    View de API para um secretário rejeitar (excluir) um cadastro pendente.
    """
    permission_classes = [IsAuthenticated, IsSecretario]

    def delete(self, request, pk, format=None):
        try:
            user_to_reject = User.objects.get(pk=pk, aprovado=False)
        except User.DoesNotExist:
            return Response({"detail": "Usuário pendente não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        
        user_to_reject.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View de API para um secretário:
    - LER (GET) os detalhes completos de um usuário.
    - ATUALIZAR (PUT/PATCH) os dados de um usuário.
    - EXCLUIR (DELETE) um usuário.
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsSecretario]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AdminUserUpdateSerializer
        return UserProfileSerializer
    

class GerarCartaConviteAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSecretario]

    def post(self, request, format=None):
        if HTML is None:
            return Response({"detail": "Erro de servidor: WeasyPrint não configurado."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        data = request.data
        required_fields = ['nome_do_evento', 'data_inicio', 'data_fim', 'horario', 'preletores', 'tipo_destinatario']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return Response({"detail": f"Campos obrigatórios faltando: {', '.join(missing_fields)}."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data_inicio_obj = datetime.strptime(data.get('data_inicio'), '%Y-%m-%d').date()
            data_fim_obj = datetime.strptime(data.get('data_fim'), '%Y-%m-%d').date()
            meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            data_inicio_formatada = data_inicio_obj.strftime('%d')
            data_fim_formatada = f"{data_fim_obj.strftime('%d')} de {meses[data_fim_obj.month - 1]} de {data_fim_obj.strftime('%Y')}"
        except (ValueError, TypeError):
            return Response({"detail": "Formato de data inválido. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # --- CORREÇÃO DO CAMINHO DA IMAGEM ---
        # Caminho aponta para o novo arquivo 'carta.png' na pasta 'documentos'
        background_static_path = 'documentos/carta.png' 
        try:
            from django.contrib.staticfiles.storage import staticfiles_storage
            background_url = request.build_absolute_uri(staticfiles_storage.url(background_static_path))
        except:
            background_url = request.build_absolute_uri(f'/static/{background_static_path}')


        context = {
            'nome_do_evento': data.get('nome_do_evento'),
            'data_inicio_formatada': data_inicio_formatada,
            'data_fim_formatada': data_fim_formatada,
            'horario': data.get('horario'),
            'tema': data.get('tema', ''),
            'versiculo_base': data.get('versiculo_base', ''),
            'referencia_biblica': data.get('referencia_biblica', ''),
            'preletores': [p.strip() for p in data.get('preletores', '').replace(',', '\n').splitlines() if p.strip()],
            'nome_pastor_presidente': "JOÃO GOMES DA SILVA",
            'data_emissao': timezone.now().date(),
            'background_url': background_url, # Passa a URL da imagem de fundo
        }

        if data.get('tipo_destinatario') == 'congregacao':
            template_path = 'documentos/carta_convite_congregacao.html'
            context['nome_congregacao'] = data.get('nome_congregacao', '')
            context['nome_diretor'] = data.get('nome_diretor', '')
            if not context['nome_congregacao']:
                 return Response({"detail": "Nome da congregação é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            template_path = 'documentos/carta_convite_igreja.html'

        try:
            html_string = render_to_string(template_path, context)
            # Passar a base_url é crucial para o WeasyPrint encontrar a background_url
            html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
            pdf = html.write_pdf()

            response = HttpResponse(pdf, content_type='application/pdf')
            nome_evento_arquivo = context['nome_do_evento'].replace(' ', '_').lower()[:30]
            response['Content-Disposition'] = f'inline; filename="convite_{nome_evento_arquivo}_{timezone.now().strftime("%Y%m%d")}.pdf"'
            
            return response
        except Exception as e:
            print(f"Erro ao gerar PDF: {e}")
            return Response({"detail": f"Erro interno ao gerar PDF: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class GerarCertificadoBatismoAPIView(APIView):
    """
    View de API para um membro gerar sua 2ª via do Certificado de Batismo.
    """
    permission_classes = [IsAuthenticated] # Apenas usuários logados

    def post(self, request, format=None):
        if HTML is None:
            return Response({"detail": "Erro de servidor: WeasyPrint não configurado."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        usuario = request.user

        # --- Lógica de Negócio e Segurança ---
        # 1. Verifica se é membro
        if usuario.papel != 'membro':
            return Response({"detail": "Apenas 'Membros' podem gerar este documento."}, status=status.HTTP_403_FORBIDDEN)
        # 2. Verifica se foi batizado
        if not usuario.batizado_aguas:
            return Response({"detail": "O seu perfil não indica que você foi batizado."}, status=status.HTTP_400_BAD_REQUEST)
        # 3. Verifica se tem data de batismo
        if not usuario.data_batismo:
            return Response({"detail": "A data do seu batismo não está registrada. Contate a secretaria."}, status=status.HTTP_400_BAD_REQUEST)

        # Prepara o contexto para o template
        try:
            # Formata a data (dia, mês por extenso, ano)
            meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            data_dia = usuario.data_batismo.strftime('%d')
            data_mes = meses[usuario.data_batismo.month - 1]
            data_ano = usuario.data_batismo.strftime('%Y')
        except Exception:
            return Response({"detail": "Erro ao formatar a data do batismo."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Pega a URL do template de certificado (JPG)
        try:
            from django.contrib.staticfiles.storage import staticfiles_storage
            certificado_url = request.build_absolute_uri(staticfiles_storage.url('documentos/Certificado Batismo - Frente.jpg'))
        except:
            certificado_url = request.build_absolute_uri('/static/documentos/Certificado Batismo - Frente.jpg')

        context = {
            'usuario': usuario,
            'data_batismo_dia': data_dia,
            'data_batismo_mes': data_mes,
            'data_batismo_ano': data_ano[2:], # Pega apenas os dois últimos dígitos do ano (ex: "25")
            'certificado_url': certificado_url,
        }

        try:
            html_string = render_to_string('documentos/certificado_batismo.html', context)
            html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
            pdf = html.write_pdf()

            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="certificado_batismo_{usuario.username}.pdf"'
            return response

        except Exception as e:
            print(f"Erro ao gerar PDF: {e}")
            return Response({"detail": f"Erro interno ao gerar PDF: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class SuperuserManagementView(APIView):
    """
    View para superusers gerenciarem outros superusers
    Apenas superusers podem acessar esta view
    """
    permission_classes = [IsAuthenticated]

    def check_permissions(self, request):
        # Apenas superusers podem gerenciar superusers
        if not request.user.is_superuser:
            self.permission_denied(
                request, 
                message="Apenas superusuários podem gerenciar superusuários."
            )
        return super().check_permissions(request)

    def get(self, request, format=None):
        """Listar todos os superusers"""
        superusers = User.objects.filter(
            is_superuser=True
        ).values('id', 'username', 'nome_completo', 'email', 'date_joined')
        
        return Response({
            'superusers': list(superusers),
            'total': superusers.count()
        })

    def post(self, request, format=None):
        """Promover um usuário para superuser"""
        user_id = request.data.get('user_id')
        try:
            user_to_promote = User.objects.get(id=user_id)
            
            # Verificar se já é superuser
            if user_to_promote.is_superuser:
                return Response(
                    {"detail": "Este usuário já é superusuário."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Promover para superuser
            user_to_promote.is_superuser = True
            user_to_promote.is_staff = True  # Necessário para acessar admin
            user_to_promote.save()
            
            return Response({
                "detail": f"Usuário {user_to_promote.nome_completo} promovido a superusuário."
            })
            
        except User.DoesNotExist:
            return Response(
                {"detail": "Usuário não encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

class SuperuserDemoteView(APIView):
    """View para remover privilégios de superuser"""
    permission_classes = [IsAuthenticated]

    def check_permissions(self, request):
        if not request.user.is_superuser:
            self.permission_denied(
                request, 
                message="Apenas superusuários podem remover privilégios de superusuário."
            )
        return super().check_permissions(request)

    def delete(self, request, user_id, format=None):
        """Reverter um superuser para usuário normal"""
        try:
            user_to_demote = User.objects.get(id=user_id)
            
            # Não permitir remover seus próprios privilégios
            if user_to_demote.id == request.user.id:
                return Response(
                    {"detail": "Você não pode remover seus próprios privilégios de superusuário."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not user_to_demote.is_superuser:
                return Response(
                    {"detail": "Este usuário não é superusuário."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Reverter para usuário normal
            user_to_demote.is_superuser = False
            user_to_demote.is_staff = False
            user_to_demote.save()
            
            return Response({
                "detail": f"Usuário {user_to_demote.nome_completo} teve privilégios de superusuário removidos."
            })
            
        except User.DoesNotExist:
            return Response(
                {"detail": "Usuário não encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

class UserSelectionListView(generics.ListAPIView):
    """
    View para listar usuários para seleção (apenas para superusers)
    Exclui superusers atuais da lista
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserBasicSerializer
    
    def get_queryset(self):
        # Apenas superusers podem acessar
        if not self.request.user.is_superuser:
            return User.objects.none()
        
        # Filtrar usuários que não são superusers (para promoção)
        return User.objects.filter(is_superuser=False).order_by('nome_completo')