from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import MinValueValidator, MaxValueValidator

class Carrera(models.Model):
    codigo = models.CharField(max_length=3, primary_key=True)
    nombre = models.CharField(max_length=50)
    duracion = models.PositiveSmallIntegerField(default=5)

    def __str__(self):
        txt = "{0} (Duración: {1} año(s))"
        return txt.format(self.nombre, self.duracion)
    
class Estudiante(models.Model):
    cc = models.CharField(max_length=20, primary_key=True)
    nombres = models.CharField(max_length=50)
    apellidoPaterno = models.CharField(max_length=50)
    apellidoMaternos = models.CharField(max_length=50)
    fechaNacimiento = models.DateField()
    sexos = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]
    sexo = models.CharField(max_length=1, choices=sexos, default='F')
    carrera = models.ForeignKey(Carrera, null=False, blank=False, on_delete=models.CASCADE)
    vigencia = models.BooleanField(default=True)
    password = models.CharField(max_length=128, default='')  # Campo para almacenar la contraseña
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
            
    def save(self, *args, **kwargs):
        if not self.pk or self.password:
            self.password = make_password(self.password)  # Hashear la contraseña al guardarla
        super().save(*args, **kwargs)

    def nombreCompleto(self):
        txt = "{0} {1}, {2}"
        return txt.format(self.apellidoPaterno, self.apellidoMaternos, self.nombres)

    def __str__(self):
        txt = "{0} / Carrera: {1} / {2}"
        estadoEstudiante = "Vigente" if self.vigencia else "De Baja"
        return txt.format(self.nombreCompleto(), self.carrera, estadoEstudiante)
    
class Profesor(models.Model):
    codigo = models.CharField(max_length=20, primary_key=True)
    nombres = models.CharField(max_length=50)
    apellidoPaterno = models.CharField(max_length=50)
    apellidoMaternos = models.CharField(max_length=50)
    password = models.CharField(max_length=128)
    vigencia = models.BooleanField(default=True)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
            
    def save(self, *args, **kwargs):
        if not self.pk or self.password:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def nombreCompleto(self):
        txt = "{0} {1}, {2}"
        return txt.format(self.apellidoPaterno, self.apellidoMaternos, self.nombres)

    def __str__(self):
        txt = "{0} (Código: {1})"
        return txt.format(self.nombreCompleto(), self.codigo)

class Curso(models.Model):
    codigo = models.CharField(max_length=6, primary_key=True)
    nombre = models.CharField(max_length=100)
    creditos = models.PositiveSmallIntegerField()
    profesor = models.ForeignKey(Profesor, on_delete=models.SET_NULL, null=True, blank=True)
    semestre = models.PositiveSmallIntegerField(default=1)
    prerequisitos = models.ManyToManyField('self', symmetrical=False, blank=True)

    def __str__(self):
        profesor_info = f" / Docente: {self.profesor.nombreCompleto()}" if self.profesor else " / Sin docente asignado"
        return f"{self.nombre} ({self.codigo}){profesor_info}"
    
class Matricula(models.Model):
    id = models.AutoField(primary_key=True)
    estudiante = models.ForeignKey(Estudiante, null=False, blank=False, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, null=False, blank=False, on_delete=models.CASCADE)
    fechaMatricula = models.DateField(auto_now_add=True)
    N1 = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(20)])
    N2 = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(20)])
    N3 = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(20)])
    examen_final = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(20)])
    class Meta:
        # Añadir restricción única para la combinación estudiante-curso
        unique_together = [['estudiante', 'curso']]
    
    def calcular_nota_final(self):
        if all([self.N1, self.N2, self.N3, self.examen_final]):
            return (self.N1 * 0.2) + (self.N2 * 0.2) + (self.N3 * 0.2) + (self.examen_final * 0.4)
        return None

    def __str__(self):
        txt = "{0} Matriculad{1} en el curso {2} / Fecha: {3}"
        if self.estudiante.sexo == "F":
            letraSexo = "a"
        else:
            letraSexo = "0"
        fecMatricula = self.fechaMatricula.strftime("%A %d/%m/%Y %H:%M:%S")
        return txt.format(self.estudiante.nombreCompleto(),letraSexo,self.curso,fecMatricula)

class Pensum(models.Model):
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, default=1)
    semestre = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = (('carrera', 'curso'),)

    def __str__(self):
        return f"{self.curso.nombre} - {self.carrera.nombre} (Semestre {self.semestre})"
    
class EstadoCurso(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    ESTADOS = [
        ('EC', 'En Curso'),
        ('SC', 'Sin Cursar'),
        ('AP', 'Aprobada')
    ]
    estado = models.CharField(max_length=2, choices=ESTADOS, default='SC')
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('estudiante', 'curso')

    def __str__(self):
        return f"{self.estudiante.nombreCompleto()} - {self.curso.nombre} ({self.get_estado_display()})"