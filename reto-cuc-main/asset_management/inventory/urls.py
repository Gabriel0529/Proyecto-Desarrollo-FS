from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('activos/', views.activos_por_empresa, name='activos_por_empresa'),
    path('activos/crear/', views.crear_activo, name='crear_activo'),
    path('activos/editar/<int:activo_id>/', views.editar_activo, name='editar_activo'),
    path('tickets/', views.lista_tickets, name='lista_tickets'),
    path('tickets/crear/', views.crear_ticket, name='crear_ticket'),
    path('tickets/cerrar/<int:ticket_id>/', views.cerrar_ticket, name='cerrar_ticket'),
    path('tickets/cambiar-estado/<int:ticket_id>/<str:nuevo_estado>/', views.cambiar_estado_ticket, name='cambiar_estado_ticket'),
    path('api/activos-por-empresa/', views.get_activos_por_empresa, name='api_activos_por_empresa'),
    path('debug/', views.debug_view, name='debug_view'),
    path('login-simple/', views.login_simple, name='login_simple'),
    path('create-users/<str:key>/', views.create_users, name='create_users'),
    path('debug-activos/', views.debug_activos, name='debug_activos'),
]
