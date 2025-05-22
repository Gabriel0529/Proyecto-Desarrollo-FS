from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Activo, PerfilUsuario, Empresa, Ticket
from .forms import LoginForm, TicketForm, ActivoForm, CerrarTicketForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .decorators import admin_required, tecnico_required, cliente_required
from django.contrib.auth import logout

@login_required
def inicio(request):
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        
        context = {
            'perfil': perfil,
        }
        
        if perfil.is_cliente():
            empresa = perfil.empresa
            if empresa:
                activos_count = Activo.objects.filter(empresa=empresa).count()
                tickets_abiertos = Ticket.objects.filter(empresa=empresa, estado='abierto').count()
                tickets_en_progreso = Ticket.objects.filter(empresa=empresa, estado='en_progreso').count()
                tickets_alta_prioridad = Ticket.objects.filter(
                    empresa=empresa, 
                    prioridad='alta',
                    estado__in=['abierto', 'en_progreso']
                ).order_by('-fecha_creacion')[:3]
                
                context.update({
                    'activos_count': activos_count,
                    'tickets_abiertos': tickets_abiertos,
                    'tickets_en_progreso': tickets_en_progreso,
                    'tickets_alta_prioridad': tickets_alta_prioridad,
                })
            else:
                messages.warning(request, 'No tienes una empresa asignada.')
        
        elif perfil.is_tecnico() or perfil.is_admin():
            activos_count = Activo.objects.all().count()
            tickets_abiertos = Ticket.objects.filter(estado='abierto').count()
            tickets_en_progreso = Ticket.objects.filter(estado='en_progreso').count()
            tickets_alta_prioridad = Ticket.objects.filter(
                prioridad='alta',
                estado__in=['abierto', 'en_progreso']
            ).order_by('-fecha_creacion')[:5]
            
            empresas_count = Empresa.objects.all().count()
            tickets_cerrados = Ticket.objects.filter(estado='cerrado').count()
            
            context.update({
                'activos_count': activos_count,
                'tickets_abiertos': tickets_abiertos,
                'tickets_en_progreso': tickets_en_progreso,
                'tickets_alta_prioridad': tickets_alta_prioridad,
                'empresas_count': empresas_count,
                'tickets_cerrados': tickets_cerrados,
            })
        
        return render(request, 'inventory/inicio.html', context)
    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'No tienes un perfil asociado a una empresa.')
        return redirect('login')

def login_view(request):
    if request.session.get('is_logged_in'):
        return redirect('inventory_list')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            if username and password: 
                request.session['is_logged_in'] = True
                messages.success(request, 'Logged in successfully.')
                return redirect('inventory_list')
            else:
                messages.error(request, 'Please enter valid username and password.')
    else:
        form = LoginForm()
    return render(request, 'inventory/login.html', {'form': form})

def inventory_list(request):
    if not request.session.get('is_logged_in'):
        messages.warning(request, 'Please log in to access the inventory.')
        return redirect('login')
    return redirect('activos_por_empresa')

@login_required
def activos_por_empresa(request):
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        
        if perfil.is_cliente():
            if perfil.empresa:
                activos = Activo.objects.filter(empresa=perfil.empresa)
            else:
                activos = Activo.objects.none()
                messages.warning(request, 'No tienes una empresa asignada.')
        else:
            activos = Activo.objects.all()
        
        return render(request, 'inventory/inventory_list.html', {
            'activos': activos,
            'perfil': perfil
        })
    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'No tienes un perfil asociado a una empresa.')
        return redirect('login')

@login_required
def lista_tickets(request):
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        
        if perfil.is_cliente():
            if perfil.empresa:
                tickets = Ticket.objects.filter(empresa=perfil.empresa).order_by('-fecha_creacion')
            else:
                tickets = Ticket.objects.none()
                messages.warning(request, 'No tienes una empresa asignada.')
        else:
            tickets = Ticket.objects.all().order_by('-fecha_creacion')
        
        return render(request, 'inventory/ticket_list.html', {
            'tickets': tickets,
            'perfil': perfil
        })
    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'No tienes un perfil asociado a una empresa.')
        return redirect('login')

