from django.shortcuts import render
from .models import Course, Teacher
from django.db import models
from django.db.models import Count, Avg
from django.db.models import Sum

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
    # Apply filters if present in the request parameters
    age = request.GET.get('age')
    modality = request.GET.get('modality')
    category = request.GET.get('category')
    grade = request.GET.get('grade')
    school = request.GET.get('school')

    # Retrieve the filtered data from the database
    teachers = Teacher.objects.all()

    if age:
        teachers = teachers.filter(birth=age)
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
    average_age = teachers.aggregate(avg_age=Avg('birth'))['avg_age']

    context = {
        'teachers': teachers,
        'degree_data': degree_distribution,
        'contract_data': contract_distribution,
        'teachers_per_school_data': teachers_per_school,
        'average_age': average_age,
    }

    return render(request, 'dashboard.html', context)
