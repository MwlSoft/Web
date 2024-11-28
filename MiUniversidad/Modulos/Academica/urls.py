from django.urls import path
from . import views
from .views import agregar_pensum, listar_pensum, chat_view
from .views import enviar_asesoria, buzón_asesoria

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_estudiante, name='login'),
    path('registro/', views.registro_estudiante, name='registro'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_estudiante, name='logout'),
    path('matricular/', views.matricular_curso, name='matricular_curso'),
    path('cancelar-curso/', views.cancelar_curso, name='cancelar_curso'),
    path('pensum/agregar/', agregar_pensum, name='agregar_pensum'),
    path('pensum/listar/', listar_pensum, name='pensum_listar'),

    path('profesor/login/', views.login_profesor, name='login_profesor'),
    path('profesor/logout/', views.logout_profesor, name='logout_profesor'),
    path('profesor/dashboard/', views.dashboard_profesor, name='dashboard_profesor'),
    path('profesor/curso/<str:curso_codigo>/estudiantes/', views.lista_estudiantes_curso, name='lista_estudiantes_curso'),
    path('profesor/calificacion/<int:matricula_id>/', views.asignar_calificaciones, name='asignar_calificaciones'),

    path('chat/<int:receiver_id>/', views.chat_view, name='chat'),
    path('crear_chat/', views.crear_chat, name='crear_chat'),

    path('enviar-asesoria/', enviar_asesoria, name='enviar_asesoria'),
    path('buzon-asesoria/', buzón_asesoria, name='buzon_asesoria'),
]   