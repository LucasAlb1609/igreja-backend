from rest_framework import serializers
# 1. Importe os modelos da Agenda
from .models import (
    ConfiguracaoSite, Devocional, SecaoLideranca, Pessoa, Departamento, 
    Pastor, Memorial, DiaSemana, Evento, EventoEspecial
)

# ... (todos os serializers existentes: ConfiguracaoSite, Devocional, Pessoa, SecaoLideranca, Departamento) ...
class ConfiguracaoSiteSerializer(serializers.ModelSerializer):
    imagem_url = serializers.SerializerMethodField()
    class Meta:
        model = ConfiguracaoSite
        fields = ['link_youtube', 'titulo_video', 'imagem_url']
    def get_imagem_url(self, obj):
        request = self.context.get('request')
        if obj.get_imagem_url() and request:
            return request.build_absolute_uri(obj.get_imagem_url())
        return None

class DevocionalSerializer(serializers.ModelSerializer):
    imagem = serializers.SerializerMethodField()
    class Meta:
        model = Devocional
        fields = ['id', 'titulo', 'subtitulo', 'autor', 'imagem', 'conteudo', 'data_publicacao']
    def get_imagem(self, obj):
        request = self.context.get('request')
        if obj.imagem and request:
            return request.build_absolute_uri(obj.imagem.url)
        return None

class PessoaSerializer(serializers.ModelSerializer):
    foto = serializers.SerializerMethodField()
    class Meta:
        model = Pessoa
        fields = ['id', 'nome', 'cargo', 'descricao', 'foto']
    def get_foto(self, obj):
        request = self.context.get('request')
        if obj.foto and request:
            return request.build_absolute_uri(obj.foto.url)
        return None

class SecaoLiderancaSerializer(serializers.ModelSerializer):
    pessoas = PessoaSerializer(many=True, read_only=True)
    class Meta:
        model = SecaoLideranca
        fields = ['id', 'titulo', 'descricao', 'pessoas']

class DepartamentoSerializer(serializers.ModelSerializer):
    imagem = serializers.SerializerMethodField()
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    class Meta:
        model = Departamento
        fields = ['id', 'nome', 'descricao', 'imagem', 'categoria', 'categoria_display']
    def get_imagem(self, obj):
        request = self.context.get('request')
        if obj.imagem and request:
            return request.build_absolute_uri(obj.imagem.url)
        return None


# --- NOVOS SERIALIZERS PARA A AGENDA ---

class EventoSerializer(serializers.ModelSerializer):
    # Formata o horário para "HH:MM"
    horario = serializers.TimeField(format='%H:%M')
    class Meta:
        model = Evento
        fields = ['id', 'titulo', 'descricao', 'horario']

class EventoEspecialSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventoEspecial
        fields = ['id', 'titulo', 'descricao', 'periodo']

class DiaSemanaSerializer(serializers.ModelSerializer):
    # Aninha os eventos dentro de cada dia
    eventos = EventoSerializer(many=True, read_only=True)
    # Expõe o nome amigável (ex: "Domingo")
    nome_display = serializers.CharField(source='get_nome_display', read_only=True)
    # Gera o nome do arquivo do ícone fixo
    icone = serializers.SerializerMethodField()

    class Meta:
        model = DiaSemana
        fields = ['nome', 'nome_display', 'resumo', 'icone', 'eventos']

    def get_icone(self, obj):
        # Mapeia o número do dia para o nome do arquivo do ícone
        nomes_icones = {
            0: 'domingo',
            1: 'segunda',
            2: 'terca',
            3: 'quarta',
            4: 'quinta',
            5: 'sexta',
            6: 'sabado'
        }
        # Retorna o nome do ícone (ex: 'domingo'), ou None se não encontrar
        return nomes_icones.get(obj.nome)