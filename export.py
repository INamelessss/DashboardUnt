import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DashboardDecano.settings')

# Inicializa Django
django.setup()

import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from dashboard.models import Sede, Period, Factultad, Escuela, Malla, Course, PAdministrativo, Teacher, CourseAssignment, CourseSchedule, Research, Estudiante, Enrollment, Activo
from django.db import transaction

def get_foreign_key_instance(model, unique_identifier_field, unique_identifier):
    try:
        if unique_identifier is not None and unique_identifier != '':
            return model.objects.get(**{unique_identifier_field: unique_identifier})
        else:
            return None
    except model.DoesNotExist:
        print(f"No se encontró {model.__name__} para {unique_identifier_field} con identificador '{unique_identifier}'")
        return None

@transaction.atomic
def import_data_from_sheet(model, sheet_name, foreign_keys=None):
    print(f"Importando datos de '{sheet_name}'...")
    try:
        df = pd.read_excel('datos_importacion.xlsx', sheet_name=sheet_name)
        if df.empty or len(df.index) == 0:
            print(f"La hoja '{sheet_name}' está vacía o solo contiene cabeceras. Se omite la importación para este modelo.")
            return
    except ValueError as e:
        print(f"Error al leer la hoja '{sheet_name}': {e}")
        return
    
    model_instances = []
    for index, row in df.iterrows():
        row_dict = row.to_dict()
        if foreign_keys:
            for fk_field, (fk_model, unique_field) in foreign_keys.items():
                fk_identifier = row_dict.pop(fk_field, None)
                fk_instance = get_foreign_key_instance(fk_model, unique_field, fk_identifier)
                if fk_instance:
                    row_dict[fk_field] = fk_instance
                else:
                    print(f"Skipping row {index+2} due to missing foreign key {fk_field}")
                    continue
        try:
            model_instances.append(model(**row_dict))
        except Exception as e:
            print(f"Error en fila {index+2}: {e}")
            continue
    if model_instances:
        model.objects.bulk_create(model_instances)
        print(f"Todos los datos de '{sheet_name}' han sido importados exitosamente.")
    else:
        print(f"No se encontraron datos válidos para importar en la hoja '{sheet_name}'.")

def import_all_data():
    import_data_from_sheet(Sede, 'Sede')
    import_data_from_sheet(Period, 'Period')
    import_data_from_sheet(Factultad, 'Factultad')
    import_data_from_sheet(Escuela, 'Escuela', foreign_keys={'facultad': (Factultad, 'name')})
    import_data_from_sheet(Malla, 'Malla', foreign_keys={'escuela': (Escuela, 'name')})
    import_data_from_sheet(Course, 'Course', foreign_keys={'school': (Escuela, 'name'),'period': (Period, 'period'),'malla': (Malla, 'documento')})
    import_data_from_sheet(PAdministrativo, 'PAdministrativo', foreign_keys={'escuela': (Escuela, 'name')})
    import_data_from_sheet(Teacher, 'Teacher', foreign_keys={'school': (Escuela, 'name'), 'sede': (Sede, 'name'), 'period': (Period, 'period')})
    import_data_from_sheet(CourseAssignment, 'CourseAssignment', foreign_keys={'course': (Course, 'name'), 'teacher': (Teacher, 'surname_and_names'), 'sede': (Sede, 'name')})
    import_data_from_sheet(CourseSchedule, 'CourseSchedule', foreign_keys={'course_model': (Course, 'name'), 'headquarters': (Sede, 'name'), 'period': (Period, 'period')})
    import_data_from_sheet(Research, 'Research', foreign_keys={})
    import_data_from_sheet(Estudiante, 'Estudiante', foreign_keys={'escuela': (Escuela, 'name'), 'sede': (Sede, 'name'), 'period': (Period, 'period'), 'malla': (Malla, 'documento')})
    import_data_from_sheet(Enrollment, 'Enrollment', foreign_keys={'student': (Estudiante, 'numero_matricula'), 'course': (Course, 'name'), 'period': (Period, 'period')})
    import_data_from_sheet(Activo, 'Activo', foreign_keys={'escuela': (Escuela, 'name')})

    print("Todos los datos han sido importados exitosamente.")

def link_research_to_teachers(sheet_name):
    df = pd.read_excel('datos_importacion.xlsx', sheet_name=sheet_name)
    for index, row in df.iterrows():
        try:
            research = Research.objects.get(code=row['research_code'])
            teacher = Teacher.objects.get(surname_and_names=row['teacher_surname_and_names'])
            research.teacher.add(teacher)
        except Research.DoesNotExist:
            print(f"Research with code {row['research_code']} does not exist.")
            continue
        except Teacher.DoesNotExist:
            print(f"Teacher with surname_and_names {row['teacher_surname_and_names']} does not exist.")
            continue

if __name__ == '__main__':
    import_all_data()
    #link_research_to_teachers('ResearchTeacher')
    print("Todos los datos han sido importados y establecidos exitosamente.")