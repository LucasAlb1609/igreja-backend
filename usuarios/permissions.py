from rest_framework.permissions import BasePermission

class IsSecretario(BasePermission):
    """
    Permissão customizada que permite acesso apenas a usuários
    com o papel de 'secretario'.
    """
    def has_permission(self, request, view):
        # A permissão é concedida se o usuário estiver autenticado E tiver o papel de secretário.
        return bool(request.user and request.user.is_authenticated and request.user.is_secretario)