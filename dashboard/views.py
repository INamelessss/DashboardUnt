from django.shortcuts import render
from .models import Course, PAdministrativo, Teacher, Research, Estudiante, CourseAssignment, Sede, Enrollment, Activo, Period, Sede, Factultad, Escuela,CourseSchedule, Malla
from django.db import models
from django.db.models import Count, Avg, Min, Max
from django.db.models import Sum
from datetime import date, datetime
from django.db.models import F, Q
from django.db.models import Count, Case, When, Value, IntegerField, OuterRef, Subquery
from django.db.models.functions import ExtractYear
from random import randint
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from roman import fromRoman
import json
from collections import Counter
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404


def get_facultades(request):
    facultades = Factultad.objects.all().values('id', 'name')
    return JsonResponse(list(facultades), safe=False)

def get_periods(request):
    periodos = Period.objects.all().values('id', 'period')
    return JsonResponse(list(periodos), safe=False)

def get_escuelas(request, facultad_id):
    escuelas = Escuela.objects.filter(facultad_id=facultad_id).values('id', 'name')
    return JsonResponse(list(escuelas), safe=False)

def get_distinct_ambientes(request):
    ambientes = Activo.objects.order_by('ambiente').values_list('ambiente', flat=True).distinct()
    return JsonResponse(list(ambientes), safe=False)

def get_distinct_descripcion(request):
    descripciones = Activo.objects.order_by('descripcion').values_list('descripcion', flat=True).distinct()
    return JsonResponse(list(descripciones), safe=False)

def getEscuelaId(name_facultad, name_escuela):
    idFacultad = Factultad.objects.get(name=name_facultad).id
    idEscuela = Escuela.objects.get(facultad=idFacultad, name=name_escuela).id
    print(idEscuela)
    return idFacultad, idEscuela

def genRandomColor():
    randomHue = randint(0, 359)
    return f'hsl({randomHue}deg,71%,65%)'

def getColorFromSet(index, set_length):
    set_length = 1 if(set_length<1) else set_length
    return f'hsl({index*(360/set_length)%360}deg,50%,83%)'

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

@login_required
def course_list(request, facultad, escuela):
    
    idFacultad, idEscuela = getEscuelaId(facultad, escuela)
    escuelas = Escuela.objects.filter(facultad=idFacultad)
    escuela = escuelas.filter(name=escuela).first()
    
    # Get query parameters from request URL
    course_name = request.GET.get('course_name')
    course_cycle = request.GET.get('course_cycle')
    course_period = request.GET.get('course_period')
    malla = request.GET.get('malla')

    # Filter courses based on query parameters
    courses = Course.objects.all()

    if course_name:
        courses = courses.filter(name__icontains=course_name)
    if course_cycle:
        courses = courses.filter(cycle=course_cycle)
    if course_period:
        courses = courses.filter(period__period=course_period)
    if malla: 
        courses = courses.filter(malla=malla)

    period_options = courses.values_list('period__period',flat=True).distinct().order_by('period')

    enrollments = Enrollment.objects.select_related('course', 'student')
    student_lowest_cycles = {}
    for enrollment in enrollments:
        student_id = enrollment.student.id
        course_cycle_number = int(enrollment.course.cycle) if enrollment.course.cycle.isdigit() else from_roman(enrollment.course.cycle.upper())
        if student_id not in student_lowest_cycles or course_cycle_number < student_lowest_cycles[student_id]:
            student_lowest_cycles[student_id] = course_cycle_number

    unique_student_ids = set()

    students_per_cycle_counts = {}
    for enrollment in enrollments:
        student_id = enrollment.student.id
        if student_id not in unique_student_ids:
          unique_student_ids.add(student_id)
          cycle_number = student_lowest_cycles[student_id]
          times_taken = enrollment.times_taken
          if cycle_number not in students_per_cycle_counts:
              students_per_cycle_counts[cycle_number] = {1: 0, 2: 0, 3: 0, 4: 0}
          if times_taken in students_per_cycle_counts[cycle_number]:
              
              students_per_cycle_counts[cycle_number][times_taken] += 1

    students_per_cycle_chart = {
        'cycles': [],
        'first_time_counts': [],
        'second_time_counts': [],
        'third_time_counts': [],
        'fourth_time_counts': [],
    }

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

    course_sede_counts = {course.id: {'TRUJILLO': 0, 'VALLE': 0} for course in courses}

    for count in course_enrollment_counts:
        course_id = Course.objects.get(name=count['name'], cycle=count['cycle']).id
        sede_id = count['sede']
        sede = Sede.objects.get(id=sede_id)
        sede_name = sede.name
        total = count['total']
        if course_id in course_sede_counts:
            course_sede_counts[course_id][sede_name] = total

    for course in courses:
        course.trujillo_count = course_sede_counts[course.id]['TRUJILLO']
        course.el_valle_count = course_sede_counts[course.id]['VALLE']

    normalized_sede_counts = {}
    for count in course_enrollment_counts:
        sede_id = count['sede']
        sede = Sede.objects.get(id=sede_id)
        sede_name = sede.name.upper()
        course_id = Course.objects.get(name=count['name'], cycle=count['cycle']).id
        total = count['total']
        if course_id not in normalized_sede_counts:
            normalized_sede_counts[course_id] = {'TRUJILLO': 0, 'VALLE': 0}
        normalized_sede_counts[course_id][sede_name] = total

    for course in courses:
        course_id = course.id
        if course_id in normalized_sede_counts:
            course.trujillo_count = normalized_sede_counts[course_id]['TRUJILLO']
            course.el_valle_count = normalized_sede_counts[course_id]['VALLE']

    courses = sorted(courses,key=sort_by_roman_numeral)

    sedes = Sede.objects.all()

    context = {
        'facultad': facultad,
        'escuelas': escuelas,
        'escuela':escuela,
        'period_options':period_options,
        'students_per_cycle_chart':students_per_cycle_chart,
        'courses': courses,
        'total_credits': total_credits['total_credits'],
        'total_courses': total_courses,
        'chart_data': chart_data,
        'sedes':sedes,
        'course_enrollment_counts': course_enrollment_counts,
        'students_per_cycle_chart': students_per_cycle_chart,
    }
    return render(request, 'cursos/course_list.html', context)

