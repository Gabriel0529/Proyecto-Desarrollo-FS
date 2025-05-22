from django.db import models
from django.contrib.auth.models import User


class InventoryItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Empresa(models.Model):
    nombre = models.CharField(max_length=255)
    nit = models.CharField(max_length=50, unique=True)
    direccion = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.nombre


class Activo(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=100, choices=[('PC', 'PC'), ('Impresora', 'Impresora'), ('Router', 'Router')])
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    fecha_registro = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.nombre


# Si quieres asociar el usuario a una empresa:
class PerfilUsuario(models.Model):
    ROLE_CHOICES = [
        ('cliente', 'Cliente'),
        ('tecnico', 'Técnico'),
        ('admin', 'Administrador'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cliente')

    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"
    
    def is_admin(self):
        return self.rol == 'admin'
    
    def is_tecnico(self):
        return self.rol == 'tecnico'
    
    def is_cliente(self):
        return self.rol == 'cliente'


class Ticket(models.Model):
    ESTADO_CHOICES = [
        ('abierto', 'Abierto'),
        ('en_progreso', 'En progreso'),
        ('cerrado', 'Cerrado'),
    ]

    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
    ]

    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='abierto')
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD_CHOICES, default='media')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    activo = models.ForeignKey("inventory.Activo", on_delete=models.CASCADE, null=True, blank=True)
    
    # Campos para seguimiento de tickets
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    comentario_cierre = models.TextField(blank=True, null=True)
    cerrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_cerrados')

    def __str__(self):
        return self.titulo