@login_required
def crear_ticket(request):
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        
        if request.method == 'POST':
            form = TicketForm(request.POST)
            if form.is_valid():
                ticket = form.save(commit=False)
                ticket.usuario = request.user
                
                empresa_id = request.POST.get('empresa')
                if empresa_id:
                    empresa = Empresa.objects.get(id=empresa_id)
                    ticket.empresa = empresa
                else:
                    ticket.empresa = perfil.empresa
                
                ticket.save()
                
                messages.success(request, 'Ticket creado correctamente.')
                return redirect('lista_tickets')
            else:
                messages.error(request, 'Error al crear el ticket. Por favor, verifica los datos.')
        else:
            form = TicketForm()
            
            if perfil.is_cliente():
                if perfil.empresa:
                    form.fields['empresa'].initial = perfil.empresa.id
                    form.fields['empresa'].queryset = Empresa.objects.filter(id=perfil.empresa.id)
                    form.fields['activo'].queryset = Activo.objects.filter(empresa=perfil.empresa)
                else:
                    messages.warning(request, 'No tienes una empresa asignada.')
                    return redirect('inicio')
            else:
                form.fields['empresa'].queryset = Empresa.objects.all()
                form.fields['activo'].queryset = Activo.objects.none()
        
        return render(request, 'inventory/ticket_form.html', {'form': form, 'perfil': perfil})
    except Exception as e:
        messages.error(request, f'Error al procesar la solicitud: {str(e)}')
        return redirect('lista_tickets')

@login_required
def get_activos_por_empresa(request):
    """Vista AJAX para obtener activos por empresa"""
    empresa_id = request.GET.get('empresa_id')
    if empresa_id:
        activos = Activo.objects.filter(empresa_id=empresa_id).values('id', 'nombre')
        return JsonResponse(list(activos), safe=False)
    return JsonResponse([], safe=False)

@admin_required
def crear_activo(request):
    """Vista para crear un nuevo activo (solo administradores)"""
    if request.method == 'POST':
        form = ActivoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Activo creado correctamente.')
            return redirect('activos_por_empresa')
    else:
        form = ActivoForm()
    
    return render(request, 'inventory/activo_form.html', {'form': form})

@admin_required
def editar_activo(request, activo_id):
    """Vista para editar un activo existente (solo administradores)"""
    activo = get_object_or_404(Activo, id=activo_id)
    
    if request.method == 'POST':
        form = ActivoForm(request.POST, instance=activo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Activo actualizado correctamente.')
            return redirect('activos_por_empresa')
    else:
        form = ActivoForm(instance=activo)
    
    return render(request, 'inventory/activo_form.html', {
        'form': form,
        'activo': activo,
        'is_edit': True
    })

@tecnico_required
def cerrar_ticket(request, ticket_id):
    """Vista para cerrar un ticket (solo técnicos y administradores)"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if ticket.estado == 'cerrado':
        messages.warning(request, 'Este ticket ya está cerrado.')
        return redirect('lista_tickets')
    
    if request.method == 'POST':
        form = CerrarTicketForm(request.POST, instance=ticket)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.estado = 'cerrado'
            ticket.fecha_cierre = timezone.now()
            ticket.cerrado_por = request.user
            ticket.save()
            messages.success(request, 'Ticket cerrado correctamente.')
            return redirect('lista_tickets')
    else:
        form = CerrarTicketForm(instance=ticket)
    
    return render(request, 'inventory/cerrar_ticket.html', {
        'form': form,
        'ticket': ticket
    })

@tecnico_required
def cambiar_estado_ticket(request, ticket_id, nuevo_estado):
    """Vista para cambiar el estado de un ticket (solo técnicos y administradores)"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    estados_validos = [estado[0] for estado in Ticket.ESTADO_CHOICES]
    
    if nuevo_estado not in estados_validos:
        messages.error(request, 'Estado no válido.')
        return redirect('lista_tickets')
    
    if nuevo_estado == 'cerrado' and ticket.estado != 'cerrado':
        return redirect('cerrar_ticket', ticket_id=ticket.id)
    
    ticket.estado = nuevo_estado
    
    if nuevo_estado != 'cerrado' and ticket.estado == 'cerrado':
        ticket.fecha_cierre = None
        ticket.cerrado_por = None
        ticket.comentario_cierre = None
    
    ticket.save()
    messages.success(request, f'Estado del ticket actualizado a "{dict(Ticket.ESTADO_CHOICES)[nuevo_estado]}".')
    return redirect('lista_tickets')

def logout_view(request):
    logout(request)
    return redirect('login')