@login_required
def malla(request, facultad, escuela):
    
    idFacultad, idEscuela = getEscuelaId(facultad, escuela)
    escuelas = Escuela.objects.filter(facultad=idFacultad)
    escuela = escuelas.filter(name=escuela).first()

    mallas = Malla.objects.filter(escuela=escuela).order_by('-año')
    malla_seleccionada = mallas.first()
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
    if malla_seleccionada:
        courses = courses.filter(malla=malla_seleccionada)

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
        'facultad': facultad,
        'escuela':escuela,
        'escuelas': escuelas,
        'courses': courses,
        'total_credits': total_credits['total_credits'],
        'total_courses': total_courses,
        'chart_data': chart_data,
        'mallas':mallas,
        'malla_seleccionada': malla_seleccionada,
    }
    return render(request, 'cursos/malla.html', context)

@login_required
def dashboard(request):  
    periods = Period.objects.all()
    facultades = Factultad.objects.all()
    sedes = Sede.objects.all()
    current_period = periods.order_by('-id').first()
    data = []

    for facultad in facultades:
        facultad_data = {
            'name': facultad.name,
            'text': facultad.text,
            'schools': [],
            'total_enrolled_trujillo': 0,
            'total_enrolled_valle': 0,
            'total_courses_trujillo': 0,
            'total_courses_valle': 0,
        }

        escuelas = facultad.escuela_set.all()
        for escuela in escuelas:
            escuela_data = {
                'name': escuela.name,
                'text': escuela.text,
                'enrolled_trujillo': 0,
                'enrolled_valle': 0,
                'courses_trujillo': 0,
                'courses_valle': 0,
            }

            enrolled_trujillo = Estudiante.objects.filter(escuela=escuela, sede__name='Trujillo').count()
            enrolled_valle = Estudiante.objects.filter(escuela=escuela, sede__name='Valle').count()
            escuela_data['enrolled_trujillo'] = enrolled_trujillo
            escuela_data['enrolled_valle'] = enrolled_valle

            facultad_data['total_enrolled_trujillo'] += enrolled_trujillo
            facultad_data['total_enrolled_valle'] += enrolled_valle

            for sede in sedes:
                courses_in_period = Course.objects.filter(
                    malla__escuela=escuela, 
                    period=current_period
                ).distinct()
                courses_count = 0
                for course in courses_in_period:
                    if Enrollment.objects.filter(
                        course=course, 
                        student__sede=sede,
                        period=current_period
                    ).exclude(student__numero_matricula=0).exists():
                        courses_count += 1
                
                if sede.name == 'Trujillo':
                    escuela_data['courses_trujillo'] = courses_count
                    facultad_data['total_courses_trujillo'] += courses_count
                elif sede.name == 'Valle':
                    escuela_data['courses_valle'] = courses_count
                    facultad_data['total_courses_valle'] += courses_count

            facultad_data['schools'].append(escuela_data)
        
        data.append(facultad_data)


    context = {
        'facultades': facultades,
        'periods': periods,
        'data': data,
        'current_period': current_period,
    }
    return render(request, 'dashboard.html', context)

