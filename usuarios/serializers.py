from rest_framework import serializers
from .models import User, Filho
from django.utils import timezone
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['nome_completo'] = user.nome_completo
        token['papel'] = user.papel
        token['is_superuser'] = user.is_superuser

        return token

class FilhoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filho
        fields = ['id', 'nome_completo', 'data_nascimento']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    filhos = FilhoSerializer(many=True, required=False, write_only=True)
    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password2', 'nome_completo', 'foto_perfil',
            'data_nascimento', 'nome_pai', 'nome_mae', 'cpf', 'rg', 'naturalidade',
            'estado_civil', 'nome_conjuge', 'data_casamento', 'telefone', 'endereco',
            'bairro', 'cidade', 'cep', 'profissao', 'nivel_escolar', 'data_conversao',
            'batizado_aguas', 'data_batismo', 'local_batismo', 'outra_igreja_batismo',
            'recebido_por_aclamacao', 'membro_congregacao', 'qual_congregacao',
            'frequenta_escola_biblica', 'qual_classe_escola_biblica',
            'deseja_exercer_funcao', 'qual_funcao_deseja', 'tem_alergia_medicacao',
            'alergias_texto', 'filhos'
        )
        extra_kwargs = { 'password': {'write_only': True} }

    def validate(self, data):
        if data['password'] != data.get('password2'):
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return data

    def create(self, validated_data):
        filhos_data = validated_data.pop('filhos', [])
        validated_data.pop('password2', None)
        user = User.objects.create_user(**validated_data)
        for filho_data in filhos_data:
            Filho.objects.create(user=user, **filho_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    filhos = FilhoSerializer(many=True, read_only=True)
    estado_civil_display = serializers.CharField(source='get_estado_civil_display', read_only=True)
    nivel_escolar_display = serializers.CharField(source='get_nivel_escolar_display', read_only=True)
    local_batismo_display = serializers.CharField(source='get_local_batismo_display', read_only=True)
    papel_display = serializers.CharField(source='get_papel_display', read_only=True)
    foto_perfil = serializers.SerializerMethodField()
    aprovado_por = serializers.StringRelatedField()

    class Meta:
        model = User
        # Lista explícita de campos para expor, excluindo a senha e campos de admin.
        fields = [
            'id', 'username', 'nome_completo', 'email', 'foto_perfil', 'data_nascimento',
            'nome_pai', 'nome_mae', 'cpf', 'rg', 'naturalidade', 'estado_civil', 
            'estado_civil_display', 'nome_conjuge', 'data_casamento', 'telefone', 
            'endereco', 'bairro', 'cidade', 'cep', 'profissao', 'nivel_escolar', 
            'nivel_escolar_display', 'data_conversao', 'batizado_aguas', 'data_batismo', 
            'local_batismo', 'local_batismo_display', 'outra_igreja_batismo', 
            'recebido_por_aclamacao', 'membro_congregacao', 'qual_congregacao',
            'frequenta_escola_biblica', 'qual_classe_escola_biblica', 'deseja_exercer_funcao',
            'qual_funcao_deseja', 'tem_alergia_medicacao', 'alergias_texto', 'filhos',
            'papel', 'papel_display', 'aprovado', 'aprovado_por', 'data_aprovacao', 'data_cadastro'
        ]
    
    def get_foto_perfil(self, obj):
        request = self.context.get('request')
        if obj.foto_perfil and request:
            return request.build_absolute_uri(obj.foto_perfil.url)
        return None
    

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para o usuário editar seu próprio perfil.
    Apenas os campos permitidos estão listados.
    """
    class Meta:
        model = User
        # Lista de campos que o usuário PODE editar.
        # Campos sensíveis como 'papel', 'aprovado' e 'is_staff' são omitidos por segurança.
        fields = [
            'nome_completo', 'email', 'foto_perfil', 'data_nascimento', 'nome_pai', 
            'nome_mae', 'cpf', 'rg', 'naturalidade', 'estado_civil', 'nome_conjuge', 
            'data_casamento', 'telefone', 'endereco', 'bairro', 'cidade', 'cep',
            'profissao', 'nivel_escolar', 'data_conversao', 'batizado_aguas', 
            'data_batismo', 'local_batismo', 'outra_igreja_batismo', 
            'recebido_por_aclamacao', 'membro_congregacao', 'qual_congregacao', 
            'frequenta_escola_biblica', 'qual_classe_escola_biblica',
            'deseja_exercer_funcao', 'qual_funcao_deseja',
            'tem_alergia_medicacao', 'alergias_texto'
        ]

class AdminUserListSerializer(serializers.ModelSerializer):
    """
    Serializer para a lista de usuários na área de administração.
    """
    papel_display = serializers.CharField(source='get_papel_display', read_only=True)
    foto_perfil_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'nome_completo', 'email', 'papel', 'papel_display', 
            'aprovado', 'ativo', 'data_cadastro', 'foto_perfil_url'
        ]
    
    def get_foto_perfil_url(self, obj):
        request = self.context.get('request')
        if obj.foto_perfil and request:
            return request.build_absolute_uri(obj.foto_perfil.url)
        return None
    
class AdminUserCreateSerializer(UserRegistrationSerializer):
    """
    Serializer para um secretário criar um novo usuário.
    Herda do UserRegistrationSerializer e adiciona a capacidade de definir o papel.
    """
    class Meta(UserRegistrationSerializer.Meta):
        # Adiciona o campo 'papel' aos campos que podem ser escritos
        fields = UserRegistrationSerializer.Meta.fields + ('papel',)

    def create(self, validated_data):
        # Chama o 'create' da classe pai para criar o usuário
        user = super().create(validated_data)
        # Define o usuário como aprovado, pois foi criado por um secretário
        user.aprovado = True
        user.aprovado_por = self.context['request'].user
        user.data_aprovacao = timezone.now()
        user.save(update_fields=['aprovado', 'aprovado_por', 'data_aprovacao'])
        return user
    
class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para um secretário editar um usuário existente.
    Permite alterar o papel e outros campos importantes.
    """
    class Meta:
        model = User
        # Lista de campos que um secretário pode editar.
        # O username e a senha não estão aqui para evitar alterações acidentais.
        fields = [
            'nome_completo', 'email', 'foto_perfil', 'data_nascimento', 'nome_pai', 
            'nome_mae', 'cpf', 'rg', 'naturalidade', 'estado_civil', 'nome_conjuge', 
            'data_casamento', 'telefone', 'endereco', 'bairro', 'cidade', 'cep',
            'profissao', 'nivel_escolar', 'data_conversao', 'batizado_aguas', 
            'data_batismo', 'local_batismo', 'outra_igreja_batismo', 
            'recebido_por_aclamacao', 'membro_congregacao', 'qual_congregacao', 
            'frequenta_escola_biblica', 'qual_classe_escola_biblica',
            'deseja_exercer_funcao', 'qual_funcao_deseja',
            'tem_alergia_medicacao', 'alergias_texto',
            'papel', 'ativo' # Secretário pode mudar o papel e o status de ativo
        ]

class UserBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para listagem de usuários"""
    papel_display = serializers.CharField(source='get_papel_display', read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'nome_completo', 'email', 'papel', 'papel_display', 'is_superuser', 'is_staff')