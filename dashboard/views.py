from django.shortcuts import render
from .models import Course, CourseModel, Teacher
from django.db import models
from django.db.models import Count, Avg
from django.db.models import Sum
from datetime import date, datetime
from django.db.models.functions import ExtractYear

def course_list(request):
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

    context = {
        'courses': courses,
        'total_credits': total_credits['total_credits'],
        'total_courses': total_courses,
        'chart_data': chart_data,
    }
    return render(request, 'cursos/course_list.html', context)


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
    teachers_per_school = [{'label': data['school'], 'data': data['count']} for data in teachers_per_school_data]

    # Calculate the average age of teachers
    average_age = teachers.aggregate(avg_age=Avg('age'))['avg_age']

    context = {
        'teachers': teachers,
        'degree_data': degree_distribution,
        'contract_data': contract_distribution,
        'teachers_per_school_data': teachers_per_school,
        'average_age': average_age,
    }

    return render(request, 'dashboard.html', context)

def schedule_view(request):
    if request.method == 'POST':
        selected_school = request.POST['school']
        selected_cycle = request.POST['cycle']
        selected_career = request.POST['career']

        courses = CourseModel.objects.filter(headquarters=selected_school, cycle=selected_cycle, career=selected_career)

        schools = CourseModel.objects.values_list('headquarters', flat=True).distinct()
        cycles = CourseModel.objects.values_list('cycle', flat=True).distinct()
        careers = CourseModel.objects.values_list('career', flat=True).distinct()
    else:
        schools = CourseModel.objects.values_list('headquarters', flat=True).distinct()
        cycles = CourseModel.objects.values_list('cycle', flat=True).distinct()
        careers = CourseModel.objects.values_list('career', flat=True).distinct()

        courses = CourseModel.objects.all()

    # Generate hours range
    hours_range = []
    start_hour = 7
    end_hour = 22
    for hour in range(start_hour, end_hour + 1):
        hours_range.append('{:02d}:00'.format(hour))

    courses = courses.prefetch_related('courseschedule_set')

    return render(request, 'schedule.html', {'courses': courses, 'schools': schools, 'cycles': cycles, 'hours_range': hours_range, 'careers':careers})