@login_required
def docentes(request, facultad, escuela):
    
    idFacultad, idEscuela = getEscuelaId(facultad, escuela)
    escuelas = Escuela.objects.filter(facultad=idFacultad)
    escuela = escuelas.filter(id=idEscuela).first()

    age_range = request.GET.get('age')
    modality = request.GET.get('modality')
    category_filter = request.GET.get('category')
    grade = request.GET.get('grade')
    school = request.GET.get('school')
    modalidad = request.GET.get('type')
    condicion = request.GET.get('status')
    selected_sede = request.GET.get('sede')

    current_year = date.today().year

    teachers_grouped = Teacher.objects.values('category', 'type','status').annotate(total=Count('id')).order_by('category', 'type','status').filter(school=escuela)

    conditions = {}

    for entry in teachers_grouped:
        category = entry['category']
        if category not in conditions:
            conditions[category] = {'NOMBRADO': 0, 'CONTRATADO': 0, 'NO CONTRATADO': 0, 'TOTAL': 0}
        conditions[category][entry['status']] += entry['total']
        conditions[category]['TOTAL'] += entry['total']

    total_nombrado = sum(cond['NOMBRADO'] for cond in conditions.values())
    total_contratado = sum(cond['CONTRATADO'] for cond in conditions.values())
    total_no_contratado = sum(cond['NO CONTRATADO'] for cond in conditions.values())
    total_general_conditions = total_nombrado + total_contratado + total_no_contratado

    if total_general_conditions > 0:
        for category, values in conditions.items():
            values['NOMBRADO_percent'] = (values['NOMBRADO'] / total_general_conditions) * 100
            values['CONTRATADO_percent'] = (values['CONTRATADO'] / total_general_conditions) * 100
            values['NO_NOMBRADO_percent'] = (values['NO CONTRATADO'] / total_general_conditions) * 100

    categories = {}

    for entry in teachers_grouped:
        category = entry['category']
        if category not in categories:
            categories[category] = {'TP': 0, 'TC': 0, 'DE': 0, 'TOTAL': 0}
        categories[category][entry['type']] += entry['total']
        categories[category]['TOTAL'] += entry['total']

    total_tp = sum(cat['TP'] for cat in categories.values())
    total_tc = sum(cat['TC'] for cat in categories.values())
    total_de = sum(cat['DE'] for cat in categories.values())
    total_general = total_tp + total_tc + total_de

    total_nombrado_percent = (total_nombrado / total_general_conditions) * 100 if total_general_conditions > 0 else 0
    total_contratado_percent = (total_contratado / total_general_conditions) * 100 if total_general_conditions > 0 else 0
    total_no_contratado_percent = (total_no_contratado / total_general_conditions) * 100 if total_general_conditions > 0 else 0
    total_general_conditions_percent = 100  # El total siempre es el 100%

    table_data = []
    for category in conditions:
        total_cond = conditions[category]['TOTAL']
        total_mod = categories.get(category, {}).get('TOTAL', 0)

        category_data = {
            'category': category,
            'NOMBRADO': conditions[category].get('NOMBRADO', 0),
            'CONTRATADO': conditions[category].get('CONTRATADO', 0),
            'NO_CONTRATADO': conditions[category].get('NO NOMBRADO', 0),
            'NOMBRADO_percent': conditions[category].get('NOMBRADO_percent', 0),
            'CONTRATADO_percent': conditions[category].get('CONTRATADO_percent', 0),
            'NO_CONTRATADO_percent': conditions[category].get('NO_CONTRATADO_percent', 0),
            'TP': categories.get(category, {}).get('TP', 0),
            'TC': categories.get(category, {}).get('TC', 0),
            'DE': categories.get(category, {}).get('DE', 0),
            'TP_percent': categories.get(category, {}).get('TP_percent', 0),
            'TC_percent': categories.get(category, {}).get('TC_percent', 0),
            'DE_percent': categories.get(category, {}).get('DE_percent', 0),
            'TOTAL_cond': total_cond,
            'TOTAL_mod': total_mod,
            'TOTAL_percent': categories.get(category, {}).get('TOTAL_percent', 0),
        }
        table_data.append(category_data)

    for category, values in categories.items():
        values['TP_percent'] = (values['TP'] / total_general) * 100
        values['TC_percent'] = (values['TC'] / total_general) * 100
        values['DE_percent'] = (values['DE'] / total_general) * 100
        values['TOTAL_percent'] = values['TOTAL'] / total_general * 100 if total_general > 0 else 0

    for data in table_data:
        data['TOTAL_cond_percent'] = (data['TOTAL_cond'] / total_general_conditions) * 100 if total_general_conditions > 0 else 0
        data['TOTAL_mod_percent'] = (data['TOTAL_mod'] / total_general) * 100 if total_general > 0 else 0


    total_tp_percent = (total_tp / total_general) * 100 if total_general > 0 else 0
    total_tc_percent = (total_tc / total_general) * 100 if total_general > 0 else 0
    total_de_percent = (total_de / total_general) * 100 if total_general > 0 else 0

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
    condicion_options = teachers.values_list('status',flat=True).distinct().order_by('status')
    sede_options = teachers.values_list('sede__name',flat=True).distinct().order_by('sede')

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
    if category_filter:
        teachers = teachers.filter(category=category_filter)
    if grade:
        teachers = teachers.filter(grade=grade)
    if condicion:
        teachers = teachers.filter(status=condicion)
    if selected_sede:
        teachers = teachers.filter(sede__name=selected_sede)

    degree_distribution_data = teachers.values('status').annotate(count=Count('status')).order_by('-count')
    degree_distribution = [{'label': data['status'], 'data': data['count']} for data in degree_distribution_data]

    contract_distribution_data = teachers.values('type').annotate(count=Count('type')).order_by('-count')
    contract_distribution = [{'label': data['type'], 'data': data['count']} for data in contract_distribution_data]

    teachers_per_school_data = teachers.values('school').annotate(count=Count('school')).order_by('-count')

    average_age = teachers.aggregate(avg_age=Avg('age'))['avg_age']

    teachers_70_or_older = teachers.filter(age__gte=70)

    count_teachers_70_or_older = teachers_70_or_older.count()


    teachers_with_research = teachers.filter(research__isnull=False).values('school').annotate(count=Count('school'))
    teachers_without_research = teachers.filter(research__isnull=True).values('school').annotate(count=Count('school'))

    teachers_per_sede_data = teachers.values('sede__name').annotate(count=Count('id')).order_by('-count')
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

    if (teachers.count() != 0):
        percentage_teachers_with_research = (teachers.filter(research__isnull=False).distinct().count() / teachers.count()) * 100
    else:
        percentage_teachers_with_research = 0

    context = {
        'modalidad_options': modalidad_options,
        'categoria_options': categoria_options,
        'grado_options': grado_options,
        'facultad': facultad,
        'escuela':escuela,
        'escuelas': escuelas,
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
        'condicion_options':condicion_options,
        'sede_options':sede_options,
        'percentage_teachers_with_research': percentage_teachers_with_research,
        'categories':categories,
        'total_tp':total_tp,
        'total_tc':total_tc,
        'total_de':total_de,
        'total_general':total_general,
        'total_nombrado':total_nombrado,
        'total_contratado':total_contratado,
        'total_no_contratado':total_no_contratado,
        'total_general_conditions':total_general_conditions,
        'conditions':conditions,
        'table_data':table_data,
        'total_nombrado_percent':total_nombrado_percent,
        'total_no_contratado_percent':total_no_contratado_percent,
        'total_contratado_percent':total_contratado_percent,
        'total_general_conditions_percent':total_general_conditions_percent,
        'total_tp_percent':total_tp_percent,
        'total_tc_percent':total_tc_percent,
        'total_de_percent':total_de_percent

    }

    return render(request, 'docentes.html', context)

