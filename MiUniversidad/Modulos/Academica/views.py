from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from .models import Estudiante, Carrera, Matricula, Curso, Pensum, EstadoCurso,  Profesor, ChatMessage, AsesoriaMensaje
from datetime import datetime
from django.db import IntegrityError
from .forms import PensumForm
from django.db.models import Q
from django.contrib.auth.models import User
from .forms import AsesoriaMensajeForm

def home(request):
    return render(request, 'home.html')

def login_estudiante(request):
    if request.method == 'POST':
        cc = request.POST.get('cc')
        password = request.POST.get('password')
        try:
            estudiante = Estudiante.objects.get(cc=cc)
            if estudiante.check_password(password):
                request.session['estudiante_id'] = estudiante.cc
                return redirect('dashboard')
            else:
                messages.error(request, 'Contraseña incorrecta')
        except Estudiante.DoesNotExist:
            messages.error(request, 'Estudiante no encontrado')
    return render(request, 'login.html')

def logout_estudiante(request):

    if 'estudiante_id' in request.session:
        del request.session['estudiante_id']
    
    request.session.flush()
    

    return redirect('login')


def registro_estudiante(request):
    if request.method == 'POST':
        cc = request.POST.get('cc')
        nombres = request.POST.get('nombres')
        apellidoPaterno = request.POST.get('apellidoPaterno')
        apellidoMaternos = request.POST.get('apellidoMaternos')
        fechaNacimiento = request.POST.get('fechaNacimiento')
        sexo = request.POST.get('sexo')
        carrera_id = request.POST.get('carrera')
        password = request.POST.get('password')

        try:
            carrera = Carrera.objects.get(codigo=carrera_id)
            estudiante = Estudiante(
                cc=cc,
                nombres=nombres,
                apellidoPaterno=apellidoPaterno,
                apellidoMaternos=apellidoMaternos,
                fechaNacimiento=fechaNacimiento,
                sexo=sexo,
                carrera=carrera,
                password=password
            )
            estudiante.save()
            messages.success(request, 'Registro exitoso')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error en el registro: {str(e)}')
    
    carreras = Carrera.objects.all()
    return render(request, 'registro.html', {'carreras': carreras})

def dashboard(request):
    if not request.session.get('estudiante_id'):
        return redirect('login')

    estudiante_id = request.session.get('estudiante_id')
    estudiante = Estudiante.objects.get(cc=estudiante_id)
    
    matriculas_actuales = Matricula.objects.filter(estudiante=estudiante).select_related('curso')
    cursos_matriculados = {matricula.curso.codigo for matricula in matriculas_actuales}
    
    cursos_aprobados = EstadoCurso.objects.filter(
        estudiante=estudiante,
        estado='AP'
    ).select_related('curso')
    cursos_disponibles = Curso.objects.filter(
        pensum__carrera=estudiante.carrera
    ).exclude(
        Q(codigo__in=cursos_matriculados) | 
        Q(codigo__in=cursos_aprobados.values_list('curso__codigo', flat=True))
    ).distinct()

    cursos_disponibles = [
        curso for curso in cursos_disponibles
        if all(pre.codigo in cursos_aprobados.values_list('curso__codigo', flat=True) for pre in curso.prerequisitos.all())
    ]

    pensum = Pensum.objects.filter(carrera=estudiante.carrera).select_related('curso')
    
    pensum_data = {}
    for item in pensum:
        if item.semestre not in pensum_data:
            pensum_data[item.semestre] = []
        
        estado = 'SC' 
        if item.curso.codigo in cursos_matriculados:
            estado = 'EC' 
        elif item.curso.codigo in cursos_aprobados.values_list('curso__codigo', flat=True):
            estado = 'AP' 
        
        prerequisitos_info = [
            {
                'curso': pre,
                'cumplido': pre.codigo in cursos_aprobados.values_list('curso__codigo', flat=True)
            } for pre in item.curso.prerequisitos.all()
        ]
        
        pensum_data[item.semestre].append({
            'curso': item.curso,
            'estado': estado,
            'estado_display': {
                'SC': 'Sin Cursar',
                'EC': 'En Curso',
                'AP': 'Aprobado'
            }[estado],
            'prerequisitos': prerequisitos_info,
            'puede_matricular': all(pre['cumplido'] for pre in prerequisitos_info) and estado == 'SC'
        })

    context = {
        'estudiante': estudiante,
        'pensum_data': pensum_data,
        'cursos_matriculados': matriculas_actuales,
        'cursos_disponibles': cursos_disponibles,
        'cursos_aprobados': cursos_aprobados,  
    }

    return render(request, 'dashboard.html', context)

