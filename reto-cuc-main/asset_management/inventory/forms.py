from django import forms
from .models import Ticket, Activo, InventoryItem, Empresa

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter item name',
            }),
            'description': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter item description',
            }),
        }

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
        'placeholder': 'Enter username',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
        'placeholder': 'Enter password',
    }))

class TicketForm(forms.ModelForm):
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'id': 'id_empresa',
        })
    )
    
    class Meta:
        model = Ticket
        fields = ['titulo', 'descripcion', 'prioridad', 'activo']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Título del ticket',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Descripción detallada del problema',
                'rows': 4,
            }),
            'prioridad': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'activo': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'id': 'id_activo',
            }),
        }

class ActivoForm(forms.ModelForm):
    class Meta:
        model = Activo
        fields = ['nombre', 'descripcion', 'tipo', 'empresa']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Nombre del activo',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Descripción del activo',
                'rows': 3,
            }),
            'tipo': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'empresa': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
        }

class CerrarTicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['comentario_cierre']
        widgets = {
            'comentario_cierre': forms.Textarea(attrs={
                'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Comentario de cierre',
                'rows': 3,
            }),
        }
