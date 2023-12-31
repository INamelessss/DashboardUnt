from django.db import models

class Course(models.Model):
    school = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    credits = models.IntegerField()
    cycle = models.CharField(max_length=100)
    ht = models.IntegerField()
    hp = models.IntegerField()
    hl = models.IntegerField()

class Teacher(models.Model):
    STATUS_CHOICES = (
        ('Does not register', 'Does not register'),
        ('Masters', 'Masters'),
        ('Doctors', 'Doctors'),
    )

    TYPE_CHOICES = (
        ('Contracted', 'Contracted'),
        ('Main', 'Main'),
    )

    school = models.CharField(max_length=100)
    surname_and_names = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    category = models.CharField(max_length=100)
    grade = models.CharField(max_length=100)
    birth = models.DateField()
    income = models.DateField()

class CourseModel(models.Model):
    SEMESTER_CHOICES = [
        ('Spring', 'Spring'),
        ('Summer', 'Summer'),
        ('Fall', 'Fall'),
    ]
    HEADQUARTERS_CHOICES = [
        ('Headquarters A', 'Headquarters A'),
        ('Headquarters B', 'Headquarters B'),
        ('Headquarters C', 'Headquarters C'),
    ]
    CYCLE_CHOICES = [
        ('Cycle 1', 'Cycle 1'),
        ('Cycle 2', 'Cycle 2'),
        ('Cycle 3', 'Cycle 3'),
    ]

    semester = models.CharField(max_length=20, choices=SEMESTER_CHOICES)
    headquarters = models.CharField(max_length=20, choices=HEADQUARTERS_CHOICES)
    cycle = models.CharField(max_length=20, choices=CYCLE_CHOICES)
    section = models.CharField(max_length=1)
    career = models.CharField(max_length=50)
    course = models.CharField(max_length=50)
    hours = models.IntegerField()
    classroom = models.CharField(max_length=20)

    def __str__(self):
        return self.course
    
class Sede(models.Model):
    name = models.CharField(max_length=100)

class CourseAssignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('course', 'teacher', 'sede')

    def __str__(self):
        return f"{self.course.name} - {self.teacher.surname_and_names} - {self.sede.name}"
    
class CourseSchedule(models.Model):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    course_model = models.ForeignKey(CourseModel, on_delete=models.CASCADE, default=1)
    day = models.CharField(max_length=20, choices=DAYS_OF_WEEK)
    type = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.course} - {self.day}: {self.start_time} - {self.end_time}"

class Research(models.Model):
    teacher = models.ManyToManyField(Teacher)
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=100)
    type_of_research = models.CharField(max_length=100)
    research_line = models.CharField(max_length=100)
    sub_line = models.CharField(max_length=100)
    budget = models.DecimalField(max_digits=10, decimal_places=2)

class Estudiante(models.Model):
    numero_matricula = models.CharField(max_length=10, unique=True)
    apellidos_nombres = models.CharField(max_length=200)
    escuela = models.CharField(max_length=100)
    sede = models.CharField(max_length=100)

class Enrollment(models.Model):
    student = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    times_taken = models.IntegerField(default=1)
    period = models.CharField(max_length=10)

class Activo(models.Model):
    numero_pc = models.CharField(max_length=20)
    codigo = models.CharField(max_length=20)
    descripcion = models.CharField(max_length=100)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    serie = models.CharField(max_length=50)
    estado = models.CharField(max_length=20)
    observaciones = models.TextField()
    ambiente = models.CharField(max_length=50)