@login_required
def schedule_view(request, facultad, escuela):

    idFacultad, idEscuela = getEscuelaId(facultad, escuela)
    escuelas = Escuela.objects.filter(facultad=idFacultad)
    escuela = escuelas.filter(name=escuela).first()

    course_teacher_map = {}

    selected_school = request.GET.get('school')
    selected_cycle = request.GET.get('cycle')

    schools = CourseSchedule.objects.values_list('headquarters__name', flat=True).distinct()
    cycles = Course.objects.values_list('cycle', flat=True).distinct()
    cycles = sorted(cycles, key=sort_by_roman_numeral2)

    course_schedules = []

    if selected_school and selected_cycle:
        sede = get_object_or_404(Sede, name=selected_school)

        schedules_queryset = CourseSchedule.objects.filter(
            headquarters=sede,
            course_model__cycle=selected_cycle,
            course_model__school=escuela.id
        ).select_related('course_model', 'headquarters', 'period').order_by('course_model', 'day', 'start_time')

        assignments_queryset = CourseAssignment.objects.filter(
            sede=sede,
            course__cycle=selected_cycle,
            course__school=escuela.id
        ).select_related('course', 'teacher')

        course_teacher_map = {
            assignment.course.id: assignment.teacher.surname_and_names
            for assignment in assignments_queryset
        }

        grouped_schedules = {}
        for schedule in schedules_queryset:
            course_id = schedule.course_model.id
            if course_id not in grouped_schedules:
                grouped_schedules[course_id] = {
                    'course': schedule.course_model,
                    'schedules': [],
                    'classroom': schedule.classroom,
                    'teacher_name': course_teacher_map.get(course_id, 'No teacher assigned'),
                    'section': schedule.section,
                }
            grouped_schedules[course_id]['schedules'].append(schedule)

        course_schedules = list(grouped_schedules.values())
        
        for index, course_data in enumerate(course_schedules):
            course_data['color'] = getColorFromSet(index, len(grouped_schedules))

    else:
        course_schedules = []

    days_of_week = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
    hours_range = [f'{hour:02d}:00' for hour in range(7, 23)]

    return render(request, 'schedule.html', {
        'escuelas': escuelas,
        'facultad': facultad,
        'escuela': escuela,
        'course_schedules': course_schedules,
        'schools': schools,
        'cycles': cycles,
        'hours_range': hours_range,
        'days_of_week': days_of_week,
        'course_teacher_map': course_teacher_map,
        'selected_school': selected_school,
        'selected_cycle': selected_cycle,
    })