def matricular_curso(request):
    if not request.session.get('estudiante_id'):
        messages.error(request, 'Por favor inicia sesión para matricular cursos')
        return redirect('login')

    if request.method == 'POST':
        estudiante_id = request.session.get('estudiante_id')
        curso_id = request.POST.get('curso')
        
        if estudiante_id and curso_id:
            try:
                estudiante = Estudiante.objects.get(cc=estudiante_id)
                curso = Curso.objects.get(codigo=curso_id)
                
                prerequisitos = curso.prerequisitos.all()
                cursos_aprobados = EstadoCurso.objects.filter(
                    estudiante=estudiante,
                    estado='AP'
                ).values_list('curso__codigo', flat=True)
                
                if all(pre.codigo in cursos_aprobados for pre in prerequisitos):
                    try:
                        matricula = Matricula.objects.create(
                            estudiante=estudiante,
                            curso=curso
                        )
                        messages.success(request, f'Te has matriculado exitosamente en el curso {curso.nombre}')
                    except IntegrityError:
                        messages.error(request, 'Ya estás matriculado en este curso')
                else:
                    messages.error(request, 'No cumples con los prerequisitos para matricular este curso.')
            except Curso.DoesNotExist:
                messages.error(request, 'El curso no existe.')
            except Estudiante.DoesNotExist:
                messages.error(request, 'El estudiante no existe.')
        else:
            messages.error(request, 'Datos inválidos.')

    return redirect('dashboard')

def cancelar_curso(request):
   
    if not request.session.get('estudiante_id'):
        messages.error(request, 'Por favor inicia sesión para cancelar cursos')
        return redirect('login')

    if request.method == 'POST':
        estudiante_id = request.session.get('estudiante_id')
        matricula_id = request.POST.get('matricula_id')
        
        if estudiante_id and matricula_id:
            try:
                estudiante = Estudiante.objects.get(cc=estudiante_id)
                matricula = Matricula.objects.get(id=matricula_id, estudiante=estudiante)
                curso_nombre = matricula.curso.nombre
                matricula.delete()
                messages.success(request, f'Has cancelado exitosamente el curso {curso_nombre}')
            except Estudiante.DoesNotExist:
                messages.error(request, 'Estudiante no encontrado')
            except Matricula.DoesNotExist:
                messages.error(request, 'Matrícula no encontrada')
        else:
            messages.error(request, 'Datos inválidos para la cancelación')
    
    return redirect('dashboard')

def agregar_pensum(request):
    if request.method == 'POST':
        form = PensumForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('pensum_listar')
    else:
        form = PensumForm()
    return render(request, 'agregar_pensum.html', {'form': form})

def listar_pensum(request):
    pensums = Pensum.objects.all()
    return render(request, 'listar_pensum.html', {'pensums': pensums})

