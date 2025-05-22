from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import PerfilUsuario

def role_required(roles):
    """
    Decorador para verificar si el usuario tiene uno de los roles requeridos.
    Uso: @role_required(['admin', 'tecnico'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                perfil = PerfilUsuario.objects.get(user=request.user)
                if perfil.rol in roles:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, 'No tienes permisos para acceder a esta página.')
                    return redirect('inicio')
            except PerfilUsuario.DoesNotExist:
                messages.error(request, 'No tienes un perfil de usuario configurado.')
                return redirect('login')
        return _wrapped_view
    return decorator

def admin_required(view_func):
    """Decorador para verificar si el usuario es administrador."""
    return role_required(['admin'])(view_func)

def tecnico_required(view_func):
    """Decorador para verificar si el usuario es técnico."""
    return role_required(['tecnico', 'admin'])(view_func)

def cliente_required(view_func):
    """Decorador para verificar si el usuario es cliente."""
    return role_required(['cliente', 'tecnico', 'admin'])(view_func)