@login_required
def research_analysis(request, facultad, escuela):
    
    idFacultad, idEscuela = getEscuelaId(facultad, escuela)
    escuelas = Escuela.objects.filter(facultad=idFacultad)
    escuela = escuelas.filter(name=escuela).first()

    teacher  = request.GET.get('main_teacher',None)

    main_researcher_school = Teacher.objects.filter(
        research__id=OuterRef('id')
    ).order_by('id').values('school')[:1]

    researchs = Research.objects.annotate(
        main_researcher_school=Subquery(main_researcher_school)
    ).filter(main_researcher_school=escuela).distinct()

    if teacher:
        researchs = researchs.filter(teacher=teacher)

    teachers_with_research = Teacher.objects.filter(research__isnull=False)
    teachers_with_research = teachers_with_research.filter(school=escuela).distinct()

    schools = teachers_with_research.values('school').distinct()
    school_counts = []
    for school in schools:
        count = teachers_with_research.filter(school=school['school']).count()
        school_counts.append((school['school'], count))

    research_types = researchs.values('type_of_research').distinct()
    type_counts = []
    for research_type in research_types:
        count = researchs.filter(type_of_research=research_type['type_of_research']).count()
        type_counts.append((research_type['type_of_research'], count))

    conditions = teachers_with_research.values('status').distinct()
    condition_counts = []
    for condition in conditions:
        count = teachers_with_research.filter(status=condition['status']).count()
        condition_counts.append((condition['status'], count))

    total_budget = researchs.aggregate(total_budget=models.Sum('budget'))

    total_projects = researchs.count()

    # researchs = Research.objects.all()

    researchs2 = Research.objects.annotate(
        main_researcher_school=Subquery(main_researcher_school)
    ).filter(main_researcher_school=escuela).distinct()

    main_researchers = []
    for research in researchs2:
      main_teacher = research.teacher.first()
      if not (main_teacher in main_researchers):  
        main_researchers.append(main_teacher)

    # print(researchs.values())
            
    # researchs = researchs.filter(teacher__school=escuela).distinct()

    # researchs.filter(school=escuela)

    research_line_counts = Counter(researchs.values_list('research_line', flat=True))
    research_line_counts_list = list(research_line_counts.items())
    if teacher:
        t_researchs = []
        
        for research in researchs:
          main_teacher = research.teacher.first()
          print( main_teacher.id, teacher, teacher == main_teacher.id)
          if str(teacher) == str(main_teacher.id):
              t_researchs.append(research)
        researchs = t_researchs

    context = {
        'escuelas': escuelas,
        'facultad': facultad,
        'escuela':escuela,
        'school_counts': school_counts,
        'type_counts': type_counts,
        'condition_counts': condition_counts,
        'total_budget': total_budget['total_budget'],
        'total_projects': total_projects,
        'research_line_counts': research_line_counts_list,
        'researchs': researchs,
        'main_researchers': main_researchers,
        'teachers_with_research':teachers_with_research
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

@login_required
def estudiantes(request, facultad, escuela):
    
    idFacultad, idEscuela = getEscuelaId(facultad, escuela)
    escuelas = Escuela.objects.filter(facultad=idFacultad)
    escuela = escuelas.filter(name=escuela).first()


    filtro_sede = request.GET.get('sede')
    filtro_ciclo = request.GET.get('ciclo')
    courses = Course.objects.all()

    estudiantes_filtrados = Estudiante.objects.all()

    if escuela:
        estudiantes_filtrados = estudiantes_filtrados.filter(escuela=escuela)

    if filtro_sede:
        estudiantes_filtrados = estudiantes_filtrados.filter(sede__name=filtro_sede)
    
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
    sedes = Estudiante.objects.values_list('sede__name', flat=True).distinct()

    enrollments = Enrollment.objects.select_related('course', 'student').filter(student__escuela=escuela)
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

    sede_counts = estudiantes_filtrados.values('sede__name').annotate(total=Count('id')).distinct()
    sedes_labels = [item['sede__name'] for item in sede_counts]
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
        'escuelas': escuelas,
        'facultad': facultad,
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

@login_required
def activos(request, facultad, escuela):
    
    idFacultad, idEscuela = getEscuelaId(facultad, escuela)
    escuelas = Escuela.objects.filter(facultad=idFacultad)
    escuela = escuelas.filter(name=escuela).first()

    # Inicialización de variables para filtros
    ambientes = Activo.objects.values_list('ambiente', flat=True).distinct()
    descripciones = Activo.objects.values_list('descripcion', flat=True).distinct()
    estados = Activo.objects.values_list('estado', flat=True).distinct()
    computadores = Activo.objects.values_list('numero_pc', flat=True).distinct()

    filtro_ambiente = request.GET.get('ambiente', None)
    filtro_descripcion = request.GET.get('descripcion', None)
    filtro_estado = request.GET.get('estado', None)

    queryset = Activo.objects.all()

    if escuela:
        queryset = queryset.filter(escuela=escuela)
    if filtro_ambiente:
        queryset = queryset.filter(ambiente=filtro_ambiente)
    if filtro_descripcion:
        queryset = queryset.filter(descripcion=filtro_descripcion)
    if filtro_estado:
        queryset = queryset.filter(estado=filtro_estado)

    datos_pastel = queryset.values('estado').annotate(total=Count('estado'))

    datos_barras_qs = queryset.values('ambiente', 'descripcion').annotate(total=Count('id')).order_by('ambiente')

    computadores = computadores.exclude(numero_pc="-")
    computadores = computadores.values('numero_pc', 'ambiente').annotate(total=Count('id')).order_by('ambiente').distinct().count()
    
    print(computadores)

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
    ]
    datasets = []
    for index, descripcion in enumerate(descripciones):
        dataset = {
            'label': descripcion,
            'data': [datos_barras.get(ambiente, {}).get(descripcion, 0) for ambiente in ambientes],
            'backgroundColor': colores[index % len(colores)]
        }
        datasets.append(dataset)

    datos_grafico_barras = {
        'labels': list(ambientes),
        'datasets': datasets
    }
    datos_grafico_barras_json = json.dumps(datos_grafico_barras)

    tabla_resumen = queryset.values('ambiente', 'descripcion', 'estado').annotate(total=Count('id'))

    datos_pastel_json = json.dumps(list(datos_pastel), default=str)
    datos_barras_json = json.dumps(list(datos_barras), default=str)
    tabla_resumen_json = json.dumps(list(tabla_resumen), default=str)

    print('datos barras', datos_pastel)

    conteo_por_estado = queryset.values('descripcion', 'estado').annotate(cantidad=Count('id')).order_by('descripcion', 'estado')

    totales_por_descripcion = queryset.values('descripcion').annotate(total=Count('id')).order_by('descripcion')

    tabla_resumen2 = {}
    for descripcion in totales_por_descripcion:
        tabla_resumen2[descripcion['descripcion']] = {
            'OPERATIVO': 0,
            'MALOGRADO': 0,
            'BAJA': 0,
            'total': descripcion['total'],
        }

    for estado in conteo_por_estado:
        equipo = estado['descripcion']
        tabla_resumen2[equipo][estado['estado']] = estado['cantidad']

    total_general = sum(descripcion['total'] for descripcion in totales_por_descripcion)
    totales_por_estado = {
        'OPERATIVO': sum(item['OPERATIVO'] for item in tabla_resumen2.values()),
        'MALOGRADO': sum(item['MALOGRADO'] for item in tabla_resumen2.values()),
        'BAJA': sum(item['BAJA'] for item in tabla_resumen2.values()),
        'total': total_general,
    }

    print(total_general)
    if total_general == 0: total_general = 1

    for equipo, totales in tabla_resumen2.items():
        tabla_resumen2[equipo]['operativo_percent'] = (totales['OPERATIVO'] / total_general) * 100
        tabla_resumen2[equipo]['malogrado_percent'] = (totales['MALOGRADO'] / total_general) * 100
        tabla_resumen2[equipo]['baja_percent'] = (totales['BAJA'] / total_general) * 100
        tabla_resumen2[equipo]['total_percent'] = (totales['total'] / total_general) * 100
    
    totales_por_estado['operativo_percent'] = (totales_por_estado['OPERATIVO'] / total_general) * 100
    totales_por_estado['malogrado_percent'] = (totales_por_estado['MALOGRADO'] / total_general) * 100
    totales_por_estado['baja_percent'] = (totales_por_estado['BAJA'] / total_general) * 100
    totales_por_estado['total_percent'] = 100

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
        'facultad': facultad,
        'escuela':escuela,
        'escuelas': escuelas,
        'tabla_resumen2': tabla_resumen2,
        'totales_por_estado': totales_por_estado,
    })