def login_profesor(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        password = request.POST.get('password')
        try:
            profesor = Profesor.objects.get(codigo=codigo)
            if profesor.check_password(password):
                request.session['profesor_id'] = profesor.codigo
                return redirect('dashboard_profesor')
            else:
                messages.error(request, 'Contraseña incorrecta')
        except Profesor.DoesNotExist:
            messages.error(request, 'Profesor no encontrado')
    return render(request, 'login_profesor.html')

def logout_profesor(request):
    if 'profesor_id' in request.session:
        del request.session['profesor_id']
    request.session.flush()
    return redirect('login_profesor')

def dashboard_profesor(request):
    if not request.session.get('profesor_id'):
        return redirect('login_profesor')
    
    profesor_id = request.session.get('profesor_id')
    profesor = Profesor.objects.get(codigo=profesor_id)
    cursos = Curso.objects.filter(profesor=profesor)
    
    context = {
        'profesor': profesor,
        'cursos': cursos,
    }
    return render(request, 'dashboard_profesor.html', context)

def lista_estudiantes_curso(request, curso_codigo):
    if not request.session.get('profesor_id'):
        return redirect('login_profesor')
    
    profesor_id = request.session.get('profesor_id')
    curso = get_object_or_404(Curso, codigo=curso_codigo, profesor__codigo=profesor_id)
    matriculas = Matricula.objects.filter(curso=curso).select_related('estudiante')
    
    context = {
        'curso': curso,
        'matriculas': matriculas,
    }
    return render(request, 'lista_estudiantes_curso.html', context)

def asignar_calificaciones(request, matricula_id):
    if not request.session.get('profesor_id'):
        return redirect('login_profesor')
    
    profesor_id = request.session.get('profesor_id')
    matricula = get_object_or_404(
        Matricula, 
        id=matricula_id, 
        curso__profesor__codigo=profesor_id
    )
    
    if request.method == 'POST':
        try:
            N1 = request.POST.get('N1')
            N2 = request.POST.get('N2')
            N3 = request.POST.get('N3')
            examen_final = request.POST.get('examen_final')
            
      
            matricula.N1 = float(N1) if N1 else None
            matricula.N2 = float(N2) if N2 else None
            matricula.N3 = float(N3) if N3 else None
            matricula.examen_final = float(examen_final) if examen_final else None
            
            matricula.save()
            
       
            if all([matricula.N1 is not None, matricula.N2 is not None, matricula.N3 is not None, matricula.examen_final is not None]):
                nota_final = matricula.calcular_nota_final()
                if nota_final >= 3.0:
                    EstadoCurso.objects.update_or_create(
                        estudiante=matricula.estudiante,
                        curso=matricula.curso,
                        defaults={'estado': 'AP'}
                    )
                    messages.success(request, 'Estudiante ha aprobado el curso')
                else:
                    EstadoCurso.objects.update_or_create(
                        estudiante=matricula.estudiante,
                        curso=matricula.curso,
                        defaults={'estado': 'RP'}  
                    )
                    messages.success(request, 'Estudiante ha reprobado el curso')
                
            messages.success(request, 'Calificaciones actualizadas exitosamente')
            return redirect('lista_estudiantes_curso', curso_codigo=matricula.curso.codigo)
            
        except ValueError:
            messages.error(request, 'Por favor ingrese valores numéricos válidos')
    
    context = {
        'matricula': matricula,
    }
    return render(request, 'asignar_calificaciones.html', context)


def chat_view(request, receiver_id):
    
    try:
        receiver = Estudiante.objects.get(cc=receiver_id)
    except Estudiante.DoesNotExist:
        receiver = get_object_or_404(Profesor, codigo=receiver_id)

    
    messages = ChatMessage.objects.filter(
        (Q(sender=request.user) & Q(receiver=receiver)) |
        (Q(sender=receiver) & Q(receiver=request.user))
    ).order_by('timestamp')

    context = {
        'receiver': receiver,
        'messages': messages,
    }

    return render(request, 'chat.html', context)



def crear_chat(request):
    estudiantes = Estudiante.objects.all() 
    profesores = Profesor.objects.all()     

    return render(request, 'crear_chat.html', {
        'estudiantes': estudiantes,
        'profesores': profesores,
    })


def enviar_asesoria(request):
    if request.method == 'POST':
        form = AsesoriaMensajeForm(request.POST)
        if form.is_valid():
            mensaje = form.save(commit=False)
            mensaje.estudiante = Estudiante.objects.get(cc=request.session.get('estudiante_id'))
            mensaje.save()
            messages.success(request, 'Mensaje de asesoría enviado exitosamente.')
            return redirect('dashboard') 
    else:
        form = AsesoriaMensajeForm()

    profesores = Profesor.objects.all() 
    return render(request, 'enviar_asesoria.html', {'form': form, 'profesores': profesores})

def buzón_asesoria(request):
    if not request.session.get('profesor_id'):
        return redirect('login_profesor')

    profesor_id = request.session.get('profesor_id')
    mensajes = AsesoriaMensaje.objects.filter(profesor__codigo=profesor_id)

    return render(request, 'buzon_asesoria.html', {'mensajes': mensajes})