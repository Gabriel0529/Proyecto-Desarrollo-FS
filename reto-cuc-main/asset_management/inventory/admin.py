from django.contrib import admin
from .models import Empresa, Activo, PerfilUsuario
from .models import Ticket

admin.site.register(Empresa)
admin.site.register(Activo)
admin.site.register(PerfilUsuario)
admin.site.register(Ticket)