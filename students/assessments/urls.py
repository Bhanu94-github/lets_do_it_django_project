from django.urls import path
from . import views

app_name = 'student_assessments'

urlpatterns = [
    path('upload-resume/', views.upload_resume, name='upload_resume'),
    path('select-difficulty/', views.select_difficulty, name='select_difficulty'),
    path('prepare-exam/', views.prepare_exam, name='prepare_exam'),
    path('exam/', views.exam, name='exam'),
    path('result/', views.result, name='result'),
]
