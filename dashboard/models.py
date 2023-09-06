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

Course.objects.create(
    school='SISTEMAS',
    code='6570',
    name='INGENIERIA GRAFICA',
    type='ELECTIVO',
    credits=3,
    cycle='III',
    ht=2,
    hp=0,
    hl=3,
)

Course.objects.create(
    school='SISTEMAS',
    code='4503',
    name='APLICACIONES MOVILES',
    type='OBLIGATORIO',
    credits=3,
    cycle='X',
    ht=2,
    hp=2,
    hl=2,
)

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
