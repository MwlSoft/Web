from django.contrib import admin
from Modulos.Academica.models import Carrera, Estudiante, Matricula, Curso, Pensum, EstadoCurso, Profesor
from django.db.models import Max
from .models import Pensum, Carrera
from django.utils.html import format_html

# Register your models here.

admin.site.register(Estudiante)
admin.site.register(Carrera)
admin.site.register(Matricula)

class EstadoCursoAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'curso', 'estado', 'fecha_actualizacion')
    list_filter = ('estado', 'curso')
    search_fields = ('estudiante__nombres', 'curso__nombre')

admin.site.register(EstadoCurso, EstadoCursoAdmin)

class CursoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'creditos', 'profesor', 'semestre')
    filter_horizontal = ('prerequisitos',)  # Esto crea una interfaz más amigable para seleccionar prerequisitos

admin.site.register(Curso, CursoAdmin)

class PensumAdmin(admin.ModelAdmin):
    change_list_template = 'admin/pensum_change_list.html'
    
    def changelist_view(self, request, extra_context=None):
        # Obtener todas las carreras
        carreras = Carrera.objects.all()
        
        # Preparar los datos para cada carrera
        pensum_data = {}
        for carrera in carreras:
            # Obtener el número máximo de semestres para esta carrera
            max_semestre = Pensum.objects.filter(carrera=carrera).aggregate(Max('semestre'))['semestre__max'] or 0
            
            # Inicializar la estructura de datos para esta carrera
            pensum_data[carrera] = {i: [] for i in range(1, max_semestre + 1)}
            
            # Obtener todos los cursos del pensum para esta carrera
            pensum_items = Pensum.objects.filter(carrera=carrera).select_related('curso')
            
            # Organizar los cursos por semestre
            for item in pensum_items:
                pensum_data[carrera][item.semestre].append(item.curso)

        extra_context = extra_context or {}
        extra_context['pensum_data'] = pensum_data
        return super().changelist_view(request, extra_context=extra_context)

admin.site.register(Pensum, PensumAdmin)
admin.site.register(Profesor)