@login_required
def employees(request, facultad, escuela):
    
    idFacultad, idEscuela = getEscuelaId(facultad, escuela)
    escuelas = Escuela.objects.filter(facultad=idFacultad)
    escuela = escuelas.filter(name=escuela).first()

    employees = PAdministrativo.objects.all()

    employees = employees.filter(escuela=idEscuela)

    context = {
        'escuelas': escuelas,
        'employees': employees,
        'facultad': facultad,
        'escuela':escuela,
    }

    return render(request, 'personal.html', context)

def api_course_students(request,curso):
    
    sede_students = request.GET.get('sede')

    assignments = CourseAssignment.objects.filter(course=curso)
    
    enrollments = Enrollment.objects.filter(course=curso)

    sede_conversion = {
      "1":"TRUJILLO",
      "2":"VALLE",
    }

    if sede_students:
        print('filtering')
        enrollments = enrollments.filter(student__sede__name=sede_conversion[sede_students])

    enrolled_students = [
        {
            'id': enrollment.id,
            'student_id': enrollment.student.id,
            'student_names': enrollment.student.apellidos_nombres,
            'student_code': enrollment.student.numero_matricula,
            'student_sede': enrollment.student.sede.name,
            'times': enrollment.times_taken,
            'period': enrollment.period.period,
        }
        for enrollment in enrollments
    ]

    assigned_teachers = [
        {
            "teacher": assignment.teacher.surname_and_names,
            "sede_name": assignment.sede.name
        }
        for assignment in assignments
    ]

    response = {
        "teachers": list(assigned_teachers),
        "students": list(enrolled_students),
    }

    # print('enrollments: ', enrolled_students)
    return JsonResponse(dict(response), safe=False)