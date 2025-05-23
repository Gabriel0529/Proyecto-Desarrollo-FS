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
    try:
        empresa_id = request.GET.get('empresa_id')
        if not empresa_id:
            return JsonResponse([], safe=False)
        
        # Registrar información para depuración
        logger.info(f"Buscando activos para empresa_id: {empresa_id}")
        
        # Obtener activos
        activos = Activo.objects.filter(empresa_id=empresa_id).values('id', 'nombre')
        activos_list = list(activos)
        
        # Registrar cuántos activos se encontraron
        logger.info(f"Se encontraron {len(activos_list)} activos para la empresa {empresa_id}")
        
        return JsonResponse(activos_list, safe=False)
    except Exception as e:
        logger.error(f"Error al obtener activos: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

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

# Vista para depurar los activos
@login_required
def debug_activos(request):
    try:
        # Obtener todas las empresas
        empresas = Empresa.objects.all()
        
        # Preparar datos para mostrar
        datos = []
        
        for empresa in empresas:
            activos = Activo.objects.filter(empresa=empresa)
            
            datos.append({
                'empresa': {
                    'id': empresa.id,
                    'nombre': empresa.nombre,
                    'nit': empresa.nit
                },
                'activos': [
                    {
                        'id': activo.id,
                        'nombre': activo.nombre,
                        'tipo': activo.tipo
                    } for activo in activos
                ],
                'activos_count': activos.count()
            })
        
        # Obtener usuarios y sus perfiles
        usuarios = []
        for user in User.objects.all():
            try:
                perfil = PerfilUsuario.objects.get(user=user)
                empresa = perfil.empresa.nombre if perfil.empresa else "No asignada"
                empresa_id = perfil.empresa.id if perfil.empresa else None
            except PerfilUsuario.DoesNotExist:
                perfil = None
                empresa = "No tiene perfil"
                empresa_id = None
            
            usuarios.append({
                'id': user.id,
                'username': user.username,
                'rol': perfil.rol if perfil else "No tiene rol",
                'empresa': empresa,
                'empresa_id': empresa_id
            })
        
        return render(request, 'inventory/debug_activos.html', {
            'datos': datos,
            'usuarios': usuarios,
            'total_empresas': empresas.count(),
            'total_activos': Activo.objects.count(),
            'total_usuarios': User.objects.count()
        })
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")

# Vista simplificada para crear usuarios predefinidos
def create_users(request, key):
    if key != 'create_users_123456':
        return HttpResponse("Acceso denegado. Clave incorrecta.", status=403)
    
    try:
        # 1. Usuario Admin
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        admin_user.set_password('Admin123!')
        admin_user.save()
        
        admin_perfil, _ = PerfilUsuario.objects.get_or_create(
            user=admin_user,
            defaults={'rol': 'Admin'}
        )
        admin_perfil.rol = 'Admin'
        admin_perfil.save()
        
        # 2. Usuario Técnico
        tecnico_user, created = User.objects.get_or_create(
            username='tecnico',
            defaults={'email': 'tecnico@example.com'}
        )
        tecnico_user.set_password('Tecnico123!')
        tecnico_user.save()
        
        tecnico_perfil, _ = PerfilUsuario.objects.get_or_create(
            user=tecnico_user,
            defaults={'rol': 'Técnico'}
        )
        tecnico_perfil.rol = 'Técnico'
        tecnico_perfil.save()
        
        # 3. Usuario Cliente
        cliente_user, created = User.objects.get_or_create(
            username='cliente',
            defaults={'email': 'cliente@example.com'}
        )
        cliente_user.set_password('Cliente123!')
        cliente_user.save()
        
        cliente_perfil, _ = PerfilUsuario.objects.get_or_create(
            user=cliente_user,
            defaults={'rol': 'Cliente'}
        )
        cliente_perfil.rol = 'Cliente'
        cliente_perfil.save()
        
        # Crear una empresa para el cliente si no existe
        empresa, _ = Empresa.objects.get_or_create(
            nombre='Empresa Demo',
            defaults={'direccion': 'Dirección Demo', 'telefono': '123456789'}
        )
        
        cliente_perfil.empresa = empresa
        cliente_perfil.save()
        
        return HttpResponse("""
        <html>
        <head>
            <title>Usuarios Creados</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .card { border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 20px; }
                h1, h2 { color: #333; }
                pre { background-color: #f5f5f5; padding: 10px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>Usuarios Creados Exitosamente</h1>
            
            <div class="card">
                <h2>Usuario Administrador</h2>
                <pre>
Usuario: admin
Contraseña: Admin123!
Rol: Admin
                </pre>
            </div>
            
            <div class="card">
                <h2>Usuario Técnico</h2>
                <pre>
Usuario: tecnico
Contraseña: Tecnico123!
Rol: Técnico
                </pre>
            </div>
            
            <div class="card">
                <h2>Usuario Cliente</h2>
                <pre>
Usuario: cliente
Contraseña: Cliente123!
Rol: Cliente
Empresa: Empresa Demo
                </pre>
            </div>
            
            <p><a href="/login/">Ir a la página de login</a></p>
        </body>
        </html>
        """)
    except Exception as e:
        return HttpResponse(f"Error al crear usuarios: {str(e)}", status=500)

@csrf_exempt
def debug_view(request):
    # Verificar clave de seguridad
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            security_key = data.get('security_key')
            
            if security_key != 'debug_secret_key':
                return JsonResponse({'error': 'Invalid security key'}, status=403)
            
            action = data.get('action')
            
            # Listar usuarios
            if action == 'list_users':
                users = []
                for user in User.objects.all():
                    try:
                        perfil = PerfilUsuario.objects.get(user=user)
                        rol = perfil.rol
                    except PerfilUsuario.DoesNotExist:
                        rol = 'No perfil'
                    
                    users.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser,
                        'rol': rol
                    })
                return JsonResponse({'users': users})
            
            # Crear superusuario
            elif action == 'create_superuser':
                username = data.get('username', 'admin')
                email = data.get('email', 'admin@example.com')
                password = data.get('password', '')
                
                if not password:
                    # Generar contraseña aleatoria
                    alphabet = string.ascii_letters + string.digits + '!@#$%^&*()'
                    password = ''.join(secrets.choice(alphabet) for i in range(12))
                
                # Verificar si el usuario ya existe
                if User.objects.filter(username=username).exists():
                    user = User.objects.get(username=username)
                    user.set_password(password)
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
            
            # Probar autenticación
            elif action == 'test_auth':
                username = data.get('username')
                password = data.get('password')
                
                user = authenticate(username=username, password=password)
                if user is not None:
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Authentication successful',
                        'user_id': user.id,
                        'username': user.username
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Authentication failed'
                    })
            
            # Crear usuarios predefinidos
            elif action == 'create_predefined_users':
                from django.contrib.auth.models import User
                
                # 1. Usuario Admin
                admin_user, created = User.objects.get_or_create(
                    username='admin',
                    defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
                )
                admin_user.set_password('Admin123!')
                admin_user.save()
                
                admin_perfil, _ = PerfilUsuario.objects.get_or_create(
                    user=admin_user,
                    defaults={'rol': 'Admin'}
                )
                admin_perfil.rol = 'Admin'
                admin_perfil.save()
                
                # 2. Usuario Técnico
                tecnico_user, created = User.objects.get_or_create(
                    username='tecnico',
                    defaults={'email': 'tecnico@example.com'}
                )
                tecnico_user.set_password('Tecnico123!')
                tecnico_user.save()
                
                tecnico_perfil, _ = PerfilUsuario.objects.get_or_create(
                    user=tecnico_user,
                    defaults={'rol': 'Técnico'}
                )
                tecnico_perfil.rol = 'Técnico'
                tecnico_perfil.save()
                
                # 3. Usuario Cliente
                cliente_user, created = User.objects.get_or_create(
                    username='cliente',
                    defaults={'email': 'cliente@example.com'}
                )
                cliente_user.set_password('Cliente123!')
                cliente_user.save()
                
                cliente_perfil, _ = PerfilUsuario.objects.get_or_create(
                    user=cliente_user,
                    defaults={'rol': 'Cliente'}
                )
                cliente_perfil.rol = 'Cliente'
                cliente_perfil.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Predefined users created',
                    'users': [
                        {'username': 'admin', 'password': 'Admin123!', 'rol': 'Admin'},
                        {'username': 'tecnico', 'password': 'Tecnico123!', 'rol': 'Técnico'},
                        {'username': 'cliente', 'password': 'Cliente123!', 'rol': 'Cliente'}
                    ]
                })
            
            return JsonResponse({'error': 'Invalid action'}, status=400)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # Página HTML para interactuar con la API
    return HttpResponse('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug Tool</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .card { border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 20px; }
            button { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #45a049; }
            input, select { padding: 8px; margin: 5px 0; width: 100%; box-sizing: border-box; }
            pre { background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>Herramienta de Diagnóstico</h1>
        
        <div class="card">
            <h2>Autenticación</h2>
            <p>Ingresa la clave de seguridad para usar esta herramienta:</p>
            <input type="password" id="securityKey" placeholder="Clave de seguridad">
        </div>
        
        <div class="card">
            <h2>Listar Usuarios</h2>
            <p>Ver todos los usuarios en la base de datos:</p>
            <button onclick="listUsers()">Listar Usuarios</button>
            <div id="usersList"></div>
        </div>
        
        <div class="card">
            <h2>Crear/Actualizar Superusuario</h2>
            <p>Crear un nuevo superusuario o actualizar la contraseña de uno existente:</p>
            <input type="text" id="adminUsername" placeholder="Nombre de usuario" value="admin">
            <input type="text" id="adminEmail" placeholder="Email" value="admin@example.com">
            <input type="password" id="adminPassword" placeholder="Contraseña (dejar vacío para generar)">
            <button onclick="createSuperuser()">Crear/Actualizar Superusuario</button>
            <div id="superuserResult"></div>
        </div>
        
        <div class="card">
            <h2>Probar Autenticación</h2>
            <p>Verificar si un usuario puede autenticarse:</p>
            <input type="text" id="testUsername" placeholder="Nombre de usuario">
            <input type="password" id="testPassword" placeholder="Contraseña">
            <button onclick="testAuth()">Probar Autenticación</button>
            <div id="authResult"></div>
        </div>
        
        <div class="card">
            <h2>Crear Usuarios Predefinidos</h2>
            <p>Crear usuarios para los roles Admin, Técnico y Cliente:</p>
            <button onclick="createPredefinedUsers()">Crear Usuarios Predefinidos</button>
            <div id="predefinedResult"></div>
        </div>
        
        <script>
            async function makeRequest(action, data = {}) {
                const securityKey = document.getElementById('securityKey').value;
                if (!securityKey) {
                    alert('Por favor ingresa la clave de seguridad');
                    return;
                }
                
                try {
                    const response = await fetch('/debug/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            security_key: securityKey,
                            action: action,
                            ...data
                        }),
                    });
                    
                    return await response.json();
                } catch (error) {
                    console.error('Error:', error);
                    return { error: 'Request failed' };
                }
            }
            
            async function listUsers() {
                const result = await makeRequest('list_users');
                const container = document.getElementById('usersList');
                
                if (result.error) {
                    container.innerHTML = `<p style="color: red;">Error: ${result.error}</p>`;
                    return;
                }
                
                let html = '<h3>Usuarios en la base de datos:</h3>';
                html += '<pre>' + JSON.stringify(result.users, null, 2) + '</pre>';
                container.innerHTML = html;
            }
            
            async function createSuperuser() {
                const username = document.getElementById('adminUsername').value;
                const email = document.getElementById('adminEmail').value;
                const password = document.getElementById('adminPassword').value;
                
                const result = await makeRequest('create_superuser', { username, email, password });
                const container = document.getElementById('superuserResult');
                
                if (result.error) {
                    container.innerHTML = `<p style="color: red;">Error: ${result.error}</p>`;
                    return;
                }
                
                container.innerHTML = `
                    <h3>Superusuario ${result.status}:</h3>
                    <pre>
Username: ${result.username}
Password: ${result.password}
                    </pre>
                    <p><strong>¡Guarda esta información!</strong></p>
                `;
            }
            
            async function testAuth() {
                const username = document.getElementById('testUsername').value;
                const password = document.getElementById('testPassword').value;
                
                const result = await makeRequest('test_auth', { username, password });
                const container = document.getElementById('authResult');
                
                if (result.error) {
                    container.innerHTML = `<p style="color: red;">Error: ${result.error}</p>`;
                    return;
                }
                
                if (result.status === 'success') {
                    container.innerHTML = `
                        <h3>Autenticación exitosa:</h3>
                        <pre>
User ID: ${result.user_id}
Username: ${result.username}
                        </pre>
                    `;
                } else {
                    container.innerHTML = `
                        <h3>Autenticación fallida:</h3>
                        <p>El usuario o la contraseña son incorrectos.</p>
                    `;
                }
            }
            
            async function createPredefinedUsers() {
                const result = await makeRequest('create_predefined_users');
                const container = document.getElementById('predefinedResult');
                
                if (result.error) {
                    container.innerHTML = `<p style="color: red;">Error: ${result.error}</p>`;
                    return;
                }
                
                let html = '<h3>Usuarios creados:</h3>';
                html += '<pre>' + JSON.stringify(result.users, null, 2) + '</pre>';
                html += '<p><strong>¡Guarda esta información!</strong></p>';
                container.innerHTML = html;
            }
        </script>
    </body>
    </html>
    ''')

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
