from django.shortcuts import render
from .models import Course, CourseModel, Teacher, Research, Estudiante, CourseAssignment, Sede, Enrollment, Activo
from django.db import models
from django.db.models import Count, Avg, Min, Max
from django.db.models import Sum
from datetime import date, datetime
from django.db.models import F, Q
from django.db.models import Count, Case, When, Value, IntegerField
from django.db.models.functions import ExtractYear
from random import randint
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from roman import fromRoman
import json
from collections import Counter
from django.http import JsonResponse


def genRandomColor():
    randomHue = randint(0, 359)
    return f'hsl({randomHue}deg,71%,65%)'

def getColorFromSet(index, set_length):
    set_length = 1 if(set_length<1) else set_length
    return f'hsl({index*(360/set_length)%360}deg,71%,65%)'

def sort_by_roman_numeral(course):
    return int(course.cycle) if course.cycle.isdigit() else from_roman(course.cycle.upper())

def sort_by_roman_numeral2(course):
    return int(course) if course.isdigit() else from_roman(course.upper())

def to_roman(number):
    num_map = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'),
               (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
    roman = ''

    while number > 0:
        for i, r in num_map:
            while number >= i:
                roman += r
                number -= i

    return roman

def from_roman(roman):
    roman_numerals = {
        'I': 1,
        'V': 5,
        'X': 10,
        'L': 50,
        'C': 100,
        'D': 500,
        'M': 1000
    }
    integer_value = 0
    prev_value = 0

    for char in reversed(roman):
        value = roman_numerals[char]
        if value < prev_value:
            integer_value -= value
        else:
            integer_value += value
        prev_value = value

    return integer_value

def course_list(request, escuela):
    # Get query parameters from request URL
    course_name = request.GET.get('course_name')
    course_cycle = request.GET.get('course_cycle')

    # Filter courses based on query parameters
    courses = Course.objects.all()

    if course_name:
        courses = courses.filter(name__icontains=course_name)
    if course_cycle:
        courses = courses.filter(cycle=course_cycle)


    enrollments = Enrollment.objects.select_related('course', 'student')
    student_lowest_cycles = {}
    for enrollment in enrollments:
        student_id = enrollment.student.id
        course_cycle_number = int(enrollment.course.cycle) if enrollment.course.cycle.isdigit() else from_roman(enrollment.course.cycle.upper())
        if student_id not in student_lowest_cycles or course_cycle_number < student_lowest_cycles[student_id]:
            student_lowest_cycles[student_id] = course_cycle_number

    students_per_cycle_counts = {}
    for enrollment in enrollments:
        student_id = enrollment.student.id
        cycle_number = student_lowest_cycles[student_id]
        times_taken = enrollment.times_taken
        if cycle_number not in students_per_cycle_counts:
            students_per_cycle_counts[cycle_number] = {1: 0, 2: 0, 3: 0, 4: 0}
        if times_taken in students_per_cycle_counts[cycle_number] and students_per_cycle_counts[cycle_number][times_taken] == 0:
            students_per_cycle_counts[cycle_number][times_taken] += 1

    students_per_cycle_chart = {
        'cycles': [],
        'first_time_counts': [],
        'second_time_counts': [],
        'third_time_counts': [],
        'fourth_time_counts': [],
    }
    print(students_per_cycle_counts)
    for cycle_number, counts in students_per_cycle_counts.items():
        cycle_roman = to_roman(cycle_number)
        students_per_cycle_chart['cycles'].append(cycle_roman)
        students_per_cycle_chart['first_time_counts'].append(counts[1]) 
        students_per_cycle_chart['second_time_counts'].append(counts[2])
        students_per_cycle_chart['third_time_counts'].append(counts[3])
        students_per_cycle_chart['fourth_time_counts'].append(counts[4])

    total_credits = courses.aggregate(total_credits=models.Sum('credits'))
    total_courses = courses.count()

    enrollment_counts = Enrollment.objects.values(
    'course__name', 'course__cycle', 'student__sede'
    ).annotate(
        total=Count('student__id', distinct=True)
    )

    course_enrollment_counts = []
    for count in enrollment_counts:
        course_enrollment_counts.append({
            'name': count['course__name'],
            'cycle': count['course__cycle'],
            'sede': count['student__sede'],
            'total': count['total']
        })

    chart_data = {
        'ht': courses.aggregate(Sum('ht'))['ht__sum'],
        'hp': courses.aggregate(Sum('hp'))['hp__sum'],
        'hl': courses.aggregate(Sum('hl'))['hl__sum'],
    }

    course_sede_counts = {course.id: {'Trujillo': 0, 'El Valle': 0} for course in courses}

    for count in course_enrollment_counts:
        course_id = Course.objects.get(name=count['name'], cycle=count['cycle']).id
        sede_name = count['sede']
        total = count['total']
        if course_id in course_sede_counts:
            course_sede_counts[course_id][sede_name] = total

    for course in courses:
        course.trujillo_count = course_sede_counts[course.id]['Trujillo']
        course.el_valle_count = course_sede_counts[course.id]['El Valle']

    normalized_sede_counts = {}
    for count in course_enrollment_counts:
        sede_name = count['sede'].upper()  # Convertir a mayúsculas
        course_id = Course.objects.get(name=count['name'], cycle=count['cycle']).id
        total = count['total']
        if course_id not in normalized_sede_counts:
            normalized_sede_counts[course_id] = {'TRUJILLO': 0, 'EL VALLE': 0}
        normalized_sede_counts[course_id][sede_name] = total

    for course in courses:
        course_id = course.id
        if course_id in normalized_sede_counts:
            course.trujillo_count = normalized_sede_counts[course_id]['TRUJILLO']
            course.el_valle_count = normalized_sede_counts[course_id]['EL VALLE']


    courses = sorted(courses,key=sort_by_roman_numeral)
    context = {
        'escuela':escuela,
        'students_per_cycle_chart':students_per_cycle_chart,
        'courses': courses,
        'total_credits': total_credits['total_credits'],
        'total_courses': total_courses,
        'chart_data': chart_data,
        'course_enrollment_counts': course_enrollment_counts,
        'students_per_cycle_chart': students_per_cycle_chart,
    }
    return render(request, 'cursos/course_list.html', context)

def malla(request, escuela):
    # Get query parameters from request URL
    course_name = request.GET.get('course_name')
    course_cycle = request.GET.get('course_cycle')
    course_type = request.GET.get('course_type')

    # Filter courses based on query parameters
    courses = Course.objects.all()

    if course_name:
        courses = courses.filter(name__icontains=course_name)
    if course_cycle:
        courses = courses.filter(cycle=course_cycle)
    if course_type:
        courses = courses.filter(type=course_type)

    # Calculate total credits and course count
    total_credits = courses.aggregate(total_credits=models.Sum('credits'))
    total_courses = courses.count()

    # Aggregate the HT, HP, and HL data
    chart_data = {
        'ht': courses.aggregate(Sum('ht'))['ht__sum'],
        'hp': courses.aggregate(Sum('hp'))['hp__sum'],
        'hl': courses.aggregate(Sum('hl'))['hl__sum'],
    }

    courses = sorted(courses,key=sort_by_roman_numeral)
    context = {
        'escuela':escuela,
        'courses': courses,
        'total_credits': total_credits['total_credits'],
        'total_courses': total_courses,
        'chart_data': chart_data,
    }
    return render(request, 'cursos/malla.html', context)

def dashboard(request):
    age_range = request.GET.get('age')
    modality = request.GET.get('modality')
    category = request.GET.get('category')
    grade = request.GET.get('grade')
    school = request.GET.get('school')

    current_year = date.today().year

    age_mapping = {
        '21-30 years': '21-30',
        '31-40 years': '31-40',
        '41-50 years': '41-50',
        '51-60 years': '51-60',
        '61+ years': '61+',
    }

    teachers = Teacher.objects.all()

    teachers = Teacher.objects.annotate(
        work=current_year - ExtractYear('income'),
        age=current_year - ExtractYear('birth'),
    )
    teachers = teachers.exclude(birth__isnull=True)

    if age_range:
        if '-' in age_range:
            start_age, end_age = age_range.split('-')
            start_age = start_age.replace('years', '').strip()
            end_age = end_age.replace('years', '').strip()
        else:
            start_age = '61'
            end_age = '120'

        if start_age and end_age:
            current_year = date.today().year
            start_birth_year = current_year - int(end_age) - 1
            end_birth_year = current_year - int(start_age)

            teachers = teachers.filter(birth__year__range=(start_birth_year, end_birth_year))

    if modality:
        teachers = teachers.filter(type=modality)
    if category:
        teachers = teachers.filter(category=category)
    if grade:
        teachers = teachers.filter(grade=grade)
    if school:
        teachers = teachers.filter(school=school)

    # Calculate the degree distribution
    degree_distribution_data = teachers.values('status').annotate(count=Count('status')).order_by('-count')
    degree_distribution = [{'label': data['status'], 'data': data['count']} for data in degree_distribution_data]

    # Calculate the contract distribution
    contract_distribution_data = teachers.values('type').annotate(count=Count('type')).order_by('-count')
    contract_distribution = [{'label': data['type'], 'data': data['count']} for data in contract_distribution_data]

    # Calculate the number of teachers per school
    teachers_per_school_data = teachers.values('school').annotate(count=Count('school')).order_by('-count')

    # Calculate the average age of teachers
    average_age = teachers.aggregate(avg_age=Avg('age'))['avg_age']

    # Filtra los profesores cuya edad es mayor o igual a 70
    teachers_70_or_older = teachers.filter(age__gte=70)

    # Obtiene la cantidad de profesores cuya edad es mayor o igual a 70
    count_teachers_70_or_older = teachers_70_or_older.count()


    teachers_with_research = Teacher.objects.filter(research__isnull=False).values('school').annotate(count=Count('school'))
    teachers_without_research = Teacher.objects.filter(research__isnull=True).values('school').annotate(count=Count('school'))

    teachers_per_school_data = []
    for with_research in teachers_with_research:
        school = with_research['school']
        with_count = with_research['count']
        without_count = next((item['count'] for item in teachers_without_research if item['school'] == school), 0)
        teachers_per_school_data.append({
            'school': school,
            'with_research': with_count,
            'without_research': without_count,
        })

    # Calcular el porcentaje
    percentage_teachers_with_research = (Teacher.objects.filter(research__isnull=False).distinct().count() / Teacher.objects.count()) * 100

    context = {
        'teachers': teachers,
        'degree_data': degree_distribution,
        'contract_data': contract_distribution,
        'teachers_per_school_data': teachers_per_school_data,
        'average_age': average_age,
        'count_teachers_70_or_older': count_teachers_70_or_older,
        'percentage_teachers_with_research': percentage_teachers_with_research,
    }

    return render(request, 'dashboard.html', context)

def docentes(request, escuela):
    age_range = request.GET.get('age')
    modality = request.GET.get('modality')
    category = request.GET.get('category')
    grade = request.GET.get('grade')
    school = request.GET.get('school')
    selected_sede = request.GET.get('sede')

    current_year = date.today().year

    age_mapping = {
        '21-30 years': '21-30',
        '31-40 years': '31-40',
        '41-50 years': '41-50',
        '51-60 years': '51-60',
        '61+ years': '61+',
    }

    teachers = Teacher.objects.all()

    teachers = Teacher.objects.annotate(
        work=current_year - ExtractYear('income'),
        age=current_year - ExtractYear('birth'),
    )
    teachers = teachers.exclude(birth__isnull=True)

    modalidad_options = teachers.values_list('type',flat=True).distinct().order_by('type')
    categoria_options = teachers.values_list('category',flat=True).distinct().order_by('category')
    grado_options = teachers.values_list('grade',flat=True).distinct().order_by('grade')

    if age_range:
        if '-' in age_range:
            start_age, end_age = age_range.split('-')
            start_age = start_age.replace('years', '').strip()
            end_age = end_age.replace('years', '').strip()
        else:
            start_age = '61'
            end_age = '120'

        if start_age and end_age:
            current_year = date.today().year
            start_birth_year = current_year - int(end_age) - 1
            end_birth_year = current_year - int(start_age)

            teachers = teachers.filter(birth__year__range=(start_birth_year, end_birth_year))

    if escuela:
        teachers = teachers.filter(school=escuela)
    if modality:
        teachers = teachers.filter(type=modality)
    if category:
        teachers = teachers.filter(category=category)
    if grade:
        teachers = teachers.filter(grade=grade)
    if selected_sede:
        teachers_ids = CourseAssignment.objects.filter(sede__name=selected_sede).values_list('teacher', flat=True)
        teachers = Teacher.objects.filter(id__in=teachers_ids)
        teachers = teachers.annotate(age=current_year - ExtractYear('birth'))
        
    # Calculate the degree distribution
    degree_distribution_data = teachers.values('status').annotate(count=Count('status')).order_by('-count')
    degree_distribution = [{'label': data['status'], 'data': data['count']} for data in degree_distribution_data]

    # Calculate the contract distribution
    contract_distribution_data = teachers.values('type').annotate(count=Count('type')).order_by('-count')
    contract_distribution = [{'label': data['type'], 'data': data['count']} for data in contract_distribution_data]

    # Calculate the number of teachers per school
    teachers_per_school_data = teachers.values('school').annotate(count=Count('school')).order_by('-count')

    # Calculate the average age of teachers
    average_age = teachers.aggregate(avg_age=Avg('age'))['avg_age']

    # Filtra los profesores cuya edad es mayor o igual a 70
    teachers_70_or_older = teachers.filter(age__gte=70)

    # Obtiene la cantidad de profesores cuya edad es mayor o igual a 70
    count_teachers_70_or_older = teachers_70_or_older.count()


    teachers_with_research = Teacher.objects.filter(research__isnull=False).values('school').annotate(count=Count('school'))
    teachers_without_research = Teacher.objects.filter(research__isnull=True).values('school').annotate(count=Count('school'))

    teachers_per_sede_data = CourseAssignment.objects.values('sede__name').annotate(count=Count('teacher', distinct=True)).order_by('-count')
    teachers_per_sede = [{'sede': data['sede__name'], 'count': data['count']} for data in teachers_per_sede_data]
    sede_names = [data['sede'] for data in teachers_per_sede]
    sede_counts = [data['count'] for data in teachers_per_sede]

    all_sedes = Sede.objects.all().values_list('name', flat=True)

    teachers_per_school_data = []
    for with_research in teachers_with_research:
        school = with_research['school']
        with_count = with_research['count']
        without_count = next((item['count'] for item in teachers_without_research if item['school'] == school), 0)
        teachers_per_school_data.append({
            'school': school,
            'with_research': with_count,
            'without_research': without_count,
        })

    # Calcular el porcentaje
    percentage_teachers_with_research = (Teacher.objects.filter(research__isnull=False).distinct().count() / Teacher.objects.count()) * 100

    context = {
        'modalidad_options': modalidad_options,
        'categoria_options': categoria_options,
        'grado_options': grado_options,
        'escuela':escuela,
        'teachers': teachers,
        'degree_data': degree_distribution,
        'contract_data': contract_distribution,
        'teachers_per_school_data': teachers_per_school_data,
        'average_age': average_age,
        'count_teachers_70_or_older': count_teachers_70_or_older,
        'teachers_per_sede': teachers_per_sede,
        'sede_names':sede_names,
        'sede_count':sede_counts,
        'all_sedes': all_sedes,
        'selected_sede':selected_sede,
        'percentage_teachers_with_research': percentage_teachers_with_research,
    }

    return render(request, 'docentes.html', context)

def schedule_view(request, escuela):
    if request.method == 'POST':
        selected_school = request.POST['school']
        selected_cycle = request.POST['cycle']
        selected_career = request.POST['career']

        courses = CourseModel.objects.filter(headquarters=selected_school, cycle=selected_cycle, career=selected_career)

        schools = CourseModel.objects.values_list('headquarters', flat=True).distinct()
        cycles = CourseModel.objects.values_list('cycle', flat=True).distinct()
        careers = CourseModel.objects.values_list('career', flat=True).distinct()

        courses = courses.prefetch_related('courseschedule_set')

        for index, course in enumerate(courses):
            course.color = getColorFromSet(index, len(courses))

    else:
        schools = CourseModel.objects.values_list('headquarters', flat=True).distinct()
        cycles = CourseModel.objects.values_list('cycle', flat=True).distinct()
        careers = CourseModel.objects.values_list('career', flat=True).distinct()

        courses = []

    # Generate hours range
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    hours_range = []
    start_hour = 7
    end_hour = 22
    for hour in range(start_hour, end_hour + 1):
        hours_range.append('{:02d}:00'.format(hour))

    return render(request, 'schedule.html', {
        'escuela':escuela,'courses': courses, 'schools': schools, 'cycles': cycles, 'hours_range': hours_range, 'careers':careers, 'days_of_week':days_of_week})

def research_analysis(request, escuela):
    # Teachers with research
    teachers_with_research = Teacher.objects.filter(research__isnull=False)

    # Teacher participation per school
    schools = teachers_with_research.values('school').distinct()
    school_counts = []
    for school in schools:
        count = teachers_with_research.filter(school=school['school']).count()
        school_counts.append((school['school'], count))

    # Amount of investigations divided by type of investigation
    research_types = Research.objects.values('type_of_research').distinct()
    type_counts = []
    for research_type in research_types:
        count = Research.objects.filter(type_of_research=research_type['type_of_research']).count()
        type_counts.append((research_type['type_of_research'], count))

    # Condition of the professors who participated in the research
    conditions = teachers_with_research.values('status').distinct()
    condition_counts = []
    for condition in conditions:
        count = teachers_with_research.filter(status=condition['status']).count()
        condition_counts.append((condition['status'], count))

    # Total budget of all the research
    total_budget = Research.objects.aggregate(total_budget=models.Sum('budget'))

    # Total number of research projects
    total_projects = Research.objects.count()

    researchs = Research.objects.all()
    research_line_counts = Counter(researchs.values_list('research_line', flat=True))
    research_line_counts_list = list(research_line_counts.items())

    context = {
        'escuela':escuela,
        'school_counts': school_counts,
        'type_counts': type_counts,
        'condition_counts': condition_counts,
        'total_budget': total_budget['total_budget'],
        'total_projects': total_projects,
        'research_line_counts': research_line_counts_list,
        'researchs': researchs,
    }
    return render(request, 'research_analysis.html', context)

def roman_numeral(n):
    roman_numerals = {
        1: 'I',
        2: 'II',
        3: 'III',
        4: 'IV',
        5: 'V',
        6: 'VI',
        7: 'VII',
        8: 'VIII',
        9: 'IX',
        10: 'X'
    }
    return roman_numerals.get(n, str(n))

def estudiantes(request, escuela):
    filtro_sede = request.GET.get('sede')
    filtro_ciclo = request.GET.get('ciclo')
    courses = Course.objects.all()

    estudiantes_filtrados = Estudiante.objects.all()

    if filtro_sede:
        estudiantes_filtrados = estudiantes_filtrados.filter(sede=filtro_sede)
    
    if filtro_ciclo:
        estudiantes_filtrados = estudiantes_filtrados.filter(enrollment__course__cycle=filtro_ciclo).distinct()

    elementos_por_pagina = 10
    paginator = Paginator(estudiantes_filtrados, elementos_por_pagina)
    pagina = request.GET.get('page', 1)

    try:
        estudiantes_pagina = paginator.page(pagina)
    except PageNotAnInteger:
        estudiantes_pagina = paginator.page(1)
    except EmptyPage:
        estudiantes_pagina = paginator.page(paginator.num_pages)

    carreras = Estudiante.objects.values_list('escuela', flat=True).distinct()
    sedes = Estudiante.objects.values_list('sede', flat=True).distinct()

    enrollments = Enrollment.objects.select_related('course', 'student')
    student_lowest_cycles = {}
    for enrollment in enrollments:
        student_id = enrollment.student.id
        course_cycle_number = sort_by_roman_numeral2(enrollment.course.cycle)
        if student_id not in student_lowest_cycles or course_cycle_number < student_lowest_cycles[student_id]:
            student_lowest_cycles[student_id] = course_cycle_number
            
    students_per_cycle_counts = [0] * 10

    for numero in range(0, 10):
        for valor in student_lowest_cycles.values():
            if valor == numero + 1:
                students_per_cycle_counts[numero] += 1

    sede_counts = estudiantes_filtrados.values('sede').annotate(total=Count('id')).distinct()
    sedes_labels = [item['sede'] for item in sede_counts]
    sedes_totals = [item['total'] for item in sede_counts]

    ciclo_labels = [f"{roman_numeral(i)}" for i in range(1, 11)]
    ciclo_totals = students_per_cycle_counts

    sede_data = json.dumps({
        'labels': sedes_labels,
        'datasets': [{
            'label': 'Total de Alumnos por Sede',
            'data': sedes_totals,
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1,
        }]
    })

    ciclo_data = json.dumps({
        'labels': ciclo_labels,
        'datasets': [{
            'label': 'Total de Alumnos por Ciclo',
            'data': ciclo_totals,
            'backgroundColor': 'rgba(255, 99, 132, 0.2)', 
            'borderColor': 'rgba(255, 99, 132, 1)', 
            'borderWidth': 1,
        }]
    })

    context = {
        'escuela': escuela,
        'estudiantes': estudiantes_filtrados,
        'carreras': carreras,
        'sedes': sedes,
        'filtro_sede': filtro_sede,
        'filtro_ciclo': filtro_ciclo,
        'sede_data': sede_data,
        'ciclo_data': ciclo_data, 
    }

    return render(request, 'estudiantes.html', context)

def activos(request, escuela):
    # Inicialización de variables para filtros
    ambientes = Activo.objects.values_list('ambiente', flat=True).distinct()
    descripciones = Activo.objects.values_list('descripcion', flat=True).distinct()
    estados = Activo.objects.values_list('estado', flat=True).distinct()

    # Filtros iniciales (puedes ajustar estos según sea necesario)
    filtro_ambiente = request.POST.get('ambiente', None)
    filtro_descripcion = request.POST.get('descripcion', None)
    filtro_estado = request.POST.get('estado', None)

    # Base QuerySet
    queryset = Activo.objects.all()

    # Aplicar filtros si se proporcionan
    if filtro_ambiente:
        queryset = queryset.filter(ambiente=filtro_ambiente)
    if filtro_descripcion:
        queryset = queryset.filter(descripcion=filtro_descripcion)
    if filtro_estado:
        queryset = queryset.filter(estado=filtro_estado)

    # Datos para el gráfico de pastel (Estado de equipos)
    datos_pastel = queryset.values('estado').annotate(total=Count('estado'))

    # Base QuerySet para los datos de barras
    datos_barras_qs = queryset.values('ambiente', 'descripcion').annotate(total=Count('id')).order_by('ambiente')

    datos_barras = {}
    for item in datos_barras_qs:
        ambiente = item['ambiente']
        descripcion = item['descripcion']
        total = item['total']
        if ambiente not in datos_barras:
            datos_barras[ambiente] = {}
        datos_barras[ambiente][descripcion] = total
    colores = [
        'rgba(255, 99, 132, 0.2)',  # Rojo
        'rgba(54, 162, 235, 0.2)',  # Azul
        'rgba(255, 206, 86, 0.2)',  # Amarillo
        'rgba(75, 192, 192, 0.2)',  # Verde
        'rgba(153, 102, 255, 0.2)', # Púrpura
        # ... más colores según sea necesario ...
    ]
    # Estructurar los datasets para Chart.js
    datasets = []
    for index, descripcion in enumerate(descripciones):
        # Aquí nos aseguramos de que 'data' es una lista de enteros, que es serializable en JSON
        dataset = {
            'label': descripcion,
            'data': [datos_barras.get(ambiente, {}).get(descripcion, 0) for ambiente in ambientes],
            'backgroundColor': colores[index % len(colores)]
        }
        datasets.append(dataset)

    datos_grafico_barras = {
        'labels': list(ambientes),  # Convertir QuerySet a lista
        'datasets': datasets
    }

    datos_grafico_barras_json = json.dumps(datos_grafico_barras)

    # Datos para la tabla resumen
    tabla_resumen = queryset.values('ambiente', 'descripcion', 'estado').annotate(total=Count('id'))

    datos_pastel_json = json.dumps(list(datos_pastel), default=str)
    datos_barras_json = json.dumps(list(datos_barras), default=str)
    tabla_resumen_json = json.dumps(list(tabla_resumen), default=str)

    print(datos_barras_json)
    print(datos_grafico_barras_json)
    return render(request, 'infraestructura.html', {
        'datos_pastel_json': datos_pastel_json,
        'datos_barras_json': datos_barras_json,
        'tabla_resumen_json': tabla_resumen_json,
        'datos_grafico_barras_json': datos_grafico_barras_json,
        'datos_pastel': datos_pastel,
        'datos_barras': datos_barras,
        'tabla_resumen': tabla_resumen,
        'ambientes': ambientes,
        'descripciones': descripciones,
        'estados': estados,
        'escuela':escuela,
    })

def api_course_students(request,curso):
    course_obj = Course.objects.get(id=curso)
    print('api_course_students: ',curso)

    
    enrollments = Enrollment.objects.filter(course=curso)

    enrolled_students = [
        {
            'id': enrollment.id,
            'student_id': enrollment.student.id,
            'student_names': enrollment.student.apellidos_nombres,
            'student_code': enrollment.student.numero_matricula,
            'student_sede': enrollment.student.sede,
            'times': enrollment.times_taken,
            'period': enrollment.period,
        }
        for enrollment in enrollments
    ]

    print('enrollments: ', enrolled_students)
    return JsonResponse(list(enrolled_students), safe=False)