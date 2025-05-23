from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Activo, PerfilUsuario, Empresa, Ticket
from .forms import LoginForm, TicketForm, ActivoForm, CerrarTicketForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from .decorators import admin_required, tecnico_required, cliente_required
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.models import User
import logging
import json
from django.views.decorators.csrf import csrf_exempt
import secrets
import string

logger = logging.getLogger(__name__)

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
    logger.info(f"Login attempt - Method: {request.method}")
    
    if request.user.is_authenticated:
        logger.info(f"User already authenticated: {request.user.username}")
        return redirect('inicio')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        logger.info(f"Form data received: {request.POST}")
        
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            logger.info(f"Attempting authentication for username: {username}")
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                logger.info(f"Authentication successful for user: {username}")
                login(request, user)
                messages.success(request, 'Inicio de sesión exitoso.')
                return redirect('inicio')
            else:
                logger.warning(f"Authentication failed for username: {username}")
                messages.error(request, 'Usuario o contraseña incorrectos.')
        else:
            logger.warning(f"Form validation failed: {form.errors}")
            messages.error(request, 'Por favor, ingresa un usuario y contraseña válidos.')
    else:
        form = LoginForm()
    
    return render(request, 'inventory/login.html', {'form': form})

@login_required
def inventory_list(request):
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
    empresa_id = request.GET.get('empresa_id')
    if empresa_id:
        activos = Activo.objects.filter(empresa_id=empresa_id).values('id', 'nombre')
        return JsonResponse(list(activos), safe=False)
    return JsonResponse([], safe=False)

@admin_required
def crear_activo(request):
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

# Vista de diagnóstico temporal - ELIMINAR DESPUÉS DE SOLUCIONAR EL PROBLEMA
@csrf_exempt
def debug_view(request):
    # Clave secreta para proteger esta vista
    DEBUG_KEY = 'debug_secret_key'
    
    if request.method == 'POST':
        data = json.loads(request.body)
        key = data.get('key')
        
        if key != DEBUG_KEY:
            return JsonResponse({'error': 'Acceso no autorizado'}, status=403)
        
        action = data.get('action')
        
        if action == 'list_users':
            users = list(User.objects.values('id', 'username', 'email', 'is_active', 'is_staff', 'is_superuser'))
            return JsonResponse({'users': users})
        
        elif action == 'create_superuser':
            username = data.get('username', 'admin')
            email = data.get('email', 'admin@example.com')
            password = data.get('password')
            
            if not password:
                # Generar contraseña aleatoria si no se proporciona
                alphabet = string.ascii_letters + string.digits
                password = ''.join(secrets.choice(alphabet) for i in range(12))
            
            try:
                if User.objects.filter(username=username).exists():
                    user = User.objects.get(username=username)
                    user.set_password(password)
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()
                    return JsonResponse({
                        'status': 'updated',
                        'username': username,
                        'password': password
                    })
                else:
                    user = User.objects.create_superuser(username, email, password)
                    return JsonResponse({
                        'status': 'created',
                        'username': username,
                        'password': password
                    })
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        
        elif action == 'test_auth':
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return JsonResponse({'error': 'Se requiere usuario y contraseña'}, status=400)
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                return JsonResponse({
                    'status': 'success',
                    'user_id': user.id,
                    'username': user.username,
                    'is_superuser': user.is_superuser,
                    'is_staff': user.is_staff
                })
            else:
                return JsonResponse({'status': 'failed', 'message': 'Autenticación fallida'})
        
        elif action == 'check_db':
            try:
                user_count = User.objects.count()
                empresa_count = Empresa.objects.count()
                activo_count = Activo.objects.count()
                ticket_count = Ticket.objects.count()
                
                return JsonResponse({
                    'status': 'success',
                    'counts': {
                        'users': user_count,
                        'empresas': empresa_count,
                        'activos': activo_count,
                        'tickets': ticket_count
                    }
                })
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
    
    return HttpResponse("""
    <html>
    <head>
        <title>Herramienta de Diagnóstico</title>
        <script>
            async function sendRequest(action, extraData = {}) {
                const key = document.getElementById('key').value;
                if (!key) {
                    alert('Por favor ingresa la clave de seguridad');
                    return;
                }
                
                const data = { key, action, ...extraData };
                
                try {
                    const response = await fetch('/debug/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data),
                    });
                    
                    const result = await response.json();
                    document.getElementById('result').textContent = JSON.stringify(result, null, 2);
                } catch (error) {
                    document.getElementById('result').textContent = 'Error: ' + error.message;
                }
            }
            
            function createSuperuser() {
                const username = document.getElementById('username').value || 'admin';
                const email = document.getElementById('email').value || 'admin@example.com';
                const password = document.getElementById('password').value || '';
                
                sendRequest('create_superuser', { username, email, password });
            }
            
            function testAuth() {
                const username = document.getElementById('auth_username').value;
                const password = document.getElementById('auth_password').value;
                
                if (!username || !password) {
                    alert('Por favor ingresa usuario y contraseña');
                    return;
                }
                
                sendRequest('test_auth', { username, password });
            }
        </script>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .section { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            h2 { margin-top: 0; }
            input, button { margin: 5px 0; padding: 8px; }
            button { background: #4CAF50; color: white; border: none; cursor: pointer; }
            button:hover { background: #45a049; }
            pre { background: #f5f5f5; padding: 10px; overflow: auto; }
        </style>
    </head>
    <body>
        <h1>Herramienta de Diagnóstico</h1>
        <p>Esta página es temporal y debe eliminarse después de solucionar los problemas.</p>
        
        <div class="section">
            <h2>Clave de Seguridad</h2>
            <input type="password" id="key" placeholder="Ingresa la clave de seguridad" />
        </div>
        
        <div class="section">
            <h2>Listar Usuarios</h2>
            <button onclick="sendRequest('list_users')">Listar Usuarios</button>
        </div>
        
        <div class="section">
            <h2>Crear/Actualizar Superusuario</h2>
            <input type="text" id="username" placeholder="Nombre de usuario (default: admin)" />
            <input type="email" id="email" placeholder="Email (default: admin@example.com)" />
            <input type="password" id="password" placeholder="Contraseña (vacío = generar aleatoria)" />
            <button onclick="createSuperuser()">Crear/Actualizar Superusuario</button>
        </div>
        
        <div class="section">
            <h2>Probar Autenticación</h2>
            <input type="text" id="auth_username" placeholder="Nombre de usuario" />
            <input type="password" id="auth_password" placeholder="Contraseña" />
            <button onclick="testAuth()">Probar Autenticación</button>
        </div>
        
        <div class="section">
            <h2>Verificar Base de Datos</h2>
            <button onclick="sendRequest('check_db')">Verificar Conteos</button>
        </div>
        
        <div class="section">
            <h2>Resultado</h2>
            <pre id="result">Los resultados aparecerán aquí...</pre>
        </div>
    </body>
    </html>
    """)

def login_simple(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, 'Inicio de sesión exitoso.')
                return redirect('inicio')
            else:
                messages.error(request, f'Usuario o contraseña incorrectos. Username: {username}')
        else:
            messages.error(request, 'Por favor, ingresa un usuario y contraseña.')
    
    return render(request, 'inventory/login_simple.html')
