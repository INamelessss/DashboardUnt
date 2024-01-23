"""DashboardDecano URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from dashboard import views
from authentication import views as auth_views

urlpatterns = [
    path('', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/<str:facultad>/<str:escuela>/course_list/', views.course_list, name='course_list'),
    path('dashboard/<str:facultad>/<str:escuela>/docentes/', views.docentes, name='docentes'),
    path('dashboard/<str:facultad>/<str:escuela>/personal/', views.employees, name='personal'),
    path('dashboard/<str:facultad>/<str:escuela>/malla/', views.malla, name='malla'),
    path('dashboard/<str:facultad>/<str:escuela>/horario/', views.schedule_view, name='horario'),
    path('dashboard/<str:facultad>/<str:escuela>/research/', views.research_analysis, name='research'),
    path('dashboard/<str:facultad>/<str:escuela>/estudiantes/', views.estudiantes, name='estudiantes'),
    path('dashboard/<str:facultad>/<str:escuela>/infraestructura/', views.activos, name='activos'),
    path('api/matriculados/<int:curso>', views.api_course_students, name='api.matriculados')
]
