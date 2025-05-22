from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.inicio, name='inicio'),  
    path('activos/', views.activos_por_empresa, name='activos_por_empresa'),
    path('activos/nuevo/', views.crear_activo, name='crear_activo'),
    path('activos/editar/<int:activo_id>/', views.editar_activo, name='editar_activo'),
    path('tickets/', views.lista_tickets, name='lista_tickets'),
    path('tickets/nuevo/', views.crear_ticket, name='crear_ticket'),
    path('tickets/cerrar/<int:ticket_id>/', views.cerrar_ticket, name='cerrar_ticket'),
    path('tickets/estado/<int:ticket_id>/<str:nuevo_estado>/', views.cambiar_estado_ticket, name='cambiar_estado_ticket'),
    path('api/activos-por-empresa/', views.get_activos_por_empresa, name='get_activos_por_empresa'),
]
